"""Image and video storage boundary.

Everything that talks to Cloudinary lives in this one module so the rest of the
application depends on a small, testable interface instead of the Cloudinary SDK
directly. If Cloudinary is not configured (``CLOUDINARY_ENABLED=False``), the
upload functions raise :class:`StorageNotConfigured` and callers translate that
into a clear HTTP response instead of an unexpected crash.

Two kinds of media are supported today:

* ``image`` – profile photos and post photos (JPEG/PNG/WEBP/GIF).
* ``video`` – short videos attached to posts (MP4/WEBM/OGG/QuickTime).

Size limits are read from settings so operators can raise or lower them per
environment (see ``MAX_PROFILE_IMAGE_MB`` / ``MAX_POST_IMAGE_MB`` /
``MAX_POST_VIDEO_MB``).
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


# --- What we accept ---------------------------------------------------------

# Accepted MIME types per media kind. A set gives an O(1) membership test.
IMAGE_CONTENT_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
VIDEO_CONTENT_TYPES = {'video/mp4', 'video/webm', 'video/ogg', 'video/quicktime'}

# Short, stable identifiers used by callers and by Cloudinary's `resource_type`.
IMAGE = 'image'
VIDEO = 'video'

# Backwards-compatible alias: older code imported `ALLOWED_IMAGE_TYPES`.
ALLOWED_IMAGE_TYPES = IMAGE_CONTENT_TYPES


# --- Errors -----------------------------------------------------------------


class StorageError(Exception):
    """Base class for storage failures surfaced to the API layer."""


class StorageNotConfigured(StorageError):
    """Raised when an operation requires Cloudinary but it is disabled."""


class UnsupportedMedia(StorageError):
    """Raised when the uploaded file is not an accepted image/video type."""


# `UnsupportedImage` is kept as an alias so existing imports keep working.
UnsupportedImage = UnsupportedMedia


# --- Configuration helpers --------------------------------------------------


def is_enabled() -> bool:
    """Return True only when Cloudinary is switched on *and* fully configured."""
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
    """Apply the credentials from settings to the Cloudinary SDK.

    Must run before every upload because the SDK keeps global state.
    """
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


def _default_limit_mb(media_kind: str) -> int:
    """Return the configured default size limit (in MB) for a media kind."""
    if media_kind == VIDEO:
        return settings.MAX_POST_VIDEO_MB
    return settings.MAX_POST_IMAGE_MB


def _allowed_types(media_kind: str) -> set[str]:
    return VIDEO_CONTENT_TYPES if media_kind == VIDEO else IMAGE_CONTENT_TYPES


def _validate(uploaded_file, media_kind: str, max_mb: int | None = None) -> None:
    """Validate size and content type *before* any bytes leave the server."""
    limit_mb = max_mb if max_mb is not None else _default_limit_mb(media_kind)
    if uploaded_file.size > limit_mb * 1024 * 1024:
        raise UnsupportedMedia(f'File exceeds the {limit_mb}MB limit.')

    content_type = (getattr(uploaded_file, 'content_type', '') or '').lower()
    allowed = _allowed_types(media_kind)
    if content_type not in allowed:
        readable = ', '.join(sorted(allowed))
        raise UnsupportedMedia(f'Unsupported {media_kind} type. Use one of: {readable}.')


def _upload(uploaded_file, public_id: str, media_kind: str) -> dict:
    """Push validated bytes to Cloudinary and normalise the response."""
    _configure()
    data = uploaded_file.read()
    try:
        result = cloudinary.uploader.upload(
            io.BytesIO(data),
            folder=settings.CLOUDINARY_UPLOAD_FOLDER,
            public_id=public_id,
            resource_type=media_kind,
            overwrite=True,
            invalidate=True,
        )
    except CloudinaryError as exc:  # surface a clean error to the API
        raise StorageError(f'Upload failed: {exc}') from exc
    return {
        'url': result.get('secure_url') or result.get('url', ''),
        'public_id': result.get('public_id', ''),
    }


# --- Public API -------------------------------------------------------------


def upload_media(uploaded_file, owner_id, media_kind: str = IMAGE) -> dict:
    """Validate and upload an image or video; return ``{'url', 'public_id'}``.

    The caller is responsible for persisting those two values. No media bytes
    ever touch the database.
    """
    if not is_enabled():
        raise StorageNotConfigured(
            'Uploads are disabled. Configure Cloudinary to enable them.'
        )
    _validate(uploaded_file, media_kind)
    # A random public_id prevents collisions and avoids leaking original names.
    public_id = f'{media_kind}_{owner_id}_{uuid.uuid4().hex[:8]}'
    return _upload(uploaded_file, public_id, media_kind)


def upload_profile_image(uploaded_file, owner_id) -> dict:
    """Upload a profile image using the dedicated (usually smaller) size limit."""
    if not is_enabled():
        raise StorageNotConfigured(
            'Image uploads are disabled. Configure Cloudinary to enable them.'
        )
    _validate(uploaded_file, IMAGE, max_mb=settings.MAX_PROFILE_IMAGE_MB)
    public_id = f'profile_{owner_id}_{uuid.uuid4().hex[:8]}'
    return _upload(uploaded_file, public_id, IMAGE)


def delete_image(public_id: str) -> None:
    """Best-effort deletion of a stored asset. Never raises to the caller.

    Cloudinary needs the ``resource_type`` to match the original upload, so we
    try both image and video; the wrong one simply fails and is ignored.
    """
    if not public_id or not is_enabled():
        return
    _configure()
    for resource_type in (IMAGE, VIDEO):
        try:
            cloudinary.uploader.destroy(public_id, resource_type=resource_type, invalidate=True)
        except Exception:  # noqa: BLE001 - cleanup must not break the request
            continue
