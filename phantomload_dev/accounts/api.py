from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAuthenticated
from django.contrib.auth import get_user_model,authenticate
from .models import UserGameProgress
from django.template.response import TemplateResponse
from .serializers import CustomTokenObtainPairSerializer, RegisterSerializer,GameProgressSerializer
import pandas as pd
import os
import csv
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
import logging
User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({
                "status": "error",
                "message": "Invalid credentials"
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        user = serializer.user
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "status": "success",
            "user": {
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            },
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }
        })

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "message": "User created successfully. Please check your email for verification."
        }, status=status.HTTP_201_CREATED)

logger = logging.getLogger(__name__)

class GameProgressAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Add user to request data
            request.data['user'] = request.user.id
            serializer = GameProgressSerializer(data=request.data)
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": "success",
                    "message": "Game progress saved successfully",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
                
            return Response({
                "status": "error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Error saving game progress: {str(e)}")
            return Response({
                "status": "error",
                "message": "Internal server error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ClientLoginView(APIView):
    """
    Custom login view for client authentication.
    """

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return Response({'detail': 'User not registered.'}, status=status.HTTP_404_NOT_FOUND)

        user = authenticate(request, email=username, password=password)

        if user is not None:
            if user.is_active:
                # Generate tokens manually
                refresh = RefreshToken.for_user(user)
                return Response({
                    'status': 'success',
                    'user_id': user.id,
                    'email': user.email,
                    'username':user.nickname,
                    'tokens': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh)
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'User account is disabled.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'detail': 'Invalid password.'}, status=status.HTTP_401_UNAUTHORIZED)
        # if user is not None and user.is_active:
        #     refresh = RefreshToken.for_user(user)
        #     token_data = {
        #         'status': 'success',
        #         'user_id': user.id,
        #         'email': user.email,
        #         'username': user.nickname,
        #         'tokens': {
        #             'access': str(refresh.access_token),
        #             'refresh': str(refresh)
        #         }
        #     }
        #     return TemplateResponse(request, 'home.html', token_data)
        # elif user is not None and not user.is_active:
        #     return Response({'detail': 'User account is disabled.'}, status=status.HTTP_403_FORBIDDEN)
        # else:
        #     return Response({'detail': 'Invalid password.'}, status=status.HTTP_401_UNAUTHORIZED)


        

class UserDataView(APIView):
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            return Response({
                'user_id': user.id,
                'email': user.email,
                'username': user.username,
                'user_data': user.user_data,
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            user_data = request.data.get('user_data')
            if user_data is None:
                return Response({'detail': 'user_data is required.'}, status=status.HTTP_400_BAD_REQUEST)

            user.user_data = user_data
            user.save()

            return Response({'detail': 'User data updated successfully.'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        
class ReadExcelStaticView(APIView):
    """
    Reads a CSV file from staticfiles/docs and returns only columns H, J, K, L, M, N, and O as JSON.
        """

   
    def get(self, request):
        filename = request.query_params.get('filename')
        if not filename:
            return Response({'error': 'Filename parameter is required.'}, status=400)

        if '/' in filename or '\\' in filename:
            return Response({'error': 'Invalid filename.'}, status=400)

        csv_path = os.path.join(settings.BASE_DIR, 'staticfiles/docs', filename)

        if not os.path.exists(csv_path):
            return Response({'filename': filename, 'path': csv_path, 'error': 'File not found.'}, status=404)

        try:
            required_headers = [
               'HotSpotID',
                'Power',
                'No_of_hours',
                'Standby_power',
                'Standby_hours',
                'Quanitity_of_fixtures',
                'Diversity_Factor',
                'ActiveZone'
            ]

            data = []
            encodings_to_try = ['utf-8-sig', 'utf-16', 'latin1']

            for enc in encodings_to_try:
                try:
                    with open(csv_path, newline='', encoding=enc) as csvfile:
                        reader = csv.DictReader(csvfile)

                        # Check for missing columns
                        missing = [h for h in required_headers if h not in reader.fieldnames]
                        if missing:
                            return Response({'error': f'Missing columns: {", ".join(missing)}'}, status=400)

                        for row in reader:
                            filtered = {h: row[h] for h in required_headers}
                            data.append(filtered)

                    # If we reached here, reading succeeded
                    break

                except UnicodeDecodeError:
                    data = []
                    continue

            if not data:
                return Response({'error': 'Unable to read CSV with supported encodings.'}, status=500)

            return Response(data)

        except Exception as e:
            return Response({'error': str(e)}, status=500)