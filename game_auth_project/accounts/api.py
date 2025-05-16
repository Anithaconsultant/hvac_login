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
from .serializers import CustomTokenObtainPairSerializer, RegisterSerializer,GameProgressSerializer
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
                }, status=status.HTTP_200_OK)
            else:
                return Response({'detail': 'User account is disabled.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'detail': 'Invalid password.'}, status=status.HTTP_401_UNAUTHORIZED)