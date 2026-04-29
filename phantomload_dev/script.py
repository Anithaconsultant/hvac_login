from django.contrib.auth import get_user_model
from django.db.models import Sum, Max
from accounts.models import UserGameProgress, Leaderboard

User = get_user_model()

for user in User.objects.all():
    progress_qs = UserGameProgress.objects.filter(user=user)

    total_points = progress_qs.aggregate(Sum('points_scored'))['points_scored__sum'] or 0
    max_level = progress_qs.aggregate(Max('level'))['level__max'] or 0

    # ✅ FIX: Convert time properly
    times = []
    for p in progress_qs:
        if p.time_taken:
            try:
                # remove 's' and convert
                t = str(p.time_taken).replace('s', '').strip()
                times.append(float(t))
            except:
                pass

    best_time = min(times) if times else None

    Leaderboard.objects.update_or_create(
        user=user,
        defaults={
            'total_points': total_points,
            'max_level': max_level,
            'best_time': best_time
        }
    )

print("✅ FIXED: Leaderboard backfill completed")