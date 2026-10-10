from rest_framework.routers import DefaultRouter

from .views import ProjectJoinRequestViewSet, ProjectViewSet

router = DefaultRouter()
router.register('projects', ProjectViewSet, basename='project')
router.register('join-requests', ProjectJoinRequestViewSet, basename='join-request')

urlpatterns = router.urls
