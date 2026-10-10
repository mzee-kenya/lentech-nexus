"""Image storage boundary.

All Cloudinary access is isolated here so the rest of the application depends
on a small, testable interface rather than the Cloudinary SDK directly. If
Cloudinary is not configured (`CLOUDINARY_ENABLED=False`), the functions raise
``StorageNotConfigured`` and callers return a clear error instead of failing
unexpectedly.
"""

from __future__ import annotations

import io
import uuid

from django.conf import settings

try:  # Import lazily so the app still boots without the SDK installed.
    import cloudinary
    import cloudinary.uploader
    from cloudinary.exceptions import Error as CloudinaryError
except ImportError:  # pragma: no cover - only when dependency missing
    cloudinary = None

    class CloudinaryError(Exception):
        pass


ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
MAX_DIMENSION_CONTENT_PREFIX = 'image/'


class StorageError(Exception):
    """Base class for storage failures surfaced to the API layer."""


class StorageNotConfigured(StorageError):
    """Raised when an operation requires Cloudinary but it is disabled."""


class UnsupportedImage(StorageError):
    """Raised when the uploaded file is not an accepted image type."""


def is_enabled() -> bool:
    if not settings.CLOUDINARY_ENABLED:
        return False
    return all(
        [
            settings.CLOUDINARY_CLOUD_NAME,
            settings.CLOUDINARY_API_KEY,
            settings.CLOUDINARY_API_SECRET,
        ]
    )


def _configure():
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


def _validate_image(uploaded_file):
    max_bytes = settings.MAX_PROFILE_IMAGE_MB * 1024 * 1024
    if uploaded_file.size > max_bytes:
        raise UnsupportedImage(
            f'Image exceeds the {settings.MAX_PROFILE_IMAGE_MB}MB limit.'
        )

    content_type = (getattr(uploaded_file, 'content_type', '') or '').lower()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise UnsupportedImage(
            'Unsupported image type. Use JPEG, PNG, WEBP, or GIF.'
        )


def upload_profile_image(uploaded_file, owner_id) -> dict:
    """Validate and upload a profile image.

    Returns a dict with `url` and `public_id`. The caller is responsible for
    persisting those values; no image binaries touch the database.
    """
    if not is_enabled():
        raise StorageNotConfigured(
            'Image uploads are disabled. Configure Cloudinary to enable them.'
        )

    _validate_image(uploaded_file)
    _configure()

    data = uploaded_file.read()
    public_id = f'user_{owner_id}_{uuid.uuid4().hex[:8]}'

    try:
        result = cloudinary.uploader.upload(
            io.BytesIO(data),
            folder=settings.CLOUDINARY_UPLOAD_FOLDER,
            public_id=public_id,
            resource_type='image',
            overwrite=True,
            invalidate=True,
        )
    except CloudinaryError as exc:  # surface a clean error to the API
        raise StorageError(f'Image upload failed: {exc}') from exc

    return {
        'url': result.get('secure_url') or result.get('url', ''),
        'public_id': result.get('public_id', ''),
    }


def delete_image(public_id: str) -> None:
    """Best-effort deletion of a stored asset. Never raises to the caller."""
    if not public_id or not is_enabled():
        return
    _configure()
    try:
        cloudinary.uploader.destroy(public_id, invalidate=True)
    except Exception:  # noqa: BLE001 - cleanup must not break the request
        pass
