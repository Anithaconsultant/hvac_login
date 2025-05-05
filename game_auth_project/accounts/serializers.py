from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import CustomUser,UserGameProgress

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        return token

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'nickname', 'password')
    
    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            nickname=validated_data.get('nickname', ''),
            password=validated_data['password']
        )
        return user


class GameProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGameProgress
        fields = '__all__'
    
    def validate(self, data):
        # Custom validation can be added here
        if data.get('points_scored', 0) > data.get('max_points', 0):
            raise serializers.ValidationError("Points scored cannot exceed max points")
        return data