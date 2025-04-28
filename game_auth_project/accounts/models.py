import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    max_points = models.PositiveIntegerField(null=True, blank=True)
    hint_penalty_points = models.PositiveIntegerField(default=0)
    bonus_points = models.PositiveIntegerField(default=0)
    tools_earned = models.JSONField(default=list)
    badges = models.JSONField(default=list)
    super_powers = models.JSONField(default=list)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'level', 'attempt_number')
        verbose_name_plural = 'User Game Progress'

    def __str__(self):
        return f"{self.user.email} - Level {self.level} Attempt {self.attempt_number}"