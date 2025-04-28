from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from accounts.views import redirect_view,CustomEmailVerificationSentView,UserListView ,dummyfunction,JWTAuthLoginView # or accounts.views if you prefer
from accounts.api import CustomTokenObtainPairView, RegisterView
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('admin/', admin.site.urls),
    path('accounts/confirm-email/', CustomEmailVerificationSentView.as_view(), name='account_email_verification_sent'),
    path('api/auth/login/', JWTAuthLoginView.as_view(), name='api_login'),
    path('accounts/', include('allauth.urls')),
    path('', redirect_view, name='redirect-root'),
    path('home/', TemplateView.as_view(template_name='home.html'), name='home'),
    path('api/users/', UserListView.as_view(), name='user-list'),
    path('api/dummyfunction/', dummyfunction, name='dummyfunction'),
   
]
