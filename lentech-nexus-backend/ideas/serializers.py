from rest_framework import serializers

from .models import Idea, IdeaInterest


class AuthorMixin(serializers.Serializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_display_name = serializers.CharField(source='author.display_name', read_only=True)


class IdeaListSerializer(AuthorMixin, serializers.ModelSerializer):
    interest_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Idea
        fields = [
            'id', 'title', 'summary', 'status', 'tags',
            'author_username', 'author_display_name', 'interest_count', 'created_at',
        ]


class IdeaDetailSerializer(AuthorMixin, serializers.ModelSerializer):
    author_id = serializers.IntegerField(source='author.id', read_only=True)
    interest_count = serializers.IntegerField(read_only=True)
    viewer_is_author = serializers.SerializerMethodField()
    viewer_interest_status = serializers.SerializerMethodField()

    class Meta:
        model = Idea
        fields = [
            'id', 'title', 'summary', 'description', 'tags', 'status',
            'author_id', 'author_username', 'author_display_name',
            'interest_count', 'viewer_is_author', 'viewer_interest_status',
            'created_at', 'updated_at',
        ]

    def _user(self):
        request = self.context.get('request')
        return getattr(request, 'user', None)

    def get_viewer_is_author(self, obj) -> bool:
        user = self._user()
        return bool(user and user.is_authenticated and obj.author_id == user.id)

    def get_viewer_interest_status(self, obj) -> str | None:
        user = self._user()
        if not user or not user.is_authenticated:
            return None
        interest = next((i for i in obj.interests.all() if i.user_id == user.id), None)
        return interest.status if interest else None


class IdeaWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Idea
        fields = ['title', 'summary', 'description', 'tags', 'status']

    def validate_title(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError('Title must be at least 3 characters.')
        return value

    def validate_tags(self, value):
        if not isinstance(value, list) or not all(isinstance(t, str) for t in value):
            raise serializers.ValidationError('Tags must be a list of strings.')
        cleaned = []
        for tag in value:
            tag = tag.strip()
            if tag and tag not in cleaned:
                cleaned.append(tag)
        if len(cleaned) > 20:
            raise serializers.ValidationError('A maximum of 20 tags is allowed.')
        return cleaned


class IdeaInterestSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_display_name = serializers.CharField(source='user.display_name', read_only=True)
    idea_title = serializers.CharField(source='idea.title', read_only=True)

    class Meta:
        model = IdeaInterest
        fields = [
            'id', 'idea', 'idea_title', 'user', 'user_username', 'user_display_name',
            'message', 'status', 'created_at',
        ]
        read_only_fields = [
            'id', 'idea', 'user', 'user_username', 'user_display_name',
            'idea_title', 'status', 'created_at',
        ]
