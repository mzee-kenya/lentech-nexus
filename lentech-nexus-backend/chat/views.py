"""API views for conversations and messages.

Access rules
------------
* Every endpoint requires authentication.
* ``get_queryset`` only ever returns conversations the caller belongs to, so
  fetching someone else's thread naturally returns 404 rather than leaking data.
* Direct chats are de-duplicated: starting a 1:1 chat that already exists
  returns the existing thread instead of creating a second one.
"""

from django.contrib.auth import get_user_model
from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Conversation, ConversationMember, Message
from .serializers import (
    ConversationSerializer,
    ConversationWriteSerializer,
    MemberSerializer,
    MessageSerializer,
)

User = get_user_model()


class ConversationViewSet(viewsets.GenericViewSet,
                          viewsets.mixins.ListModelMixin,
                          viewsets.mixins.RetrieveModelMixin):
    """List the caller's conversations, start new ones, and exchange messages."""

    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer

    def get_queryset(self):
        """Conversations the caller belongs to, newest activity first.

        A ``Subquery`` pulls the newest message's body/time/sender in the same
        query the list uses, so previews cost nothing extra.
        """
        if getattr(self, 'swagger_fake_view', False):
            return Conversation.objects.none()

        user = self.request.user
        latest = Message.objects.filter(conversation=OuterRef('pk')).order_by('-created_at')
        return (
            Conversation.objects.filter(members__user=user)
            .prefetch_related('members__user', 'members__user__developer_profile')
            .annotate(
                last_message_body=Subquery(latest.values('body')[:1]),
                last_message_at=Subquery(latest.values('created_at')[:1]),
                last_message_sender_id=Subquery(latest.values('sender_id')[:1]),
            )
            .distinct()
        )

    # -- create --------------------------------------------------------------

    def create(self, request, *args, **kwargs):
        write = ConversationWriteSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        write.is_valid(raise_exception=True)
        data = write.validated_data
        member_ids = data['member_ids']

        # Direct chats are unique per pair of users. We first narrow to threads
        # containing both people, then confirm the pair has no extra members.
        if data['kind'] == Conversation.Kind.DIRECT:
            candidates = (
                Conversation.objects.filter(kind=Conversation.Kind.DIRECT)
                .filter(members__user=request.user)
                .filter(members__user_id=member_ids[0])
                .distinct()
            )
            existing = next(
                (c for c in candidates if c.members.count() == 2),
                None,
            )
            if existing:
                conversation = self.get_queryset().get(pk=existing.pk)
                return Response(
                    ConversationSerializer(
                        conversation, context=self.get_serializer_context()
                    ).data,
                    status=status.HTTP_200_OK,
                )

        conversation = Conversation.objects.create(
            kind=data['kind'],
            title=data['title'],
            created_by=request.user,
        )
        # The creator becomes the owner; everyone else is a regular member.
        ConversationMember.objects.create(
            conversation=conversation, user=request.user, role=ConversationMember.Role.OWNER
        )
        ConversationMember.objects.bulk_create(
            [
                ConversationMember(conversation=conversation, user_id=uid)
                for uid in member_ids
            ]
        )

        conversation = self.get_queryset().get(pk=conversation.pk)
        return Response(
            ConversationSerializer(conversation, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    # -- messages ------------------------------------------------------------

    @action(detail=True, methods=['get', 'post'])
    def messages(self, request, pk=None):
        """GET the message history (paginated), or POST a new message."""
        conversation = self.get_object()  # 404s when the caller is not a member

        if request.method == 'GET':
            # Opening the thread counts as reading it: stamp the member's
            # ``last_read_at`` so the navbar badge clears for this conversation.
            ConversationMember.objects.filter(
                conversation=conversation, user=request.user
            ).update(last_read_at=timezone.now())

            queryset = conversation.messages.select_related(
                'sender', 'sender__developer_profile'
            )
            page = self.paginate_queryset(queryset)
            if page is not None:
                return self.get_paginated_response(MessageSerializer(page, many=True).data)
            return Response(MessageSerializer(queryset, many=True).data)

        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save(conversation=conversation, sender=request.user)
        # Bump the conversation so it floats to the top of everyone's list.
        conversation.save(update_fields=['updated_at'])
        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)

    # -- notifications -------------------------------------------------------

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Total unread messages for the caller, used by the navbar badge.

        Aggregating across every conversation in one call keeps the notification
        poll cheap (the frontend hits this on an interval).
        """
        total = 0
        memberships = ConversationMember.objects.filter(user=request.user)
        for membership in memberships:
            queryset = Message.objects.filter(
                conversation_id=membership.conversation_id
            ).exclude(sender=request.user)
            if membership.last_read_at is not None:
                queryset = queryset.filter(created_at__gt=membership.last_read_at)
            total += queryset.count()
        return Response({'unread': total})

    # -- membership ----------------------------------------------------------

    def _require_group(self, conversation):
        if conversation.kind != Conversation.Kind.GROUP:
            raise ValidationError('Membership can only be changed on group chats.')

    @action(detail=True, methods=['post'], url_path='members')
    def add_member(self, request, pk=None):
        """Add a user to a group conversation (any member may invite)."""
        conversation = self.get_object()
        self._require_group(conversation)

        user_id = request.data.get('user_id')
        if not user_id:
            raise ValidationError({'user_id': 'This field is required.'})
        user = get_object_or_404(User, pk=user_id)
        if conversation.members.filter(user=user).exists():
            raise ValidationError('That user is already in this conversation.')

        membership = ConversationMember.objects.create(conversation=conversation, user=user)
        return Response(
            MemberSerializer(membership).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['delete'],
            url_path=r'members/(?P<user_id>[^/.]+)')
    def remove_member(self, request, pk=None, user_id=None):
        """Remove a member: the owner may remove anyone, others only themselves."""
        conversation = self.get_object()
        self._require_group(conversation)

        membership = conversation.members.filter(user_id=user_id).first()
        if membership is None:
            raise NotFound('That user is not in this conversation.')

        viewer_is_owner = conversation.members.filter(
            user=request.user, role=ConversationMember.Role.OWNER
        ).exists()
        if str(request.user.id) != str(user_id) and not viewer_is_owner:
            raise PermissionDenied('Only the group owner can remove other members.')

        membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a conversation (removes the caller's membership)."""
        conversation = self.get_object()
        conversation.members.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
