from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    BlogIntegrationViewSet,
    BlogViewSet,
    IntegrationViewSet,
    NoteHeaderViewSet,
    NoteIntegrationViewSet,
    NoteTextContentViewSet,
    NoteViewSet,
    RegisterViewSet,
)

router = DefaultRouter()
router.register('auth/register', RegisterViewSet, basename='register')
router.register('blogs', BlogViewSet, basename='blogs')
router.register('notes', NoteViewSet, basename='notes')
router.register('integrations', IntegrationViewSet, basename='integrations')
router.register(
    'blog-integrations',
    BlogIntegrationViewSet,
    basename='blog-integrations',
)
router.register(
    'note-integrations',
    NoteIntegrationViewSet,
    basename='note-integrations',
)
router.register('note-headers', NoteHeaderViewSet, basename='note-headers')
router.register(
    'note-text-contents',
    NoteTextContentViewSet,
    basename='note-text-contents',
)

urlpatterns = [
    path(
        'auth/token/',
        TokenObtainPairView.as_view(),
        name='token_obtain_pair',
    ),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]
