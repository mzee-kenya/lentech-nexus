from rest_framework.routers import DefaultRouter

from .views import IdeaInterestViewSet, IdeaViewSet

router = DefaultRouter()
router.register('ideas', IdeaViewSet, basename='idea')
router.register('idea-interests', IdeaInterestViewSet, basename='idea-interest')

urlpatterns = router.urls