from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class Project(TimeStampedModel):
    """A software project published on Lentech Nexus."""

    class Status(models.TextChoices):
        PLANNING = 'planning', 'Planning'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        ARCHIVED = 'archived', 'Archived'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_projects',
    )
    title = models.CharField(max_length=160)
    summary = models.CharField(max_length=280, blank=True)
    description = models.TextField(blank=True)
    technologies = models.JSONField(default=list, blank=True)
    repo_url = models.URLField(blank=True)
    live_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNING)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title


class ProjectMembership(TimeStampedModel):
    """Links a user to a project with a collaboration role."""

    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner'
        MAINTAINER = 'maintainer', 'Maintainer'
        CONTRIBUTOR = 'contributor', 'Contributor'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_memberships'
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CONTRIBUTOR)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['project', 'user'], name='unique_project_member')
        ]

    def __str__(self):
        return f'{self.user} in {self.project} ({self.role})'


class ProjectJoinRequest(TimeStampedModel):
    """A user's request to join a project, reviewed by the project owner."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        CANCELLED = 'cancelled', 'Cancelled'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='join_requests')
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='project_join_requests'
    )
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            # A user may have at most one *pending* request per project.
            models.UniqueConstraint(
                fields=['project', 'requester'],
                condition=models.Q(status='pending'),
                name='unique_pending_join_request',
            )
        ]

    def __str__(self):
        return f'{self.requester} -> {self.project} ({self.status})'
