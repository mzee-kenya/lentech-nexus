from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from core.permissions import IsOwnerOrReadOnly
from core.services import storage
from core.throttling import UploadRateThrottle

from .models import Developer
from .serializers import DeveloperSerializer, DeveloperWriteSerializer


class DeveloperViewSet(viewsets.ModelViewSet):
    """CRUD for public developer profiles.

    Read access is open to everyone. Writes require authentication and are
    restricted to the owner of the profile.
    """

    queryset = Developer.objects.select_related('user').all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    search_fields = ['name', 'role', 'bio', 'skills']
    filterset_fields = ['role']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            return DeveloperWriteSerializer
        return DeveloperSerializer

    def perform_create(self, serializer):
        if Developer.objects.filter(user=self.request.user).exists():
            raise ValidationError('You already have a developer profile.')
        name = self.request.user.display_name
        serializer.save(user=self.request.user, name=name)

    def create(self, request, *args, **kwargs):
        # Return the full read representation after creation.
        write = self.get_serializer(data=request.data)
        write.is_valid(raise_exception=True)
        self.perform_create(write)
        return Response(
            DeveloperSerializer(write.instance).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        write = self.get_serializer(instance, data=request.data, partial=partial)
        write.is_valid(raise_exception=True)
        write.save()
        return Response(DeveloperSerializer(instance).data)

    # -- Convenience endpoint for the signed-in user's own profile ----------

    @action(detail=False, methods=['get', 'post', 'patch', 'put'], permission_classes=[IsAuthenticated],
            url_path='me')
    def me(self, request):
        profile, _ = Developer.objects.get_or_create(
            user=request.user,
            defaults={'name': request.user.display_name, 'role': ''},
        )
        if request.method in ('PATCH', 'PUT', 'POST'):
            write = DeveloperWriteSerializer(
                profile, data=request.data, partial=request.method != 'POST'
            )
            write.is_valid(raise_exception=True)
            write.save()
        return Response(DeveloperSerializer(profile).data)

    @action(
        detail=False,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/photo',
        parser_classes=[MultiPartParser, FormParser],
        throttle_classes=[UploadRateThrottle],
    )
    def photo(self, request):
        profile, _ = Developer.objects.get_or_create(
            user=request.user,
            defaults={'name': request.user.display_name, 'role': ''},
        )

        if request.method == 'DELETE':
            public_id = profile.profile_image_public_id
            profile.profile_image = ''
            profile.profile_image_public_id = ''
            profile.save(update_fields=['profile_image', 'profile_image_public_id', 'updated_at'])
            if public_id:
                storage.delete_image(public_id)
            return Response(DeveloperSerializer(profile).data)

    @action(
        detail=False,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/photo',
        parser_classes=[MultiPartParser, FormParser],
    )
    def photo(self, request):
        profile, _ = Developer.objects.get_or_create(
            user=request.user,
            defaults={'name': request.user.display_name, 'role': ''},
        )

        if request.method == 'DELETE':
            public_id = profile.profile_image_public_id
            profile.profile_image = ''
            profile.profile_image_public_id = ''
            profile.save(update_fields=['profile_image', 'profile_image_public_id', 'updated_at'])
            if public_id:
                storage.delete_image(public_id)
            return Response(DeveloperSerializer(profile).data)

        uploaded = request.FILES.get('image') or request.FILES.get('file')
        if not uploaded:
            raise ValidationError({'image': ['No image file was provided.']})

        old_public_id = profile.profile_image_public_id
        try:
            result = storage.upload_profile_image(uploaded, request.user.id)
        except storage.StorageNotConfigured:
            return Response(
                {'detail': 'Image uploads are not configured on the server.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except storage.UnsupportedImage as exc:
            raise ValidationError({'image': [str(exc)]})
        except storage.StorageError:
            return Response(
                {'detail': 'Image upload failed. Please try again.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Persist first, then remove the previous asset so a DB failure never
        # leaves the profile pointing at a deleted image.
        with transaction.atomic():
            profile.profile_image = result['url']
            profile.profile_image_public_id = result['public_id']
            profile.save(update_fields=['profile_image', 'profile_image_public_id', 'updated_at'])

        if old_public_id and old_public_id != result['public_id']:
            storage.delete_image(old_public_id)

        return Response(DeveloperSerializer(profile).data)
