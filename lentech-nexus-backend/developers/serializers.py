from rest_framework import serializers

from .models import Developer


class DeveloperSerializer(serializers.ModelSerializer):
    """Read serializer for public developer profiles."""

    username = serializers.CharField(source='user.username', read_only=True, default=None)
    user_id = serializers.IntegerField(source='user.id', read_only=True, default=None)

    class Meta:
        model = Developer
        fields = [
            'id',
            'user_id',
            'username',
            'name',
            'role',
            'bio',
            'profile_image',
            'skills',
            'github_url',
            'linkedin_url',
            'website_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class DeveloperWriteSerializer(serializers.ModelSerializer):
    """Write serializer.

    `user` and the Cloudinary identifiers are intentionally read-only so a
    client cannot claim another user's profile or forge image references.
    """

    class Meta:
        model = Developer
        fields = [
            # `name` is intentionally absent: it is derived from the linked
            # user's display name and cannot be claimed via the API.
            'role',
            'bio',
            'skills',
            'github_url',
            'linkedin_url',
            'website_url',
        ]

    def validate_skills(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('Skills must be a list of strings.')
        cleaned = []
        for skill in value:
            if not isinstance(skill, str):
                raise serializers.ValidationError('Each skill must be a string.')
            skill = skill.strip()
            if skill and skill not in cleaned:
                cleaned.append(skill)
        if len(cleaned) > 30:
            raise serializers.ValidationError('A maximum of 30 skills is allowed.')
        return cleaned
