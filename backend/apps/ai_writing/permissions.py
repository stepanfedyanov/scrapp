from rest_framework.permissions import BasePermission, IsAuthenticated


class HasAIAccess(BasePermission):
    """
    Grants access only to authenticated users who have been explicitly
    granted the `ai_writing.can_use_ai` permission via the Django admin.
    """

    message = 'AI features are not enabled for your account.'

    def has_permission(self, request, view):
        return (
            IsAuthenticated().has_permission(request, view)
            and request.user.has_perm('ai_writing.can_use_ai')
        )
