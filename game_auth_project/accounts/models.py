import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from .utils import generate_short_id  
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
import json
class CustomUserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, first_name, last_name, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None  # Remove the username field
    id = models.CharField(
        primary_key=True,
        max_length=8,
        unique=True,
        editable=False,
        default=generate_short_id  # 👈 use it here
    )
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    game_version = models.CharField(max_length=20, blank=True, null=True)
    nickname = models.CharField(max_length=30, blank=True, null=True)
    mobile_number = models.CharField(max_length=20, blank=True, null=True)
    date_registered = models.DateTimeField(default=timezone.now)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = CustomUserManager()
    
    def __str__(self):
        return self.email


User = get_user_model()
class UserGameProgress(models.Model):
    COMPLETION_STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('aborted', 'Aborted'),
        ('time_out', 'Time Out'),
        ('within_time', 'Within Time'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    level = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    attempt_number = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    completion_status = models.CharField(max_length=20, choices=COMPLETION_STATUS_CHOICES)
    points_scored = models.PositiveIntegerField(null=True, blank=True)
    time_taken = models.CharField(max_length=20, null=True, blank=True)
    task_number = models.CharField(max_length=20, null=True, blank=True)
    max_points = models.PositiveIntegerField(null=True, blank=True)
    hint_penalty_points = models.PositiveIntegerField(default=0,null=True, blank=True)
    bonus_points = models.PositiveIntegerField(default=0,null=True, blank=True)
    tools_earned = models.JSONField(default=list)
    badges = models.JSONField(default=list)
    super_powers = models.JSONField(default=list)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'level', 'attempt_number','task_number')
        verbose_name_plural = 'User Game Progress'

    def __str__(self):
        return f"{self.user.email} - Level {self.level} Attempt {self.attempt_number}"
    
    # def save(self, *args, **kwargs):
    #     # Ensure JSON fields are properly formatted
    #     if isinstance(self.tools_earned, str):
    #         try:
    #             self.tools_earned = json.loads(self.tools_earned)
    #         except json.JSONDecodeError:
    #             self.tools_earned = []
        
    #     if isinstance(self.badges, str):
    #         try:
    #             self.badges = json.loads(self.badges)
    #         except json.JSONDecodeError:
    #             self.badges = []
                
    #     if isinstance(self.super_powers, str):
    #         try:
    #             self.super_powers = json.loads(self.super_powers)
    #         except json.JSONDecodeError:
    #             self.super_powers = []
                
    #     super().save(*args, **kwargs)