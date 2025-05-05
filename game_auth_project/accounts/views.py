from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from allauth.account.views import EmailVerificationSentView
from django.views.generic import TemplateView
from django.http import JsonResponse,Http404,FileResponse
from django.utils import timezone  
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from .serializers import GameProgressSerializer
from .models import UserGameProgress,CustomUser
from django.contrib.auth.decorators import login_required
import django 
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import JSONParser
import os
from django.conf import settings
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


@login_required
def download_windows(request):
    user = request.user
    # Update user record: for example
    user.game_version = 'GameVersion1.0'  # 👈 real version
    user.save()

    filepath = os.path.join(settings.MEDIA_ROOT, 'downloads', 'game_windows.exe')  # 👈 real file path
    if not os.path.exists(filepath):
        raise Http404("File not found.")

    return FileResponse(open(filepath, 'rb'), as_attachment=True, filename='game_windows.exe')


@login_required
def download_mac(request):
    user = request.user
    # Update user record: for example
    user.game_version = 'GameVersion1.0'  # 👈 real version
    user.save()
    filepath = os.path.join(settings.MEDIA_ROOT, 'downloads', 'game_windows.exe')  # 👈 real file path
    if not os.path.exists(filepath):
        raise Http404("File not found.")

    return FileResponse(open(filepath, 'rb'), as_attachment=True, filename='game_windows.exe')

@login_required
@api_view(['GET', 'POST', 'PUT'])
def updateUserBoard(request, userID):
    if request.method == 'POST':
        bonus_points = int(request.POST['bonus_points'])
        tools = request.POST['tools_earned'].split(',')
        badges = request.POST['badges'].split(',')
        powers = request.POST['super_powers'].split(',')

        UserGameProgress.objects.create(
            user=request.user,
            bonus_points=bonus_points,
            tools_earned=[tool.strip() for tool in tools],
            badges=[badge.strip() for badge in badges],
            super_powers=[power.strip() for power in powers]
        )
        return JsonResponse({"message": "User progress created."}, status=status.HTTP_201_CREATED)

    if request.method == 'PUT':
        data = request.data.copy()
        progress = UserGameProgress.objects.filter(user_id=userID).first()

        # Handle if record does NOT exist —> create new
        if not progress:
            # Extract and clean list fields if present
            tools = data.get('tools_earned', [])
            badges = data.get('badges', [])
            powers = data.get('super_powers', [])

            # Ensure list fields are lists
            if isinstance(tools, str):
                tools = [tools]
            if isinstance(badges, str):
                badges = [badges]
            if isinstance(powers, str):
                powers = [powers]

            # Ensure all fields needed are there
            new_record_data = {
                "user": get_object_or_404(CustomUser, pk=userID),
                "tools_earned": tools,
                "badges": badges,
                "super_powers": powers
            }

            # Add other scalar fields from data
            for field in ['level', 'attempt_number', 'completion_status', 'points_scored', 'max_points', 'hint_penalty_points', 'bonus_points']:
                if field in data:
                    new_record_data[field] = data[field]

            serializer = GameProgressSerializer(data=new_record_data)
            if serializer.is_valid():
                serializer.save()
                return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        getcity = UserGameProgress.objects.filter(user_id=userID)
        serializer = GameProgressSerializer(getcity, many=True)
        return JsonResponse(serializer.data, safe=False)
    else:
        
         return JsonResponse({'error': 'Method not allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

