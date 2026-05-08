
import string
import random
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

def generate_short_id(length=8):
    characters = string.ascii_letters + string.digits  # a-zA-Z0-9
    return ''.join(random.choices(characters, k=length))


def can_user_login(user):
    from .models import ActiveSession

    timeout = timezone.now() - timedelta(minutes=60)

    ActiveSession.objects.filter(
        last_seen__lt=timeout
    ).delete()

    # ✅ STEP 2: If already logged in → allow
    if ActiveSession.objects.filter(user=user).exists():
        return True, None

    # ✅ STEP 3: Count active users
    active_count = ActiveSession.objects.count()

    # ✅ STEP 4: Check max limit
    if active_count >= settings.MAX_CONCURRENT_USERS:
        return False, "Maximum users reached"

    return True, None