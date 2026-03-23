from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserGameProgress
#from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.signals import user_logged_out
from .models import ActiveSession

@receiver(user_logged_out)
def clear_active_session(sender, request, user, **kwargs):
    if user:  # ✅ avoid None issues
        ActiveSession.objects.filter(user=user).delete()
    
    
    
User = get_user_model()

@receiver(post_save, sender=User)
def create_user_game_progress(sender, instance, created, **kwargs):
    if created:
        # Create records for only 2 levels (1-2), 3 attempts each, and 10 tasks per attempt
        for level in range(1, 3):  # Only levels 1 and 2
            for attempt in range(1, 4):  # 3 attempts (1-3)
                for task in range(1, 11):  # 10 tasks (1-10)
                    UserGameProgress.objects.create(
                        user=instance,
                        level=level,
                        attempt_number=attempt,
                        task_number=str(task),  # Stored as string (CharField)
                        completion_status='not_started',
                        # Other fields will use their defaults (null/blank/default values)
                    )