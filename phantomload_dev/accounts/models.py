
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from .utils import generate_short_id  
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.conf import settings
import random
import string



class ActiveSession(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    session_key = models.CharField(max_length=40, unique=True)
    login_time = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} active"

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
   


class WebGLSession(models.Model):

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("closed", "Closed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    session_id = models.CharField(
        max_length=100,
        unique=True
    )

    browser_session_key = models.CharField(
        max_length=100
    )

    started_at = models.DateTimeField(
        auto_now_add=True
    )

    last_ping = models.DateTimeField(
        auto_now=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active"
    )

    is_alive = models.BooleanField(
        default=True
    )

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["status"]),
            models.Index(fields=["last_ping"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.session_id}"
            
def generate_group_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


class CustomUser(AbstractUser):
    username = None

    id = models.CharField(
        primary_key=True,
        max_length=8,
        unique=True,
        editable=False,
        default=generate_short_id
    )

    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    email = models.EmailField(unique=True)

    game_version = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    nickname = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        null=True,
        blank=True
    )

    country = models.CharField(
        max_length=2,
        null=True,
        blank=True
    )

    mobile_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True
    )

    pincode = models.IntegerField(
        null=True,
        blank=True
    )

    # ✅ New Group Relation
    group = models.ForeignKey(
        'Group',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )

    date_registered = models.DateTimeField(
        default=timezone.now
    )

    user_data = models.JSONField(default=list)

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
User = get_user_model()


class LoadShredderRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    place = models.CharField(max_length=255)
    starting_case = models.CharField(max_length=255)
    current_sf_tr = models.FloatField()
    status = models.CharField(max_length=50)  # simple string (no choices)
    score = models.FloatField()
    attempt_number = models.IntegerField()
    actual_attempt_number = models.IntegerField()
    class Meta:
        unique_together = ('user', 'attempt_number')
   
    def __str__(self):
        return f"{self.place} - {self.status}"
    
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
    points_scored = models.IntegerField(null=True, blank=True)
    time_taken = models.CharField(max_length=20, null=True, blank=True)
    task_number = models.CharField(max_length=20, null=True, blank=True)
    max_points = models.PositiveIntegerField(null=True, blank=True)
    hint_penalty_points = models.IntegerField(default=0,null=True, blank=True)
    bonus_points = models.IntegerField(default=0,null=True, blank=True)
    tools_earned = models.JSONField(default=list)
    badges = models.JSONField(default=list)
    super_powers = models.JSONField(default=list)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    

    class Meta:
        unique_together = ('user', 'level', 'attempt_number','task_number')
        verbose_name_plural = 'User Game Progress'

    def __str__(self):
        return f"{self.user.email} - Level {self.level} Attempt {self.attempt_number}"
    

class Leaderboard(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    total_points = models.IntegerField(default=0)
    max_level = models.IntegerField(default=0)
    best_time = models.FloatField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-total_points', 'best_time']
        indexes = [
            models.Index(fields=['-total_points', 'best_time']),
        ]

    def __str__(self):
        return f"{self.user} - {self.total_points}"
    
class Group(models.Model):
    group_id = models.CharField(max_length=10, unique=True, editable=False)
    group_name = models.CharField(max_length=50)
    organisation = models.CharField(max_length=100)
    user_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.group_id:

            unique = False

            while not unique:

                new_id = generate_group_id()

                if not Group.objects.filter(group_id=new_id).exists():
                    self.group_id = new_id
                    unique = True

        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.group_name} ({self.group_id})"