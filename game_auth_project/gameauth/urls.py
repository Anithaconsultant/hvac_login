from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.generic import TemplateView
from accounts.views import home_redirect, home_view, CustomEmailVerificationSentView, UserListView, download_windows, download_mac, update_game_progress, view_progress, leaderboard  # or accounts.views if you prefer
from accounts.api import CustomTokenObtainPairView, RegisterView, ClientLoginView
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('api/token/', CustomTokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('admin/', admin.site.urls),
    path('accounts/confirm-email/', CustomEmailVerificationSentView.as_view(),
         name='account_email_verification_sent'),
    path('accounts/', include('allauth.urls')),
    path('', home_redirect, name='redirect-root'),  # Temporary redirect
    path('home/', home_view, name='home'),  # Actual home page view
    path('api/users/', UserListView.as_view(), name='user-list'),
    path('api/client-login/', ClientLoginView.as_view(), name='client-login'),
    path('download_windows/', download_windows, name='download_windows'),
    path('download-mac/', download_mac, name='download_mac'),
    path('update-progress/', update_game_progress, name='update_progress'),
    path('view-progress/', view_progress, name='view_progress'),
    path('leaderboard/', leaderboard, name='leaderboard'),


]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
