"""Ensure that all endpoints called on the client side ends with a `/` to avoid 404 errors.
"""

from django.urls import path

from api.auth.otp import ResendOTPView, VerifyOTPView, RegisterView
from api.auth.reset_password import PasswordResetRequestView, PasswordResetTokenValidateView, PasswordResetView, ResendPasswordResetView
from api.email_views import EmailVerify

from api.views import (
    CurrentUserView,
    LogoutView,
    ObtainTokenPairView, 
    PostViewSet, 
    LikePostView,
    TrendingPostListView,
    UpdateUserView,
    UserViewSet,
    LikedPostsViewSet,
)

from rest_framework_simplejwt.views import TokenRefreshView

from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("posts", PostViewSet, basename="posts")
router.register('recipes/favorites', LikedPostsViewSet, basename='favorites')
router.register("users", UserViewSet, basename="users")

urlpatterns = [
    path('auth/login/', ObtainTokenPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    path('posts/<uuid:id>/like/', LikePostView.as_view(), name='like_post'),
    path('posts/trending/', TrendingPostListView.as_view(), name='trending_posts'),

    path('auth/user/', CurrentUserView.as_view(), name='current_user'),
    path('auth/update-user/', UpdateUserView.as_view(), name='update_user'),

    path('email-verify/<uidb64>/<token>/', EmailVerify.as_view(), name='email-verify'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('auth/resend-otp/', ResendOTPView.as_view(), name='resend-otp'),

    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('auth/password-reset/validate-token/<uidb64>/<token>/', PasswordResetTokenValidateView.as_view(), name='password_reset_token_validate'),
    path('auth/password-reset/confirm/<uidb64>/<token>/', PasswordResetView.as_view(), name='password_reset_confirm'),
    path('auth/password-reset/resend/', ResendPasswordResetView.as_view(), name='resend_password_reset'),
]

urlpatterns += router.urls
