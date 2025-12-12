from allauth.account.adapter import DefaultAccountAdapter
from django import forms
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from django.shortcuts import redirect

User = get_user_model()


class CustomAccountAdapter(DefaultAccountAdapter):
    def clean_email(self, email):
        email = super().clean_email(email)
        if hasattr(self, 'request') and self.request.path == reverse('account_signup'):
            email = email.lower().strip() if email else email
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError(
                    "This email is already registered. If you forgot your password, please reset it."
                )
        return email

    def send_mail(self, template_prefix, email, context):
        context['support_email'] = 'support@phantom-load.in'
        context['site_name'] = settings.SITE_NAME
        print(f"📧 Sending verification email to {email}")  # Debug line
        print("📨 Template prefix:", template_prefix)
        print("🔍 Looking for HTML template at: account/email/%s_message.html" %
          template_prefix)
        return super().send_mail(template_prefix, email, context)

    def get_email_confirmation_url(self, request, emailconfirmation):
        url = reverse("account_confirm_email", args=[emailconfirmation.key])
        full_url = f"{request.scheme}://{request.get_host()}{url}"
        print(f"🔗 Confirmation URL: {full_url}")
        return full_url

    def respond_email_verification_sent(self, request, user):
        """
        Redirect user to the 'verification sent' page after signup.
        """
        print("✅ Redirecting to verification sent page...")
        return redirect('account_email_verification_sent')
