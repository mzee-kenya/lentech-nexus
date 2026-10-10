from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class Idea(TimeStampedModel):
    """A user-submitted idea that others can express interest in."""

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        REALIZED = 'realized', 'Realized'
        ARCHIVED = 'archived', 'Archived'

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ideas'
    )
    title = models.CharField(max_length=160)
    summary = models.CharField(max_length=280, blank=True)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title


class IdeaInterest(TimeStampedModel):
    """A user's offer to collaborate on an idea, reviewed by the author."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        DECLINED = 'declined', 'Declined'
        WITHDRAWN = 'withdrawn', 'Withdrawn'

    idea = models.ForeignKey(Idea, on_delete=models.CASCADE, related_name='interests')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='idea_interests'
    )
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['idea', 'user'],
                condition=models.Q(status='pending'),
                name='unique_pending_idea_interest',
            )
        ]

    def __str__(self):
        return f'{self.user} -> {self.idea} ({self.status})'
