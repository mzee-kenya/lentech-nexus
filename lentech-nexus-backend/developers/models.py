from django.conf import settings
from django.db import models


class Developer(models.Model):
    """A public developer profile.

    One profile per authenticated user. The profile is created lazily the first
    time a user opens their profile settings, and everything writable here is
    owned by that user.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='developer_profile',
        null=True,
        blank=True,
    )

    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    bio = models.TextField(blank=True)

    # Image is stored in Cloudinary; the DB keeps only the reference + id.
    profile_image = models.URLField(blank=True)
    profile_image_public_id = models.CharField(max_length=255, blank=True)

    # Store skills as a JSON list, for example: ["React", "Python", "Django"].
    skills = models.JSONField(default=list, blank=True)

    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Keep the display name in sync with the linked user when possible.
        if self.user and not self.name:
            self.name = self.user.display_name
        super().save(*args, **kwargs)
