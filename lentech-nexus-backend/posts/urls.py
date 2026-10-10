from rest_framework.routers import DefaultRouter

from .views import CommentViewSet, PostViewSet

# `DefaultRouter` also generates the browsable API root, which is handy while
# developing against the endpoints in the browser.
router = DefaultRouter()
router.register('posts', PostViewSet, basename='post')
router.register('comments', CommentViewSet, basename='comment')

urlpatterns = router.urls
