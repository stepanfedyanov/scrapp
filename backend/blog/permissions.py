from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, 'owner', None)
        if owner is not None:
            return owner == request.user
        blog = getattr(obj, 'blog', None)
        if blog is not None:
            return getattr(blog, 'owner', None) == request.user
        note = getattr(obj, 'note', None)
        if note is not None:
            blog = getattr(note, 'blog', None)
            if blog is not None:
                return getattr(blog, 'owner', None) == request.user
        return False
