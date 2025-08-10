from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import PostViewSet, SubPostViewSet

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post")
router.register(r"subposts", SubPostViewSet, basename="subpost")

urlpatterns = [
    path("", include(router.urls)),
]
