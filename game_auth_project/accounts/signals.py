from django.db.models.signals import post_save,post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserGameProgress,ActiveSession,Leaderboard
#from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.signals import user_logged_out

@receiver(user_logged_out)
def clear_active_session(sender, request, user, **kwargs):
    if user:  # ✅ avoid None issues
        ActiveSession.objects.filter(user=user).delete()
    
    
    
User = get_user_model()
@receiver(post_save, sender=User)
def create_user_related_data(sender, instance, created, **kwargs):
    if created:
        # ✅ Create leaderboard row
        Leaderboard.objects.create(user=instance)

        # ✅ Your existing progress creation (UNCHANGED)
        for level in range(1, 3):
            for attempt in range(1, 4):  # ✅ FIXED (was 1–5 earlier)
                for task in range(1, 11):
                    UserGameProgress.objects.create(
                        user=instance,
                        level=level,
                        attempt_number=attempt,
                        task_number=str(task),
                        completion_status='not_started',
                    )

        for attempt in range(1, 4):
            UserGameProgress.objects.create(
                user=instance,
                level=1,
                attempt_number=attempt,
                task_number="Load_Shredder",
                completion_status='not_started',
            )
            
from django.db.models import Sum, Max, Min

@receiver(post_save, sender=UserGameProgress)
def update_leaderboard(sender, instance, **kwargs):
    leaderboard, _ = Leaderboard.objects.get_or_create(user=instance.user)

    # ✅ SAFE recalculation (no double counting)
    agg = UserGameProgress.objects.filter(user=instance.user).aggregate(
        total_points=Sum('points_scored'),
        max_level=Max('level'),
        best_time=Min('time_taken')
    )

    leaderboard.total_points = agg['total_points'] or 0
    leaderboard.max_level = agg['max_level'] or 0
    leaderboard.best_time = agg['best_time']

    leaderboard.save()
    
@receiver(post_save, sender=User)
def update_group_user_count(sender, instance, created, **kwargs):
    if created and instance.group:
        group = instance.group
        group.user_count =group.users.count()
        group.save()

@receiver(post_delete, sender=User)
def decrease_group_user_count(sender, instance, **kwargs):
    if instance.group:
        group = instance.group
        group.user_count -= 1
        group.save()