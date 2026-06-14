from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from accounts import views, api
from allauth.account.views import LoginView
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [

    # =========================
    # AUTH / LOGIN / SIGNUP
    # =========================
    path('accounts/signup/', views.CustomSignupView.as_view(), name='account_signup'),
    path('accounts/login/', views.LimitedLoginView.as_view(), name='account_login'),
    path("accounts/password/change/", views.CustomPasswordChangeView.as_view(), name="account_change_password"),
    path("accounts/confirm-email/<key>/", views.CustomConfirmEmailView.as_view(), name="account_confirm_email"),
    path("api/refresh/token/",TokenRefreshView.as_view(),name="token_refresh"),

    path('accounts/', include('allauth.urls')),

    # =========================
    # CORE PAGES
    # =========================
    path('', views.home_redirect, name='redirect-root'),
    path('home/', views.home_view, name='home'),
    #path('logout/', views.custom_logout, name='custom_logout'),

    path("Integrated_Build/", views.unity_game_view, name="Integrated_Build"),
    path("play-task/<str:task_name>/", views.play_task, name="play_task"),

    # =========================
    # ADMIN
    # =========================
    path('admin/', admin.site.urls),

    # =========================
    # USER APIs
    # =========================
    #path('api/users/', views.UserListView.as_view(), name='user-list'),
    path('user_data/<str:user_id>/', api.UserDataView.as_view(), name='user-data'),

    # =========================
    # AUTH / SESSION APIs-
    # =========================
    path("api/client-login/", api.ClientLoginView.as_view(), name="client-login"),
    #path("api/check-session/", api.CheckSessionView.as_view(), name="check-session"),
    
    path("api/logout/", views.custom_logout, name="account_logout"),

    # =========================
    # HEARTBEAT / UNITY SYNC
    # =========================
    #path("api/website-heartbeat/", api.WebsiteHeartbeatAPIView.as_view(), name="website-heartbeat"),
    path("api/webgl/ping/", api.WebGLPingAPIView.as_view(), name="webgl_ping"),
    path("api/webgl/close/", api.CloseWebGLSessionAPIView.as_view(), name="webgl-close"),

    # =========================
    # GAME PROGRESS
    # =========================
    path('update-progress/', views.update_game_progress, name='update_game_progress'),
    path('view-progress/', views.view_progress, name='view_progress'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('api/get_userprogressdata/', api.get_userprogress, name='get_userprogress'),
    path('api/post_loadshredderscore/', api.save_loadshredder_full, name='save_loadshredder_full'),
    path('api/reset_game_progress/', views.reset_game_progress, name='reset_game_progress'),
    path('api/get_loadshredderdata/', api.get_loadshredder_data, name='get_loadshredder_data'),
    path('api/get_trainingdata/', api.get_training_data, name='get_training_data'),
    path('api/post_trainingdata/', api.post_training_data, name='post_training_data'),

    # =========================
    # TASK DATA APIs
    # =========================
    path('api/task02-energybilldata/', api.ReadExcelAttemptView.as_view(), name='read_excel_attempt'),
    path('api/QAdata/', api.ReadQandAexcel.as_view(), name='ReadQandAexcel'),
    path('api/task08-quizdata/', api.ReadTask08excel.as_view(), name='ReadTask08excel'),
    path('api/task11-lightfixturedata/', api.Task11LightFixtureApi.as_view(), name='Task11LightFixtureApi'),
    path('api/task11-ticketFixesApi/', api.Task11TicketFixesApi.as_view(), name='Task11TicketFixesApi'),
    path('api/task11-lightingScenarioApi/', api.Task11LightingScenarioApi.as_view(), name='Task11LightingScenarioApi'),

    # =========================
    # MISC PAGES
    # =========================
    path('download_windows/', views.download_windows, name='download_windows'),
    path('download-mac/', views.download_mac, name='download_mac'),
    path('feedback/', views.feedback_view, name='feedback'),
    path('about/', views.about, name='about'),
    path('credits/', views.credits, name='credits'),
    path('profile/', views.profile, name='profile'),
]

# =========================
# STATIC / MEDIA (DEV ONLY)
# =========================
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)