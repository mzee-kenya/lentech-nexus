"""Data models for the social feed.

The feed is intentionally simple and modular:

* :class:`Post`      – a short status update with optional image/video media.
* :class:`PostLike`  – one row per (post, user) pair, so a like is idempotent.
* :class:`Comment`   – a text reply on a post.

Media files are not stored here. Only the Cloudinary URL and public id are kept
on the post; the binary lives in Cloudinary (see ``core.services.storage``).
"""

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class Post(TimeStampedModel):
    """A single feed post authored by one user."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts',
    )

    # The text body. Optional: a post may be media-only.
    body = models.TextField(blank=True)

    # Image attachment (Cloudinary). Empty when the post has no image.
    image_url = models.URLField(blank=True)
    image_public_id = models.CharField(max_length=255, blank=True)

    # Video attachment (Cloudinary). Empty when the post has no video.
    # A post can carry at most one image and one video.
    video_url = models.URLField(blank=True)
    video_public_id = models.CharField(max_length=255, blank=True)

    class Meta:
        # Newest first is the natural feed order.
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author']),
        ]

    def __str__(self) -> str:
        preview = self.body[:40] or '<media>'
        return f'{self.author_id}: {preview}'

    @property
    def has_media(self) -> bool:
        """True when the post carries an image or a video."""
        return bool(self.image_url or self.video_url)


class PostLike(models.Model):
    """A like on a post.

    We use a plain join table rather than a ManyToManyField so we can record
    *when* the like happened and enforce "one like per user per post" at the
    database level.
    """

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='post_likes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # The database guarantees a user can only like a post once, even
            # under concurrent requests — application checks alone can race.
            models.UniqueConstraint(fields=['post', 'user'], name='unique_post_like'),
        ]
        indexes = [models.Index(fields=['post', 'created_at'])]

    def __str__(self) -> str:
        return f'{self.user_id} ♥ post {self.post_id}'


class Comment(TimeStampedModel):
    """A text comment left on a post."""

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    body = models.TextField()

    class Meta:
        # Comments read best oldest-first (a conversation thread).
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
        ]

    def __str__(self) -> str:
        return f'{self.author_id} on {self.post_id}: {self.body[:30]}'
