from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.views.generic import TemplateView
# from accounts.views import home_redirect, home_view, CustomEmailVerificationSentView, UserListView, download_windows, download_mac, update_game_progress, view_progress, leaderboard, CustomConfirmEmailView  # or accounts.views if you prefer
from accounts.views import (
    home_redirect,
    home_view,
    CustomEmailVerificationSentView,
    UserListView,
    download_windows,
    download_mac,
    update_game_progress,
    view_progress,
    leaderboard,
    CustomConfirmEmailView,
    CustomSignupView,
    CustomPasswordChangeView,
    LimitedLoginView,
    reset_game_progress
)
from accounts.api import get_userprogress,save_loadshredder_full,get_loadshredder_data,get_username,Task11LightingScenarioApi,unity_logout,CustomTokenObtainPairView,Task11TicketFixesApi, ReadTask08excel,ReadQandAexcel,RegisterView, ClientLoginView, UserDataView, ReadExcelAttemptView, Task11LightFixtureApi
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from accounts.views import CustomSignupView, CustomPasswordChangeView
from allauth.account.views import LoginView
from accounts import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('api/client-login/', ClientLoginView.as_view(), name='client-login'),
    # path('api/read-excel/', ReadExcelStaticView.as_view(), name='read-excel'),
    path('api/task02-energybilldata/', ReadExcelAttemptView.as_view(),
         name='read_excel_attempt'),
    path('api/QAdata/', ReadQandAexcel.as_view(),
         name='ReadQandAexcel'),
    path('api/task08-quizdata/', ReadTask08excel.as_view(),
         name='ReadTask08excel'),
    path('api/task11-lightfixturedata/', Task11LightFixtureApi.as_view(),
         name='Task11LightFixtureApi'),
    path('api/task11-ticketFixesApi/', Task11TicketFixesApi.as_view(),
         name='Task11TicketFixesApi'),
    path('api/task11-lightingScenarioApi/', Task11LightingScenarioApi.as_view(),
         name='Task11LightingScenarioApi'),
    path('admin/', admin.site.urls),
    path('accounts/signup/', CustomSignupView.as_view(), name='account_signup'),
    # path('accounts/login/', LoginView.as_view(), name='account_login'),
    path('accounts/login/', LimitedLoginView.as_view(),
         name='account_login'),   # UPDATED
    

    path("accounts/password/change/", CustomPasswordChangeView.as_view(),
         name="account_change_password"),

    path("accounts/confirm-email/<key>/",
         CustomConfirmEmailView.as_view(),
         name="account_confirm_email"),
    path('accounts/', include('allauth.urls')),
    path('', views.home_redirect, name='redirect-root'),  # Temporary redirect
    path('home/', views.home_view, name='home'),  # Actual home page view
    path('api/users/', views.UserListView.as_view(), name='user-list'),

    path('api/unity-logout/', unity_logout, name='unity_logout'),

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
     
    # path('test_email/', views.test_email, name='test_email'),
    path('user_data/<str:user_id>/', UserDataView.as_view(), name='user-data'),
    path('api/get-username/', get_username, name='get_username'),
    path('api/loadshredderdata/', get_loadshredder_data, name='get_loadshredder_data'),
    path('api/get_userprogressdata/', get_userprogress, name='get_userprogress'),
    path('api/save-loadshredderscore/', save_loadshredder_full, name='save_loadshredder_full'),
    path('api/reset_game_progress/', reset_game_progress, name='reset_game_progress')

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
