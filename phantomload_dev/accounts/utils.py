
import string
import random
from django.conf import settings

def generate_short_id(length=8):
    characters = string.ascii_letters + string.digits  # a-zA-Z0-9
    return ''.join(random.choices(characters, k=length))


def can_user_login(user):
    from .models import ActiveSession  # ✅ IMPORT INSIDE FUNCTION

    # If already logged in → allow
    if ActiveSession.objects.filter(user=user).exists():
        return True, None

    active_count = ActiveSession.objects.count()

    if active_count >= settings.MAX_CONCURRENT_USERS:
        return False, "Maximum users reached"

    return True, None