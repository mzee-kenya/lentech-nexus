"""Serializers for chat conversations and messages.

Reads expose a consistent "user summary" (id/username/display name/avatar) so
the frontend can render message bubbles and member lists without extra calls.
Writes are handled by a small ``ConversationWriteSerializer`` because creating a
conversation is a multi-step operation better orchestrated in the view.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Conversation, ConversationMember, Message

User = get_user_model()


def _avatar(user) -> str:
    """Return the user's profile image URL, or '' when no profile exists."""
    profile = getattr(user, 'developer_profile', None)
    return getattr(profile, 'profile_image', '') or ''


class MemberSerializer(serializers.ModelSerializer):
    """A conversation member, flattened into a user summary."""

    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    display_name = serializers.CharField(source='user.display_name', read_only=True)
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = ConversationMember
        fields = ['user_id', 'username', 'display_name', 'avatar', 'role', 'joined_at']

    def get_avatar(self, obj) -> str:
        return _avatar(obj.user)


class MessageSerializer(serializers.ModelSerializer):
    """A chat message plus its sender's summary."""

    sender_id = serializers.IntegerField(source='sender.id', read_only=True)
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_display_name = serializers.CharField(source='sender.display_name', read_only=True)
    sender_avatar = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'conversation',
            'sender_id', 'sender_username', 'sender_display_name', 'sender_avatar',
            'body', 'created_at',
        ]
        read_only_fields = [
            'id', 'conversation',
            'sender_id', 'sender_username', 'sender_display_name', 'sender_avatar',
            'created_at',
        ]

    def get_sender_avatar(self, obj) -> str:
        return _avatar(obj.sender)

    def validate_body(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Message cannot be empty.')
        return value


class ConversationSerializer(serializers.ModelSerializer):
    """Read shape for a conversation, tailored to the requesting user.

    For direct chats ``display_title`` resolves to the other person's name, and
    ``viewer_role`` tells the client whether this user owns the group.
    """

    members = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    display_title = serializers.SerializerMethodField()
    viewer_role = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'kind', 'title', 'display_title', 'viewer_role',
            'members', 'member_count', 'last_message', 'unread_count',
            'created_at', 'updated_at',
        ]

    # -- helpers -------------------------------------------------------------

    def _viewer(self):
        request = self.context.get('request')
        return getattr(request, 'user', None)

    # -- fields --------------------------------------------------------------

    def get_members(self, obj) -> list:
        # ``obj.members`` is typically prefetched by the view, avoiding N+1.
        return MemberSerializer(obj.members.all(), many=True).data

    def get_member_count(self, obj) -> int:
        return len(obj.members.all())

    def get_display_title(self, obj) -> str:
        return obj.display_title(self._viewer())

    def get_viewer_role(self, obj) -> str | None:
        viewer = self._viewer()
        if not viewer or not viewer.is_authenticated:
            return None
        member = next(
            (m for m in obj.members.all() if m.user_id == viewer.id),
            None,
        )
        return member.role if member else None

    def get_last_message(self, obj) -> dict | None:
        """Return a compact preview of the newest message.

        The view annotates ``last_message_body`` / ``last_message_at`` /
        ``last_message_sender_id`` so this never triggers an extra query.
        """
        body = getattr(obj, 'last_message_body', None)
        sent_at = getattr(obj, 'last_message_at', None)
        sender_id = getattr(obj, 'last_message_sender_id', None)
        if body is None and sent_at is None:
            return None
        return {'body': body or '', 'sender_id': sender_id, 'created_at': sent_at}

    def get_unread_count(self, obj) -> int:
        """Number of messages the viewer has not seen yet.

        A message counts as unread when it came from someone else and was
        created after the viewer's ``last_read_at`` (or ever, if the viewer has
        never opened the thread).
        """
        viewer = self._viewer()
        if not viewer or not viewer.is_authenticated:
            return 0
        member = next(
            (m for m in obj.members.all() if m.user_id == viewer.id),
            None,
        )
        if member is None:
            return 0
        queryset = Message.objects.filter(conversation=obj).exclude(sender=viewer)
        if member.last_read_at is not None:
            queryset = queryset.filter(created_at__gt=member.last_read_at)
        return queryset.count()


class ConversationWriteSerializer(serializers.Serializer):
    """Validates a conversation-creation request.

    * ``direct`` requires exactly one other member.
    * ``group`` requires a title and at least one other member.
    """

    kind = serializers.ChoiceField(
        choices=Conversation.Kind.choices, default=Conversation.Kind.DIRECT
    )
    title = serializers.CharField(required=False, allow_blank=True, max_length=120)
    member_ids = serializers.ListField(child=serializers.IntegerField(), required=False)

    def validate(self, attrs):
        request = self.context['request']
        kind = attrs.get('kind', Conversation.Kind.DIRECT)
        title = (attrs.get('title') or '').strip()

        # De-duplicate while preserving order, and never include the creator —
        # the view adds them automatically as the owner.
        raw_ids = attrs.get('member_ids') or []
        member_ids = [uid for uid in dict.fromkeys(raw_ids) if uid != request.user.id]

        found = set(User.objects.filter(id__in=member_ids).values_list('id', flat=True))
        missing = [uid for uid in member_ids if uid not in found]
        if missing:
            raise serializers.ValidationError(
                {'member_ids': f'Unknown user id(s): {missing}.'}
            )

        if kind == Conversation.Kind.DIRECT:
            if len(member_ids) != 1:
                raise serializers.ValidationError(
                    {'member_ids': 'A direct chat needs exactly one other member.'}
                )
        else:
            if not title:
                raise serializers.ValidationError({'title': 'Group chats need a title.'})
            if not member_ids:
                raise serializers.ValidationError(
                    {'member_ids': 'Add at least one member to the group.'}
                )

        attrs['title'] = title
        attrs['member_ids'] = member_ids
        return attrs
