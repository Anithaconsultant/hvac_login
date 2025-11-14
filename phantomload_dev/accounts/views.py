from django.core.mail import send_mail
import smtplib
import logging              
from django.shortcuts import redirect, render
from django.views import View
from django.contrib.auth.decorators import login_required
from allauth.account.views import EmailVerificationSentView, LoginView, SignupView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.http import JsonResponse, Http404, FileResponse
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from .serializers import GameProgressSerializer
from .forms import UserGameProgressForm, FeedbackForm
from .models import UserGameProgress, CustomUser
from django.contrib.auth.decorators import login_required
import django
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import JSONParser
import os
import json
from django.contrib import messages
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Sum, Min
from django.contrib.auth import login as auth_login
from .forms import CustomUserCreationForm
from django.urls import reverse
from allauth.account.views import SignupView
from allauth.account.models import EmailAddress
from allauth.account.views import ConfirmEmailView                                                  


class CustomConfirmEmailView(ConfirmEmailView):
    def post(self, *args, **kwargs):
        response = super().post(*args, **kwargs)
        if self.request.user.is_authenticated:
            login(self.request, self.request.user)
        return redirect('home')

    def get(self, *args, **kwargs):
        response = super().get(*args, **kwargs)
        if self.request.user.is_authenticated:
            login(self.request, self.request.user)
            return redirect('home')
        return response


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
        progress.tools_earned_list = [tool.strip() for tool in tools if tool.strip()]

        # Split and clean badges
        badges = (
            progress.badges.split(',') if isinstance(progress.badges, str)
            else progress.badges or []
        )
        progress.badges_list = [badge.strip() for badge in badges if badge.strip()]

        # Split and clean super_powers
        powers = (
            progress.super_powers.split(',') if isinstance(progress.super_powers, str)
            else progress.super_powers or []
        )
        progress.super_powers_list = [power.strip() for power in powers if power.strip()]

    return render(request, 'progress_data.html', {'progress_data': progress_data})
@login_required
def leaderboard(request):
    # Calculate net points for each user (sum of all points_scored)
    leaderboard_data = CustomUser.objects.annotate(
        total_points=Sum('usergameprogress__points_scored'),
        max_level=Max('usergameprogress__level'),
        time_taken=Max('usergameprogress__time_taken')
    ).order_by('-total_points', 'time_taken')

    # Get tools, badges, and super_powers for each user
    for user in leaderboard_data:
        progress_data = UserGameProgress.objects.filter(user=user)
        
        # Initialize sets to avoid duplicates
        all_tools = set()
        all_badges = set()
        all_powers = set()

        for progress in progress_data:
            # Process tools_earned (split if string, else treat as list)
            tools = (
                progress.tools_earned.split(',')
                if isinstance(progress.tools_earned, str)
                else progress.tools_earned or []  # Handle None/empty
            )
            all_tools.update(tool.strip() for tool in tools)

            # Process badges (split if string, else treat as list)
            badges = (
                progress.badges.split(',')
                if isinstance(progress.badges, str)
                else progress.badges or []
            )
            all_badges.update(badge.strip() for badge in badges)

            # Process super_powers (split if string, else treat as list)
            powers = (
                progress.super_powers.split(',')
                if isinstance(progress.super_powers, str)
                else progress.super_powers or []
            )
            all_powers.update(power.strip() for power in powers)

        # Assign formatted strings (or "-" if empty)
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



def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.cleaned_data['feedback']
            user_email = form.cleaned_data['email']

            print(f"=== FEEDBACK SUBMISSION ===")
            print(f"Feedback: {feedback}")
            print(f"User email: {user_email}")

            # Create email content
            subject = "New Feedback - Phantom Load Application"
            message = f"""
New feedback has been submitted through the Phantom Load application:

FEEDBACK:
{feedback}

SUBMITTED BY:
- User: {request.user.email if request.user.is_authenticated else 'Anonymous'}
- Email: {user_email}
- Timestamp: {timezone.now()}

Please review this feedback and take appropriate action.
"""

            try:
           
                result = send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=['support@phantom-load.in'],
                    fail_silently=False,
                )

                print(f"=== EMAIL SEND RESULT: {result} ===")

                if result == 1:
                    messages.success(
                        request, 'Thank you for your feedback! Your message has been sent successfully.')
                    print("✅ Feedback email sent successfully")
                else:
                    messages.error(
                        request, 'Failed to send feedback. Please try again.')
                    print("❌ Feedback email failed")

                return redirect('feedback')

            except smtplib.SMTPAuthenticationError as e:
                error_msg = "Email authentication failed. Please check the email configuration."
                print(f"❌ SMTP Authentication Error: {e}")
                messages.error(request, error_msg)
            except smtplib.SMTPException as e:
                error_msg = "Email service error. Please try again later."
                print(f"❌ SMTP Error: {e}")
                messages.error(request, error_msg)
            except Exception as e:
                error_msg = f"Error sending feedback: {str(e)}"
                print(f"❌ General Error: {e}")
                messages.error(request, error_msg)
        else:
            print("Form validation failed")
            messages.error(request, 'Please correct the errors below.')

    else:
        form = FeedbackForm()

    return render(request, 'feedback.html', {'form': form})

def credits(request):
    return render(request, 'credits.html')


def profile(request):
    return render(request, 'profile.html')

