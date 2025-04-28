from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from allauth.account.views import EmailVerificationSentView
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.utils import timezone  
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
import django 
from rest_framework.decorators import api_view
def redirect_view(request):
    if request.user.is_authenticated:
        return redirect('home')  # go to home page
    else:
        return redirect('account_login')  # go to login page

class CustomEmailVerificationSentView(TemplateView):
    template_name = "account/confirm_email.html"  
    


class UserListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = CustomUser.objects.all()
        serializer = CustomUserSerializer(users, many=True)
        return Response(serializer.data)


def confirm_payment(request):
    return JsonResponse({'message': 'Payment confirmed. Seat booked successfully'})

@api_view(['GET', 'POST'])
def dummyfunction(request):
    if request.method == 'GET':
        return JsonResponse({'message': 'Payment confirmed. Seat booked successfully'})