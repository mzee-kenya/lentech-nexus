"""Serializers for the social feed.

Reads and writes are split so the API stays predictable:

* ``PostListSerializer``   – lightweight shape for the feed.
* ``PostDetailSerializer`` – adds viewer-specific flags (e.g. has-liked).
* ``PostWriteSerializer``  – only the editable ``body`` field. Media is handled
  in the view because files arrive in ``request.FILES``, not in JSON.
* ``CommentSerializer``    – read + write for comments.
"""

from rest_framework import serializers

from .models import Comment, Post

MAX_BODY_LENGTH = 2000


def _author_avatar(obj) -> str:
    """Best-effort lookup of the author's profile image.

    The developer profile is an optional one-to-one relation, so we defensively
    return an empty string when it is missing.
    """
    profile = getattr(obj.author, 'developer_profile', None)
    return getattr(profile, 'profile_image', '') or ''


class AuthorMixin(serializers.Serializer):
    """Reusable author summary fields embedded in posts and comments."""

    author_id = serializers.IntegerField(source='author.id', read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_display_name = serializers.CharField(source='author.display_name', read_only=True)
    author_avatar = serializers.SerializerMethodField()

    def get_author_avatar(self, obj) -> str:
        return _author_avatar(obj)


class PostListSerializer(AuthorMixin, serializers.ModelSerializer):
    like_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    viewer_has_liked = serializers.BooleanField(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'body', 'image_url', 'video_url',
            'author_id', 'author_username', 'author_display_name', 'author_avatar',
            'like_count', 'comment_count', 'viewer_has_liked', 'created_at',
        ]


class PostDetailSerializer(PostListSerializer):
    viewer_is_author = serializers.SerializerMethodField()

    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ['viewer_is_author', 'updated_at']

    def get_viewer_is_author(self, obj) -> bool:
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        return bool(user and user.is_authenticated and obj.author_id == user.id)


class PostWriteSerializer(serializers.ModelSerializer):
    """Validates the editable text of a post (media is validated separately)."""

    class Meta:
        model = Post
        fields = ['body']

    def validate_body(self, value):
        value = (value or '').strip()
        if len(value) > MAX_BODY_LENGTH:
            raise serializers.ValidationError(
                f'Post body must be at most {MAX_BODY_LENGTH} characters.'
            )
        return value


class CommentSerializer(AuthorMixin, serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = [
            'id', 'post', 'author_id', 'author_username', 'author_display_name',
            'author_avatar', 'body', 'created_at',
        ]
        read_only_fields = [
            'id', 'post', 'author_id', 'author_username', 'author_display_name',
            'author_avatar', 'created_at',
        ]

    def validate_body(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Comment cannot be empty.')
        if len(value) > MAX_BODY_LENGTH:
            raise serializers.ValidationError(
                f'Comment must be at most {MAX_BODY_LENGTH} characters.'
            )
        return value
