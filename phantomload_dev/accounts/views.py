from django.db.models.functions import Cast
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from allauth.account.views import SignupView
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.http import JsonResponse, Http404, FileResponse, HttpResponse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from .forms import FeedbackForm, CustomUserCreationForm
from .models import UserGameProgress, CustomUser, ActiveSession,UserGameProgress, LoadShredderRecord,Leaderboard
from django.contrib.auth.decorators import login_required
from rest_framework_simplejwt.tokens import AccessToken
from django.db.models import Case, When, Value, IntegerField
import os
import json
from django.contrib import messages
from django.conf import settings
from django.db.models import Sum, Max, Min, Q
from django.contrib.auth import login, get_backends,logout,get_user_model
from .forms import CustomUserCreationForm
from allauth.account.views import SignupView, ConfirmEmailView, PasswordChangeView, LoginView, LogoutView
from allauth.account.models import EmailAddress
from django.conf import settings
from django.dispatch import receiver
from django.utils import timezone
from .utils import can_user_login
from rest_framework.decorators import api_view
from rest_framework.response import Response

User = get_user_model()

class LimitedLoginView(LoginView):

    def form_valid(self, form):
        user = form.user

        # ✅ STEP 4.1: Check limit
        allowed, error = can_user_login(user)

        if not allowed:
            messages.error(
                self.request,
                "Maximum users reached. Try later.",
                extra_tags="limit_error"
            )
            return redirect("account_login")

        # ✅ STEP 4.2: Login normally
        response = super().form_valid(form)

        # ✅ STEP 4.3: Ensure session exists
        if not self.request.session.session_key:
            self.request.session.create()

        # ✅ STEP 4.4: Store session (IMPORTANT)
        ActiveSession.objects.update_or_create(
            user=user,
            defaults={
                "session_key": self.request.session.session_key
            }
        )

        return response


@login_required
def unity_game_view(request):

    user = request.user

    token = str(AccessToken.for_user(user))

    return render(
        request,
        "unity_game.html",
        {
            "jwt_token": token,
            "username": user.nickname,
            "user_id": str(user.id),
            "user_email": user.email,
            "user_gender": user.gender,
        }
    )
from uuid import uuid4
@login_required
def play_task(request, task_name):

    existing_session = ActiveSession.objects.filter(
        user=request.user,
        task_name=task_name,
        is_active=True
    ).exists()

    if existing_session:

        return render(
            request,
            "task_already_open.html",
            {
                "task_name": task_name
            }
        )

    session_id = str(uuid4())

    ActiveSession.objects.create(
        user=request.user,
        session_key=request.session.session_key,
        task_name=task_name,
        session_id=session_id,
        is_active=True,
        last_heartbeat=timezone.now()
    )

    token = str(
        AccessToken.for_user(
            request.user
        )
    )

    return render(
        request,
        "play_task.html",
        {
            "task_name": task_name,

            "session_id": session_id,

            "jwt_token": token,
            "username": request.user.nickname,
            "user_id": request.user.id,
            "user_email": request.user.email,
            "user_gender": request.user.gender,
        }
    )
def custom_logout(request):

    if request.user.is_authenticated:

        ActiveSession.objects.filter(
            user=request.user
        ).delete()

    logout(request)

    return redirect('account_login')


class CustomPasswordChangeView(PasswordChangeView):
    def form_valid(self, form):
        # Clear previous messages so login/logout messages are removed
        storage = messages.get_messages(self.request)
        storage.used = True

        messages.success(
            self.request, "Your password has been successfully updated.")
        return super().form_valid(form)


