"""Ensure that all endpoints called on the client side ends with a `/` to avoid 404 errors.
"""

from django.urls import path

from api.views import (
    ObtainTokenPairView, 
    RegisterView, 
    PostViewSet, 
    LikePostView
)

from rest_framework_simplejwt.views import TokenRefreshView

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("posts", PostViewSet, basename="posts")

urlpatterns = [
    path('auth/login/', ObtainTokenPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', RegisterView.as_view(), name='register'),

    path('posts/<uuid:id>/like/', LikePostView.as_view(), name='like_post'),
]

urlpatterns += router.urls
