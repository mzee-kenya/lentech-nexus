from rest_framework.routers import DefaultRouter

from .views import DeveloperViewSet

router = DefaultRouter()
router.register('developers', DeveloperViewSet, basename='developer')

urlpatterns = router.urls
