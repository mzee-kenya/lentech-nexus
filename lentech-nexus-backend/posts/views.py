"""API views for the social feed.

Design notes
------------
* Posts are world-readable but only the author may edit or delete them.
* Likes are idempotent: liking twice is a no-op, unliking never errors.
* Comments are created through a nested action on the post and managed
  individually through ``CommentViewSet``.
* Image/video uploads are delegated to ``core.services.storage`` so this module
  never imports the Cloudinary SDK directly.
"""

from django.db.models import BooleanField, Count, Exists, OuterRef, Value
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from core.permissions import IsAuthorOrReadOnly
from core.services import storage

from .models import Comment, Post, PostLike
from .serializers import (
    CommentSerializer,
    PostDetailSerializer,
    PostListSerializer,
    PostWriteSerializer,
)


class PostViewSet(viewsets.ModelViewSet):
    """Feed posts with likes, comments and media attachments."""

    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    search_fields = ['body', 'author__username']
    filterset_fields = ['author']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Annotate engagement counters and the current viewer's like state.

        Using a single annotated queryset avoids the N+1 problem: instead of one
        query per post to count likes, the database computes everything at once.
        """
        user = self.request.user
        qs = Post.objects.select_related('author', 'author__developer_profile').annotate(
            like_count=Count('likes', distinct=True),
            comment_count=Count('comments', distinct=True),
        )
        if user.is_authenticated:
            # Exists() yields a per-row boolean telling us whether the viewer
            # already liked this post — cheaper than loading the like rows.
            qs = qs.annotate(
                viewer_has_liked=Exists(
                    PostLike.objects.filter(post=OuterRef('pk'), user=user)
                )
            )
        else:
            qs = qs.annotate(
                viewer_has_liked=Value(False, output_field=BooleanField())
            )
        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return PostListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return PostWriteSerializer
        return PostDetailSerializer

    # -- media helpers -------------------------------------------------------

    def _save_media(self, post, request):
        """Attach any uploaded image/video to ``post``.

        Raises DRF ``ValidationError`` (HTTP 400) for rejected files so the
        client gets an actionable message instead of a 500.
        """
        changed_fields = []
        for field, kind in (('image', storage.IMAGE), ('video', storage.VIDEO)):
            upload = request.FILES.get(field)
            if not upload:
                continue
            try:
                result = storage.upload_media(upload, request.user.id, kind)
            except storage.UnsupportedMedia as exc:
                raise ValidationError({field: str(exc)}) from exc
            except storage.StorageNotConfigured as exc:
                raise ValidationError({field: str(exc)}) from exc
            except storage.StorageError as exc:
                raise ValidationError({field: f'Upload failed: {exc}'}) from exc

            db_field = 'image' if kind == storage.IMAGE else 'video'
            setattr(post, f'{db_field}_url', result['url'])
            setattr(post, f'{db_field}_public_id', result['public_id'])
            changed_fields.append(f'{db_field}_url')
            changed_fields.append(f'{db_field}_public_id')
        if changed_fields:
            post.save(update_fields=changed_fields + ['updated_at'])

    # -- CRUD ----------------------------------------------------------------

    def create(self, request, *args, **kwargs):
        """Create a post from multipart/form-data.

        Text is validated by the serializer; files are validated and uploaded
        by :meth:`_save_media`. A post must contain text or at least one file.
        """
        write = PostWriteSerializer(data=request.data, context=self.get_serializer_context())
        write.is_valid(raise_exception=True)

        has_media = bool(request.FILES.get('image') or request.FILES.get('video'))
        if not write.validated_data.get('body') and not has_media:
            raise ValidationError('A post needs text, an image or a video.')

        post = Post.objects.create(author=request.user, body=write.validated_data.get('body', ''))
        self._save_media(post, request)
        # Re-fetch through the annotated queryset so the response includes counts.
        post = self.get_queryset().get(pk=post.pk)
        return Response(
            PostDetailSerializer(post, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        write = PostWriteSerializer(
            instance, data=request.data, partial=partial, context=self.get_serializer_context()
        )
        write.is_valid(raise_exception=True)
        write.save()
        instance = self.get_queryset().get(pk=instance.pk)
        return Response(PostDetailSerializer(instance, context=self.get_serializer_context()).data)

    def perform_destroy(self, instance):
        # Remove the Cloudinary assets before the row disappears.
        if instance.image_public_id:
            storage.delete_image(instance.image_public_id)
        if instance.video_public_id:
            storage.delete_image(instance.video_public_id)
        instance.delete()

    # -- likes ---------------------------------------------------------------

    def _like_state(self, post, user) -> dict:
        """Return fresh counters after a like/unlike change."""
        return {
            'like_count': post.likes.count(),
            'comment_count': post.comments.count(),
            'viewer_has_liked': post.likes.filter(user=user).exists(),
        }

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """Like (POST) or unlike (DELETE) a post.

        Both verbs share one action because DRF resolves a URL path to a single
        view; two separate actions on the same path would shadow each other.
        Both are idempotent — repeating either is harmless.
        """
        post = self.get_object()
        if request.method == 'POST':
            PostLike.objects.get_or_create(post=post, user=request.user)
        else:
            PostLike.objects.filter(post=post, user=request.user).delete()
        return Response(self._like_state(post, request.user))

    # -- comments ------------------------------------------------------------

    @action(detail=True, methods=['get', 'post'],
            permission_classes=[IsAuthenticatedOrReadOnly])
    def comments(self, request, pk=None):
        """GET the comment thread, or POST a new comment."""
        post = self.get_object()

        if request.method == 'GET':
            queryset = post.comments.select_related('author', 'author__developer_profile')
            page = self.paginate_queryset(queryset)
            if page is not None:
                return self.get_paginated_response(CommentSerializer(page, many=True).data)
            return Response(CommentSerializer(queryset, many=True).data)

        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(post=post, author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentViewSet(viewsets.GenericViewSet,
                     viewsets.mixins.RetrieveModelMixin,
                     viewsets.mixins.DestroyModelMixin):
    """Retrieve or delete a single comment (author or staff only)."""

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        return Comment.objects.select_related('author', 'author__developer_profile')
