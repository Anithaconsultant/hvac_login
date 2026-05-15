from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, UserGameProgress,Group
from allauth.account.forms import SignupForm
from django.utils.safestring import mark_safe
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field

import pycountry
import phonenumbers


COUNTRY_CHOICES = sorted(
    [(c.alpha_2, c.name) for c in pycountry.countries],
    key=lambda x: x[1]
)

GENDER_CHOICES = [
    ('male', 'Male'),
    ('female', 'Female'),
    ('other', 'Other'),
]


class CustomUserCreationForm(SignupForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    nickname = forms.CharField(max_length=30, required=True)
    gender = forms.ChoiceField(choices=GENDER_CHOICES, required=True)
    group_id = forms.CharField(max_length=10, required=False)

    country = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        required=True,
        initial='IN'
    )

    mobile_number = forms.CharField(max_length=15, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in self.fields:
            self.fields[field_name].label = ''

        common_attrs = {
            'class': 'auth-form-control',
            'autocomplete': 'off'
        }

        field_placeholders = {
            'email': 'Email',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'nickname': 'Nickname ',
            'mobile_number': 'Enter number (no country code)',
            'password1': 'Set your password'
        }

        for field, placeholder in field_placeholders.items():
            if field in self.fields:
                self.fields[field].widget.attrs.update({
                    **common_attrs,
                    'placeholder': placeholder
                })

        # ✅ FIX: add styling safely
        if 'country' in self.fields:
            self.fields['country'].widget.attrs.update(common_attrs)

        if 'gender' in self.fields:
            self.fields['gender'].widget.attrs.update(common_attrs)

        self.fields['password1'].help_text = mark_safe(
            '<small class="password-help-text">'
            'Password must contain: '
            '<ul class="password-requirements">'
            '<li>At least 8 characters</li>'
            '<li>1 uppercase letter</li>'
            '<li>1 lowercase letter</li>'
            '<li>1 number</li>'
            '<li>1 special character</li>'
            '</ul>'
            '</small>'
        )
        self.fields['group_id'].widget.attrs.update({
            'class': 'auth-form-control',
            'placeholder': 'Enter Group ID',
            'autocomplete': 'off',
            'id': 'group_id_input'   # 👈 important for JS
        })
        for field_name, field in self.fields.items():
            if field.required:
                existing_class = field.widget.attrs.get('class', '')

                field.widget.attrs['class'] = (
                    existing_class + ' required-input'
                )
        
    def clean_group_id(self):
        group_id = self.cleaned_data.get('group_id')
        if group_id:
            try:
                group = Group.objects.get(
                    group_id=group_id.upper()
                )
                self.cleaned_data['group_instance'] = group
            except Group.DoesNotExist:
                raise ValidationError("Invalid Group ID")
        return group_id.upper()
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        validate_password(password1)
        return password1

    def clean_mobile_number(self):
        mobile = self.cleaned_data.get('mobile_number')
        country = self.cleaned_data.get('country')

        if not mobile:
            raise ValidationError("Mobile number is required")

        mobile = mobile.strip()

        if not mobile.isdigit():
            raise ValidationError("Enter digits only")

        try:
            parsed_number = phonenumbers.parse(mobile, region=country)

            if not phonenumbers.is_valid_number(parsed_number):
                raise ValidationError("Invalid mobile number for selected country")

            full_number = phonenumbers.format_number(
                parsed_number,
                phonenumbers.PhoneNumberFormat.E164
            )

            # ✅ CHECK DUPLICATE HERE
            if CustomUser.objects.filter(
                mobile_number=full_number
            ).exists():
                raise ValidationError(
                    "This mobile number is already registered"
                )

            self.cleaned_data['full_mobile_number'] = full_number

        except phonenumbers.NumberParseException:
            raise ValidationError("Invalid phone number format")

        return mobile


    def save(self, request):
        user = super().save(request)

        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.nickname = self.cleaned_data.get('nickname')

        user.gender = self.cleaned_data.get('gender')
        user.country = self.cleaned_data.get('country')

        user.mobile_number = self.cleaned_data.get('full_mobile_number', None)

        # ✅ Assign group
        user.group = self.cleaned_data.get('group_instance', None)

        user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'game_version', 'nickname')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in self.fields:
            self.fields[field_name].label = ''

        common_attrs = {
            'class': 'auth-form-control',
            'autocomplete': 'off'
        }

        field_placeholders = {
            'email': 'Email',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'nickname': 'Nickname',
            'game_version': 'Game Version'
        }

        for field, placeholder in field_placeholders.items():
            if field in self.fields:
                self.fields[field].widget.attrs.update({
                    **common_attrs,
                    'placeholder': placeholder
                })


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.label = None

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('email',
                  css_class='auth-form-control',
                  placeholder='Email',
                  wrapper_class='form-group',
                  label='',
                  ),
            Field('password',
                  css_class='auth-form-control',
                  placeholder='Password',
                  wrapper_class='form-group',
                  label='',
                  ),
        )


class UserGameProgressForm(forms.ModelForm):
    tools_earned = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'auth-form-control json-field',
            'placeholder': 'Enter as comma-separated values, e.g. hammer,wrench,screwdriver'
        }),
        required=False
    )

    badges = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'auth-form-control json-field',
            'placeholder': 'Enter as comma-separated values, e.g. fast_learner,energy_saver'
        }),
        required=False
    )

    super_powers = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'auth-form-control json-field',
            'placeholder': 'Enter as comma-separated values, e.g. xray_vision,time_travel'
        }),
        required=False
    )

    class Meta:
        model = UserGameProgress
        fields = [
            'level', 'attempt_number', 'task_number', 'completion_status',
            'points_scored', 'time_taken', 'max_points', 'hint_penalty_points',
            'bonus_points', 'tools_earned', 'badges', 'super_powers'
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            for field in ['tools_earned', 'badges', 'super_powers']:
                if getattr(self.instance, field):
                    self.initial[field] = ', '.join(getattr(self.instance, field))

        for field_name, field in self.fields.items():
            if field_name not in ['tools_earned', 'badges', 'super_powers']:
                field.widget.attrs.update({'class': 'auth-form-control'})

    def clean(self):
        cleaned_data = super().clean()

        for field in ['tools_earned', 'badges', 'super_powers']:
            if cleaned_data.get(field):
                items = [item.strip() for item in cleaned_data[field].split(',') if item.strip()]
                cleaned_data[field] = items

        return cleaned_data


class FeedbackForm(forms.Form):
    feedback = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'cols': 30,
            'placeholder': 'Please enter your feedback here...',
            'class': 'form-control'
        }),
        label='Your Feedback'
    )