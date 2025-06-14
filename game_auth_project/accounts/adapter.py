from allauth.account.adapter import DefaultAccountAdapter
from django import forms
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

User = get_user_model()

class CustomAccountAdapter(DefaultAccountAdapter):
    def clean_email(self, email):
        """
        Only validate email during signup (not login/password reset)
        """
        email = super().clean_email(email)  # First run default validation
        
        # Only check for existing emails during signup
        if hasattr(self, 'request') and self.request.path == reverse('account_signup'):
            email = email.lower().strip() if email else email
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError(
                    "This email is already registered. If you forgot your password, please reset it."
                    
                )
        return email

    # Comment out email sending functionality since we're disabling verification
    # def send_mail(self, template_prefix, email, context):
    #     """
    #     Add support email to all outgoing emails
    #     """
    #     context['support_email'] = 'support@phantom-load.in'
    #     context['site_name'] = settings.SITE_NAME
    #     return super().send_mail(template_prefix, email, context)

    # Disable email verification requirement
    def is_open_for_signup(self, request):
        return True

    # Skip email verification
    def confirm_email(self, request, email_address):
        return

    # Don't require email confirmation
    def get_email_confirmation_url(self, request, emailconfirmation):
        return