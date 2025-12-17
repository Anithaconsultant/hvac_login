from django.core.mail import send_mail
import smtplib
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
from .models import UserGameProgress, CustomUser, ActiveSession
from django.contrib.auth.decorators import login_required
import os
import json
from django.contrib import messages
from django.conf import settings
from django.db.models import Sum, Max, Min, Q
from django.contrib.auth import login, get_backends
from .forms import CustomUserCreationForm
from allauth.account.views import SignupView, ConfirmEmailView, PasswordChangeView, LoginView, LogoutView
from allauth.account.models import EmailAddress
from django.contrib.sessions.models import Session
from django.conf import settings
from django.dispatch import receiver
from django.utils import timezone

# limit to 10 total logged-in users

from allauth.account.views import LoginView


class LimitedLoginView(LoginView):

    def form_valid(self, form):
        user = form.user

        # 🔒 If user is already authenticated, allow (no slot check)
        if self.request.user.is_authenticated:
            return super().form_valid(form)

        # 🔒 If user already has a reserved slot, allow
        if ActiveSession.objects.filter(user=user).exists():
            return super().form_valid(form)

        # 🔢 Count active users
        active_count = ActiveSession.objects.count()
        print("ACTIVE COUNT:", active_count)

        if active_count >= settings.MAX_CONCURRENT_USERS:
            messages.error(
                self.request,
                "Sorry. We have reached the maximum simultaneous user limit. Please try after some time.",
                extra_tags="limit_error"
            )
            return redirect("account_login")

        # ✅ Allow login
        response = super().form_valid(form)

        # Ensure session exists
        if not self.request.session.session_key:
            self.request.session.create()

        ActiveSession.objects.create(
            user=user,
            session_key=self.request.session.session_key
        )

        return response


# class LimitedLoginView(LoginView):
#     template_name = "account/login.html"

#     def form_valid(self, form):
#         user = form.user  # FIXED

#         # Count active sessions
#         active_count = ActiveSession.objects.filter(
#             logout_time__isnull=True
#         ).count()

#         if active_count >= settings.MAX_CONCURRENT_USERS:
#             form.add_error(None, "Maximum user limit reached. Please try again later.")
#             return super().form_invalid(form)

#         # Create new session
#         ActiveSession.objects.create(
#             user=user,
#             session_key=self.request.session.session_key
#         )

#         return super().form_valid(form)


# class LimitedLogoutView(LogoutView):

#     def dispatch(self, request, *args, **kwargs):
#         ActiveSession.objects.filter(
#             session_key=request.session.session_key,
#             user=request.user,
#             logout_time__isnull=True
#         ).update(logout_time=timezone.now())

#         return super().dispatch(request, *args, **kwargs)

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


@login_required
def view_progress(request):
    progress_data = UserGameProgress.objects.filter(
        user=request.user
    ).order_by('level', 'attempt_number', 'task_number')

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
    # Annotate users with total points, max level, and shortest time taken for tie-breaking
    leaderboard_data = CustomUser.objects.annotate(
        total_points=Sum('usergameprogress__points_scored'),
        max_level=Max('usergameprogress__level'),
        time_taken=Min('usergameprogress__time_taken')  # shortest time
    ).filter(
        # Exclude zero and empty time
        ~Q(total_points=0) & ~Q(time_taken__isnull=True)
    ).order_by('-total_points', 'time_taken')[:10]   # Limit Top 10

    # Get tools, badges, and superpowers for each user
    for user in leaderboard_data:
        progress_data = UserGameProgress.objects.filter(user=user)

        all_tools, all_badges, all_powers = set(), set(), set()

        for progress in progress_data:

            tools = progress.tools_earned.split(',') if isinstance(
                progress.tools_earned, str) else progress.tools_earned or []
            badges = progress.badges.split(',') if isinstance(
                progress.badges, str) else progress.badges or []
            powers = progress.super_powers.split(',') if isinstance(
                progress.super_powers, str) else progress.super_powers or []

            all_tools.update(tool.strip() for tool in tools)
            all_badges.update(badge.strip() for badge in badges)
            all_powers.update(power.strip() for power in powers)

        user.tools_earned = ', '.join(sorted(all_tools)) if all_tools else "-"
        user.tools_earned_list = sorted(all_tools) if all_tools else []

        user.badges = ', '.join(sorted(all_badges)) if all_badges else "-"
        user.badges_list = sorted(all_badges) if all_badges else []

        user.super_powers = ', '.join(
            sorted(all_powers)) if all_powers else "-"
        user.super_powers_list = sorted(all_powers) if all_powers else []

    return render(request, 'leaderboard.html', {'leaderboard_data': leaderboard_data})


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
    return render(request, 'profile.html')


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
