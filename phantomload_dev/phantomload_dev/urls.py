from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.generic import TemplateView
from accounts.views import home_redirect, home_view, CustomEmailVerificationSentView, UserListView, download_windows, download_mac, update_game_progress, view_progress, leaderboard ,CustomConfirmEmailView # or accounts.views if you prefer
from accounts.api import CustomTokenObtainPairView, RegisterView, ClientLoginView, UserDataView, ReadExcelAttemptView, FilterCSVDataTask09
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from accounts.views import CustomSignupView
from allauth.account.views import LoginView
from accounts import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('api/token/', CustomTokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/register/', RegisterView.as_view(), name='register'),
    # path('api/read-excel/', ReadExcelStaticView.as_view(), name='read-excel'),
    path('api/read-excel-task2/', ReadExcelAttemptView.as_view(),
         name='read_excel_attempt'),
    path('api/filterdata-Task09/', FilterCSVDataTask09.as_view(),
         name='FilterCSVDataTask09'),
    path('admin/', admin.site.urls),
    path('accounts/signup/', CustomSignupView.as_view(), name='account_signup'),
    path('accounts/login/', LoginView.as_view(), name='account_login'),
   
    path('accounts/', include('allauth.urls')),
    path("accounts/confirm-email/<key>/",
         CustomConfirmEmailView.as_view(),
         name="account_confirm_email"),                                      
    path('', views.home_redirect, name='redirect-root'),  # Temporary redirect
    path('home/', views.home_view, name='home'),  # Actual home page view
    path('api/users/', views.UserListView.as_view(), name='user-list'),
    path('api/client-login/', ClientLoginView.as_view(), name='client-login'),

    path('download_windows/', views.download_windows, name='download_windows'),
    path('download-mac/', views.download_mac, name='download_mac'),
    path('update-progress/', views.update_game_progress,
         name='update_game_progress'),
    path('view-progress/', views.view_progress, name='view_progress'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('feedback/', views.feedback_view, name='feedback'),                                                        
    path('about/', views.about, name='about'),
    path('credits/', views.credits, name='credits'),
    path('profile/', views.profile, name='profile'),
    path('user_data/<str:user_id>/', UserDataView.as_view(), name='user-data'),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
