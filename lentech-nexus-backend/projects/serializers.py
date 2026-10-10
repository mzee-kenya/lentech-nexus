from rest_framework import serializers

from .models import Project, ProjectJoinRequest, ProjectMembership


class OwnerMixin(serializers.Serializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    owner_display_name = serializers.CharField(source='owner.display_name', read_only=True)


class ProjectListSerializer(OwnerMixin, serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'summary', 'status', 'technologies',
            'owner_username', 'owner_display_name', 'member_count', 'created_at',
        ]


class ProjectMembershipSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    display_name = serializers.CharField(source='user.display_name', read_only=True)

    class Meta:
        model = ProjectMembership
        fields = ['id', 'user', 'username', 'display_name', 'role', 'created_at']
        read_only_fields = ['id', 'user', 'username', 'display_name', 'created_at']


class ProjectDetailSerializer(OwnerMixin, serializers.ModelSerializer):
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)
    members = ProjectMembershipSerializer(source='memberships', many=True, read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    viewer_is_member = serializers.SerializerMethodField()
    viewer_is_owner = serializers.SerializerMethodField()
    viewer_request_status = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'summary', 'description', 'technologies',
            'repo_url', 'live_url', 'status',
            'owner_id', 'owner_username', 'owner_display_name',
            'members', 'member_count',
            'viewer_is_member', 'viewer_is_owner', 'viewer_request_status',
            'created_at', 'updated_at',
        ]

    def _user(self):
        request = self.context.get('request')
        return getattr(request, 'user', None)

    def get_viewer_is_member(self, obj) -> bool:
        user = self._user()
        if not user or not user.is_authenticated:
            return False
        return any(m.user_id == user.id for m in obj.memberships.all())

    def get_viewer_is_owner(self, obj) -> bool:
        user = self._user()
        return bool(user and user.is_authenticated and obj.owner_id == user.id)

    def get_viewer_request_status(self, obj) -> str | None:
        user = self._user()
        if not user or not user.is_authenticated:
            return None
        req = next((r for r in obj.join_requests.all() if r.requester_id == user.id), None)
        return req.status if req else None


class ProjectWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['title', 'summary', 'description', 'technologies', 'repo_url', 'live_url', 'status']

    def validate_technologies(self, value):
        if not isinstance(value, list) or not all(isinstance(t, str) for t in value):
            raise serializers.ValidationError('Technologies must be a list of strings.')
        cleaned = []
        for tech in value:
            tech = tech.strip()
            if tech and tech not in cleaned:
                cleaned.append(tech)
        if len(cleaned) > 40:
            raise serializers.ValidationError('A maximum of 40 technologies is allowed.')
        return cleaned

    def validate_title(self, value):
        value = value.strip()
        if len(value) < 3:
            raise serializers.ValidationError('Title must be at least 3 characters.')
        return value


class ProjectJoinRequestSerializer(serializers.ModelSerializer):
    requester_username = serializers.CharField(source='requester.username', read_only=True)
    requester_display_name = serializers.CharField(source='requester.display_name', read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)

    class Meta:
        model = ProjectJoinRequest
        fields = [
            'id', 'project', 'project_title', 'requester', 'requester_username',
            'requester_display_name', 'message', 'status', 'reviewed_at', 'created_at',
        ]
        read_only_fields = [
            'id', 'project', 'requester', 'requester_username', 'requester_display_name',
            'project_title', 'status', 'reviewed_at', 'created_at',
        ]
