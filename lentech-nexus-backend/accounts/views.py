from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import filters, generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    LoginSerializer,
    PublicUserSerializer,
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

User = get_user_model()


_EmptySerializer = type('EmptySerializer', (serializers.Serializer,), {})


class CsrfView(APIView):
    """Sets the CSRF cookie so the SPA can read it before unsafe requests."""

    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    @extend_schema(
        responses=inline_serializer(
            'CsrfToken', fields={'csrfToken': serializers.CharField()}
        )
    )
    def get(self, request):
        return Response({'csrfToken': get_token(request)})


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_scope = 'auth'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Log the new user in immediately for a smooth first-run experience.
        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    throttle_scope = 'auth'

    @method_decorator(ensure_csrf_cookie)
    @extend_schema(request=LoginSerializer, responses=UserSerializer)
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={204: OpenApiResponse(description='Logged out')})
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserDirectoryView(generics.ListAPIView):
    """List other members so the chat UI can start conversations.

    The caller is excluded (you cannot chat with yourself) and ``?search=``
    matches username, first or last name for a type-ahead picker.
    """

    serializer_class = PublicUserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'first_name', 'last_name']

    def get_queryset(self):
        return (
            User.objects.exclude(pk=self.request.user.pk)
            .select_related('developer_profile')
            .order_by('username')
        )


class MeView(generics.RetrieveUpdateAPIView):
    """Return and update the authenticated user's own account."""

    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UserUpdateSerializer
        return UserSerializer


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=inline_serializer(
            'PasswordChange',
            fields={
                'old_password': serializers.CharField(),
                'new_password': serializers.CharField(),
            },
        ),
        responses={
            200: inline_serializer(
                'PasswordChangeOk', fields={'detail': serializers.CharField()}
            )
        },
    )
    def post(self, request):
        old_password = request.data.get('old_password', '')
        new_password = request.data.get('new_password', '')

        if not request.user.check_password(old_password):
            return Response(
                {'old_password': ['Current password is incorrect.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            validate_password(new_password, request.user)
        except DjangoValidationError as exc:
            return Response({'new_password': list(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_password)
        request.user.save()
        # Keep the current session valid after the password change.
        update_session_auth_hash(request, request.user)
        return Response({'detail': 'Password updated.'})