class CustomConfirmEmailView(ConfirmEmailView):

    def login_user(self, request, user):
        """Logs in user safely when multiple backends exist."""
        if not getattr(user, "backend", None):
            backend = get_backends()[0]
            user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
        login(request, user)

    def get(self, request, *args, **kwargs):
        """Handles GET requests including 'try again in browser'."""
        try:
            confirmation = self.get_object()
        except Exception:
            # Already verified → safe redirect
            if request.user.is_authenticated:
                return redirect("home")
            # or a custom "already verified page"
            return redirect("account_login")

        # If email already verified
        if confirmation.email_address.verified:
            if request.user.is_authenticated:
                return redirect("home")
            else:
                # log user in & redirect
                self.login_user(request, confirmation.email_address.user)
                return redirect("home")

        # Not yet verified → normal flow
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Handles POST confirmation."""
        response = super().post(request, *args, **kwargs)

        if request.user.is_authenticated:
            self.login_user(request, request.user)

        return redirect("home")


class CustomSignupView(SignupView):
    form_class = CustomUserCreationForm  # your custom signup form

    def form_valid(self, form):
        # Create the user but don't log them in
        response = super().form_valid(form)
        user = self.user

        # Send verification email using new API
        EmailAddress.objects.add_email(
            self.request,
            user,
            user.email,
            confirm=True  # triggers the confirmation email
        )

        # Redirect to verification-sent page
        return redirect('account_email_verification_sent')


def home_redirect(request):
    """Redirect root URL to appropriate location"""
    if request.user.is_authenticated:
        return redirect('home')  # Goes to the actual home view
    return redirect('account_login')  # Goes to allauth login


@login_required
def home_view(request):
    if not request.user.is_authenticated:
        return redirect('account_login')

    return render(request, 'home.html')


class CustomEmailVerificationSentView(TemplateView):
    template_name = "account/confirm_email.html"


class UserListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = CustomUser.objects.all()
        serializer = CustomUserSerializer(users, many=True)
        return Response(serializer.data)


def confirm_payment(request):
    return JsonResponse({'message': 'Payment confirmed. Seat booked successfully'})


@login_required
def download_windows(request):
    user = request.user
    # Update user record: for example
    user.game_version = 'GameVersion1.0'  # 👈 real version
    user.save()

    filepath = os.path.join(settings.MEDIA_ROOT, 'downloads',
                            'game_windows.exe')  # 👈 real file path
    if not os.path.exists(filepath):
        raise Http404("File not found.")

    return FileResponse(open(filepath, 'rb'), as_attachment=True, filename='game_windows.exe')


@login_required
def download_mac(request):
    user = request.user
    # Update user record: for example
    user.game_version = 'GameVersion1.0'  # 👈 real version
    user.save()
    filepath = os.path.join(settings.MEDIA_ROOT, 'downloads',
                            'game_windows.exe')  # 👈 real file path
    if not os.path.exists(filepath):
        raise Http404("File not found.")

    return FileResponse(open(filepath, 'rb'), as_attachment=True, filename='game_windows.exe')


@csrf_exempt
# @login_required
def update_game_progress(request):
    if request.method == 'POST':

        try:
            # Find existing record to update
            data = json.loads(request.body)
            print("Data received:", data)  # Debugging line
            # Get the user from the request data (instead of request.user)
            user_id = data.get('user_id')  # 👈 Expecting user_id in JSON
            if not user_id:
                return JsonResponse(
                    {'status': 'error', 'message': 'user_id is required'},
                    status=400
                )

            try:
                user = CustomUser.objects.get(pk=data['user_id'])
            except CustomUser.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid user_id'
                }, status=400)
            progress = UserGameProgress.objects.get(
                user=user,
                level=data.get('level'),
                attempt_number=data.get('attempt_number'),
                task_number=data.get('task_number')
            )

            # Update only the editable fields
            progress.completion_status = data.get('completion_status')
            progress.user_id = data.get('user_id')
            progress.points_scored = data.get('points_scored')
            progress.time_taken = data.get('time_taken')
            progress.max_points = data.get('max_points')
            progress.hint_penalty_points = data.get('hint_penalty_points')
            progress.bonus_points = data.get('bonus_points')
            progress.tools_earned = data.get('tools_earned')
            progress.badges = data.get('badges')
            progress.super_powers = data.get('super_powers')
            progress.save()
            return JsonResponse({'status': 'success', 'message': 'Progress updated successfully'})

        except UserGameProgress.DoesNotExist:
            # Handle case where record doesn't exist
            return JsonResponse(
                {'status': 'error', 'message': 'No matching progress record found'},
                status=404)
        except json.JSONDecodeError:
            return JsonResponse(
                {'status': 'error', 'message': 'Invalid JSON data'},
                status=400)
        except Exception as e:
            return JsonResponse(
                {'status': 'error', 'message': str(e)},
                status=500)

    elif request.method == 'GET':
        # Return first available record as JSON
        existing_record = UserGameProgress.objects.filter(
            user=request.user
        ).order_by('level', 'attempt_number', 'task_number').first()

        if existing_record:
            record_data = {
                'level': existing_record.level,
                'attempt_number': existing_record.attempt_number,
                'task_number': existing_record.task_number,
                'completion_status': existing_record.completion_status,
                'points_scored': existing_record.points_scored,
                'time_taken': existing_record.time_taken,
                'max_points': existing_record.max_points,
                'hint_penalty_points': existing_record.hint_penalty_points,
                'bonus_points': existing_record.bonus_points,
                'tools_earned': existing_record.tools_earned,
                'badges': existing_record.badges,
                'super_powers': existing_record.super_powers,
            }
            return JsonResponse({'status': 'success', 'data': record_data})
        else:
            return JsonResponse(
                {'status': 'error', 'message': 'No progress records available'},
                status=404
            )

    return JsonResponse(
        {'status': 'error', 'message': 'Method not allowed'},
        status=405
    )





@csrf_exempt
def reset_game_progress(request):
    if request.method == 'POST':
        try:
            user_id = request.GET.get('user_id')
            if not user_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'user_id is required'
                }, status=400)

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'User not found'
                }, status=404)

            # =========================
            # ✅ RESET UserGameProgress
            # =========================
            progress_updated = UserGameProgress.objects.filter(user=user).update(
                completion_status='not_started',
                points_scored=None,
                time_taken=None,
                max_points=None,
                hint_penalty_points=0,
                bonus_points=0,
                tools_earned=[],
                badges=[],
                super_powers=[]
            )

            # =========================
            # ✅ RESET LoadShredderRecord
            # =========================
            shredder_records = LoadShredderRecord.objects.filter(user=user).order_by('attempt_number')

            actual_counter = 1

            for record in shredder_records:
                record.score = 0
                record.status = 'not_started'
                record.place = ""
                record.starting_case = ""
                record.current_sf_tr = 0

                # 🔁 reset attempt rotation properly
                record.actual_attempt_number = actual_counter
                record.attempt_number = ((actual_counter - 1) % 3) + 1

                record.save()
                actual_counter += 1

            return JsonResponse({
                'status': 'success',
                'message': 'Game + Load Shredder reset successfully',
                'progress_updated': progress_updated,
                'shredder_records_reset': shredder_records.count()
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

    return JsonResponse({
        'status': 'error',
        'message': 'Only POST allowed'
    }, status=405)

@login_required
def view_progress(request):
    progress_data = UserGameProgress.objects.filter(
        user=request.user
    ).annotate(
        priority=Case(
            When(task_number__iexact='Load_Shredder', then=Value(0)),
            default=Value(1),
            output_field=IntegerField()
        ),
        task_int=Cast('task_number', IntegerField())
    ).order_by('priority', 'task_int', 'attempt_number')
    for progress in progress_data:
        # Split and clean tools_earned
        tools = (
            progress.tools_earned.split(',') if isinstance(progress.tools_earned, str)
            else progress.tools_earned or []
        )
        progress.tools_earned_list = [tool.strip()
                                    for tool in tools if tool.strip()]

        # Split and clean badges
        badges = (
            progress.badges.split(',') if isinstance(progress.badges, str)
            else progress.badges or []
        )
        progress.badges_list = [badge.strip()
                                for badge in badges if badge.strip()]

        # Split and clean super_powers
        powers = (
            progress.super_powers.split(',') if isinstance(progress.super_powers, str)
            else progress.super_powers or []
        )
        progress.super_powers_list = [power.strip()
                                    for power in powers if power.strip()]
    
    return render(request, 'progress_data.html', {'progress_data': progress_data})

@login_required
def leaderboard(request):

    # ✅ Step 1: Get top 10 from Leaderboard table (FAST)
    leaderboard_qs = Leaderboard.objects.select_related('user')\
        .filter(total_points__gt=0, best_time__isnull=False)[:10]

    user_ids = [l.user_id for l in leaderboard_qs]

    # ✅ Step 2: Fetch all progress in ONE query
    all_progress = UserGameProgress.objects.filter(user__in=user_ids)

    progress_map = {}
    for p in all_progress:
        progress_map.setdefault(p.user_id, []).append(p)

    # ✅ Step 3: Attach tools, badges, powers (your logic)
    leaderboard_data = []

    for entry in leaderboard_qs:
        user = entry.user

        user.total_points = entry.total_points
        user.max_level = entry.max_level
        user.time_taken = int(entry.best_time)

        progress_data = progress_map.get(user.id, [])

        all_tools, all_badges, all_powers = set(), set(), set()

        for progress in progress_data:
            tools = progress.tools_earned.split(',') if isinstance(
                progress.tools_earned, str) else progress.tools_earned or []
            badges = progress.badges.split(',') if isinstance(
                progress.badges, str) else progress.badges or []
            powers = progress.super_powers.split(',') if isinstance(
                progress.super_powers, str) else progress.super_powers or []

            all_tools.update(t.strip() for t in tools if t.strip())
            all_badges.update(b.strip() for b in badges if b.strip())
            all_powers.update(p.strip() for p in powers if p.strip())

        user.tools_earned = ', '.join(sorted(all_tools)) if all_tools else "-"
        user.tools_earned_list = sorted(all_tools)

        user.badges = ', '.join(sorted(all_badges)) if all_badges else "-"
        user.badges_list = sorted(all_badges)

        user.super_powers = ', '.join(sorted(all_powers)) if all_powers else "-"
        user.super_powers_list = sorted(all_powers)

        leaderboard_data.append(user)

    return render(request, 'leaderboard.html', {
        'leaderboard_data': leaderboard_data
    })

def about(request):
    return render(request, 'about.html')


@login_required
def feedback_view(request):
    feedback_sent = False
    print(request.user.email)

    if request.method == "POST":
        form = FeedbackForm(request.POST)
        print("Form data:", request.POST)

        if form.is_valid():
            feedback_text = form.cleaned_data["feedback"]
            user_email = request.user.email if request.user.is_authenticated else "Anonymous"

            subject = f" New Feedback - Phantom Load"

            message = f"""
