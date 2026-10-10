from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Object-level permission: anyone may read; only the owner may write.

    The object is expected to expose an `owner` or `user` attribute.
    """

    message = 'You do not have permission to modify this object.'

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        owner = getattr(obj, 'owner', None) or getattr(obj, 'user', None)
        return owner == request.user


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Object-level permission: anyone may read; only the author may write."""

    message = 'You do not have permission to modify this object.'

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        author = getattr(obj, 'author', None) or getattr(obj, 'user', None)
        return author == request.user


class IsOwnerOrAdmin(permissions.BasePermission):
    """Object-level permission: owner or staff may write."""

    message = 'You do not have permission to modify this object.'

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_staff:
            return True
        owner = getattr(obj, 'owner', None) or getattr(obj, 'user', None)
        return owner == request.user
