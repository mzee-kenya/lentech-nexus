from django.db.models import Count, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from core.permissions import IsAuthorOrReadOnly

from .models import Idea, IdeaInterest
from .serializers import (
    IdeaDetailSerializer,
    IdeaInterestSerializer,
    IdeaListSerializer,
    IdeaWriteSerializer,
)


class IdeaViewSet(viewsets.ModelViewSet):
    """Ideas: public discovery, author-controlled management, interest."""

    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    search_fields = ['title', 'summary', 'description', 'tags']
    filterset_fields = ['status', 'author']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        return (
            Idea.objects.select_related('author')
            .annotate(interest_count=Count('interests', distinct=True))
            .prefetch_related('interests')
        )

    def get_serializer_class(self):
        if self.action == 'list':
            return IdeaListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return IdeaWriteSerializer
        return IdeaDetailSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        write = IdeaWriteSerializer(data=request.data, context=self.get_serializer_context())
        write.is_valid(raise_exception=True)
        self.perform_create(write)
        return Response(
            IdeaDetailSerializer(write.instance, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        write = IdeaWriteSerializer(
            instance, data=request.data, partial=partial, context=self.get_serializer_context()
        )
        write.is_valid(raise_exception=True)
        write.save()
        return Response(IdeaDetailSerializer(instance, context=self.get_serializer_context()).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def interest(self, request, pk=None):
        idea = self.get_object()
        if idea.author_id == request.user.id:
            raise ValidationError('You cannot express interest in your own idea.')
        if idea.status not in (Idea.Status.OPEN, Idea.Status.IN_PROGRESS):
            raise ValidationError('This idea is not accepting new interest right now.')
        if IdeaInterest.objects.filter(
            idea=idea, user=request.user, status=IdeaInterest.Status.PENDING
        ).exists():
            raise ValidationError('You already expressed interest in this idea.')

        interest = IdeaInterest.objects.create(
            idea=idea, user=request.user, message=request.data.get('message', '')
        )
        return Response(IdeaInterestSerializer(interest).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def interests(self, request, pk=None):
        idea = self.get_object()
        if idea.author_id != request.user.id and not request.user.is_staff:
            raise PermissionDenied('Only the idea author can see interest details.')
        qs = idea.interests.select_related('user').exclude(
            status=IdeaInterest.Status.WITHDRAWN
        )
        return Response(IdeaInterestSerializer(qs, many=True).data)


class IdeaInterestViewSet(viewsets.GenericViewSet,
                          viewsets.mixins.ListModelMixin,
                          viewsets.mixins.RetrieveModelMixin,
                          viewsets.mixins.DestroyModelMixin):
    """Review and withdraw idea interest."""

    serializer_class = IdeaInterestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return IdeaInterest.objects.none()
        user = self.request.user
        qs = IdeaInterest.objects.select_related('idea', 'user')
        if user.is_staff:
            return qs
        return qs.filter(Q(user=user) | Q(idea__author=user))

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        return self._review(request, pk, IdeaInterest.Status.ACCEPTED)

    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        return self._review(request, pk, IdeaInterest.Status.DECLINED)

    def _review(self, request, pk, new_status):
        interest = self.get_object()
        if interest.idea.author_id != request.user.id:
            raise PermissionDenied('Only the idea author can review interest.')
        if interest.status != IdeaInterest.Status.PENDING:
            raise ValidationError('This interest has already been reviewed.')
        interest.status = new_status
        interest.save(update_fields=['status', 'updated_at'])
        return Response(IdeaInterestSerializer(interest).data)

    def destroy(self, request, pk=None):
        interest = self.get_object()
        if interest.user_id != request.user.id:
            raise PermissionDenied('You can only withdraw your own interest.')
        if interest.status != IdeaInterest.Status.PENDING:
            raise ValidationError('Only pending interest can be withdrawn.')
        interest.status = IdeaInterest.Status.WITHDRAWN
        interest.save(update_fields=['status', 'updated_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)