-----------------------------------------------------------
USER FEEDBACK
-----------------------------------------------------------

Feedback Message:
{feedback_text}

----------------------------------------------------------
Submitted By:
Email: {user_email}
Time: {timezone.now().strftime('%d %B %Y, %I:%M %p')}
"""

            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    ["support@phantom-load.in"],
                    fail_silently=False,
                )

                feedback_sent = True
                form = FeedbackForm()  # Clear textarea after success

            except Exception as e:
                print("Email Error:", e)
                messages.error(
                    request, "⚠ Something went wrong. Could not send the feedback email.")

        else:
            print("Form validation failed:", form.errors)
            messages.error(request, "Please correct the errors.")

    else:
        form = FeedbackForm()

    return render(request, "feedback.html", {
        "form": form,
        "feedback_sent": feedback_sent,
    })


def credits(request):
    return render(request, 'credits.html')


@login_required
def profile(request):
    user = request.user

    group = user.group

    context = {
        'group': group,
        'group_id': group.group_id if group else None,
        'group_name': group.group_name if group else None,
        'organisation': group.organisation if group else None,
    }

    return render(request, 'profile.html', context)


def test_email(request):
    try:
        send_mail(
            "Test Subject",
            "Test body",
            settings.DEFAULT_FROM_EMAIL,
            ["support@phantom-load.in"],
            fail_silently=False,
        )
        return HttpResponse("SUCCESS: Email sent")
    except Exception as e:
        return HttpResponse(f"FAILED: {repr(e)}")
# views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Group

@api_view(['GET'])
def get_group_by_id(request):
    group_id = request.GET.get('group_id')

    try:
        group = Group.objects.get(group_id=group_id)
        return Response({
            "valid": True,
            "group_name": group.group_name
        })
    except Group.DoesNotExist:
        return Response({
            "valid": False,
            "group_name": None
        })