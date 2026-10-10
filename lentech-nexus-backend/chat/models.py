"""Data models for one-to-one and group messaging.

Structure
---------
* :class:`Conversation`       – a thread. ``kind`` is either ``direct``
  (exactly two members) or ``group`` (two or more members, with a title).
* :class:`ConversationMember` – join table between users and conversations.
  Storing membership explicitly lets us add roles (owner/member) and timestamps.
* :class:`Message`            – a single chat message inside a conversation.
"""

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class Conversation(TimeStampedModel):
    """A chat thread: either a direct 1:1 chat or a named group."""

    class Kind(models.TextChoices):
        DIRECT = 'direct', 'Direct'
        GROUP = 'group', 'Group'

    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.DIRECT)

    # Only meaningful for groups; direct chats derive their title from members.
    title = models.CharField(max_length=120, blank=True)

    # Who created the thread. Kept nullable so deleting a user does not delete
    # the conversation history for everyone else.
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_conversations',
    )

    class Meta:
        # Most-recently active conversation first.
        ordering = ['-updated_at']
        indexes = [models.Index(fields=['-updated_at'])]

    def __str__(self) -> str:
        return self.title or f'{self.kind} #{self.pk}'

    def is_member(self, user) -> bool:
        """True when ``user`` belongs to this conversation."""
        if not user or not user.is_authenticated:
            return False
        return self.members.filter(user=user).exists()

    def other_member(self, user):
        """Return the other user in a direct chat (or ``None``)."""
        if self.kind != self.Kind.DIRECT:
            return None
        return (
            self.members.select_related('user', 'user__developer_profile')
            .exclude(user=user)
            .first()
            .user
        )

    def display_title(self, user) -> str:
        """A human-friendly label: group title, or the peer's name for direct."""
        if self.title:
            return self.title
        other = self.other_member(user)
        return other.display_name if other else 'Conversation'


class ConversationMember(models.Model):
    """Membership of a user in a conversation."""

    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner'
        MEMBER = 'member', 'Member'

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='members',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversation_memberships',
    )
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    # Tracks the last time this member opened the thread. Messages created after
    # this timestamp (from other people) count as "unread" and drive the navbar
    # notification badge. ``None`` means the member has never read the thread.
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            # A user can only be added to a conversation once.
            models.UniqueConstraint(
                fields=['conversation', 'user'], name='unique_conversation_member'
            ),
        ]
        indexes = [models.Index(fields=['user', 'conversation'])]

    def __str__(self) -> str:
        return f'{self.user_id} in {self.conversation_id} ({self.role})'


class Message(TimeStampedModel):
    """A single message inside a conversation."""

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messages',
    )
    body = models.TextField()

    class Meta:
        # Chat reads oldest-first; clients can scroll back in time.
        ordering = ['created_at']
        indexes = [models.Index(fields=['conversation', 'created_at'])]

    def __str__(self) -> str:
        return f'{self.sender_id}: {self.body[:30]}'
