from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Public/self representation of a user. Never exposes password data."""

    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'display_name',
            'role',
            'is_staff',
            'date_joined',
        ]
        read_only_fields = ['id', 'username', 'is_staff', 'date_joined', 'role']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(
        write_only=True, style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'role',
        ]

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('That username is already taken.')
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('That email is already registered.')
        return value

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        # Run Django's configured password validators server-side.
        try:
            validate_password(attrs.get('password'))
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Authenticate with either a username or an email address."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        identifier = attrs.get('username')
        password = attrs.get('password')

        username = identifier
        if '@' in identifier:
            match = User.objects.filter(email__iexact=identifier).first()
            if match:
                username = match.username

        user = authenticate(request=self.context.get('request'), username=username, password=password)
        if not user:
            raise serializers.ValidationError('Invalid credentials.')
        if not user.is_active:
            raise serializers.ValidationError('This account is inactive.')
        attrs['user'] = user
        return attrs


class UserUpdateSerializer(serializers.ModelSerializer):
    """Account settings the owner may change about themselves.

    Note: `role`, `is_staff`, and `is_superuser` are intentionally excluded to
    prevent privilege escalation via the API.
    """

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def validate_email(self, value):
        if User.objects.filter(Q(email__iexact=value) & ~Q(pk=self.instance.pk)).exists():
            raise serializers.ValidationError('That email is already registered.')
        return value
