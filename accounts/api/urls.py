from django.urls import path
from .views import (
    oauth_callback,
    oauth_user_info,
    oauth_login
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

app_name = "oauth_api"

urlpatterns = [
    path("oauth/login/", oauth_login, name="oauth_login"),
    path("oauth/callback/", oauth_callback, name="oauth_callback"),
    path("oauth/user-info/", oauth_user_info, name="oauth_user_info"),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
]
