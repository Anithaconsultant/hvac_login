
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

    return True, None

ACTIVE_TIMEOUT_SECONDS = 60*5
    

def cleanup_dead_sessions():
    from accounts.models import WebGLSession
    timeout = timezone.now() - timedelta(seconds=ACTIVE_TIMEOUT_SECONDS)

    expired_sessions = WebGLSession.objects.filter(
        last_ping__lt=timeout,
        status="active",
        is_alive=True
    )

    for s in expired_sessions:
        print(
            f"EXPIRING: session={s.session_id} "
            f"user={s.user.email} "
            f"last_ping={s.last_ping} "
            f"now={timezone.now()}"
        )

    expired_sessions.update(
        status="inactive",
        is_alive=False
    )


def has_active_webgl_session(user):
    from accounts.models import WebGLSession
    """Check if the user already has an active WebGL session."""
    cleanup_dead_sessions()
    timeout = timezone.now() - timedelta(seconds=ACTIVE_TIMEOUT_SECONDS)
    return WebGLSession.objects.filter(
        user=user,
        status="active",
        last_ping__gte=timeout,
        is_alive=True
    ).exists()
