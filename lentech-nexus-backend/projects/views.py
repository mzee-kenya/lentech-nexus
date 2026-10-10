from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from core.permissions import IsOwnerOrAdmin

from .models import Project, ProjectJoinRequest, ProjectMembership
from .serializers import (
    ProjectDetailSerializer,
    ProjectJoinRequestSerializer,
    ProjectListSerializer,
    ProjectMembershipSerializer,
    ProjectWriteSerializer,
)


class ProjectViewSet(viewsets.ModelViewSet):
    """Projects: public discovery, owner-controlled management, joining."""

    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]
    search_fields = ['title', 'summary', 'description', 'technologies']
    filterset_fields = ['status', 'owner']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        return (
            Project.objects.select_related('owner')
            .annotate(member_count=Count('memberships', distinct=True))
            .prefetch_related('memberships__user', 'join_requests')
        )

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return ProjectWriteSerializer
        return ProjectDetailSerializer

    def perform_create(self, serializer):
        # Creating a project also makes the creator its owner-member.
        with transaction.atomic():
            project = serializer.save(owner=self.request.user)
            ProjectMembership.objects.create(
                project=project, user=self.request.user, role=ProjectMembership.Role.OWNER
            )

    def _detail_response(self, project, status_code=status.HTTP_200_OK):
        return Response(
            ProjectDetailSerializer(project, context=self.get_serializer_context()).data,
            status=status_code,
        )

    def create(self, request, *args, **kwargs):
        write = ProjectWriteSerializer(data=request.data, context=self.get_serializer_context())
        write.is_valid(raise_exception=True)
        self.perform_create(write)
        return self._detail_response(write.instance, status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        write = ProjectWriteSerializer(
            instance, data=request.data, partial=partial, context=self.get_serializer_context()
        )
        write.is_valid(raise_exception=True)
        write.save()
        return self._detail_response(instance)

    # -- Collaboration ------------------------------------------------------

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def join(self, request, pk=None):
        project = self.get_object()
        if project.owner_id == request.user.id:
            raise ValidationError('You already own this project.')
        if ProjectMembership.objects.filter(project=project, user=request.user).exists():
            raise ValidationError('You are already a member of this project.')
        if ProjectJoinRequest.objects.filter(
            project=project, requester=request.user, status=ProjectJoinRequest.Status.PENDING
        ).exists():
            raise ValidationError('You already have a pending request for this project.')

        join_request = ProjectJoinRequest.objects.create(
            project=project, requester=request.user, message=request.data.get('message', '')
        )
        return Response(
            ProjectJoinRequestSerializer(join_request).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def leave(self, request, pk=None):
        project = self.get_object()
        if project.owner_id == request.user.id:
            raise ValidationError('The project owner cannot leave their own project.')
        deleted, _ = ProjectMembership.objects.filter(
            project=project, user=request.user
        ).delete()
        if not deleted:
            raise ValidationError('You are not a member of this project.')
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def requests(self, request, pk=None):
        project = self.get_object()
        if project.owner_id != request.user.id and not request.user.is_staff:
            raise PermissionDenied('Only the project owner can view join requests.')
        qs = project.join_requests.select_related('requester').exclude(
            status=ProjectJoinRequest.Status.CANCELLED
        )
        return Response(ProjectJoinRequestSerializer(qs, many=True).data)

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        project = self.get_object()
        return Response(
            ProjectMembershipSerializer(project.memberships.select_related('user'), many=True).data
        )

    @action(
        detail=True,
        methods=['delete'],
        permission_classes=[IsAuthenticated],
        url_path=r'members/(?P<user_id>[0-9]+)',
    )
    def remove_member(self, request, pk=None, user_id=None):
        project = self.get_object()
        if project.owner_id != request.user.id:
            raise PermissionDenied('Only the project owner can remove members.')
        if str(project.owner_id) == str(user_id):
            raise ValidationError('The owner cannot be removed.')
        deleted, _ = ProjectMembership.objects.filter(project=project, user_id=user_id).delete()
        if not deleted:
            raise ValidationError('That user is not a member of this project.')
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectJoinRequestViewSet(viewsets.GenericViewSet,
                                viewsets.mixins.ListModelMixin,
                                viewsets.mixins.RetrieveModelMixin,
                                viewsets.mixins.DestroyModelMixin):
    """Review and cancel project join requests."""

    serializer_class = ProjectJoinRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ProjectJoinRequest.objects.none()
        user = self.request.user
        qs = ProjectJoinRequest.objects.select_related('project', 'requester')
        if user.is_staff:
            return qs
        return qs.filter(Q(requester=user) | Q(project__owner=user))

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        return self._review(request, pk, ProjectJoinRequest.Status.APPROVED)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        return self._review(request, pk, ProjectJoinRequest.Status.REJECTED)

    def _review(self, request, pk, new_status):
        join_request = self.get_object()
        if join_request.project.owner_id != request.user.id:
            raise PermissionDenied('Only the project owner can review requests.')
        if join_request.status != ProjectJoinRequest.Status.PENDING:
            raise ValidationError('This request has already been reviewed.')

        with transaction.atomic():
            join_request.status = new_status
            join_request.reviewed_at = timezone.now()
            join_request.save(update_fields=['status', 'reviewed_at', 'updated_at'])
            if new_status == ProjectJoinRequest.Status.APPROVED:
                ProjectMembership.objects.get_or_create(
                    project=join_request.project,
                    user=join_request.requester,
                    defaults={'role': ProjectMembership.Role.CONTRIBUTOR},
                )
        return Response(ProjectJoinRequestSerializer(join_request).data)

    def destroy(self, request, pk=None):
        join_request = self.get_object()
        if join_request.requester_id != request.user.id:
            raise PermissionDenied('You can only cancel your own request.')
        if join_request.status != ProjectJoinRequest.Status.PENDING:
            raise ValidationError('Only pending requests can be cancelled.')
        join_request.status = ProjectJoinRequest.Status.CANCELLED
        join_request.save(update_fields=['status', 'updated_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)
