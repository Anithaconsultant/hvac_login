from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser,UserGameProgress
from allauth.account.forms import SignupForm
from django.utils.safestring import mark_safe
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
import json

# class CustomUserCreationForm(SignupForm):
#     first_name = forms.CharField(max_length=30, required=True)
#     last_name = forms.CharField(max_length=30, required=True)
#     nickname = forms.CharField(max_length=30, required=False)
#     mobile_number = forms.CharField(max_length=20, required=False)

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         for field_name in self.fields:
#             self.fields[field_name].label = ''

#         self.fields['email'].widget.attrs.update({
#             'class': 'auth-form-control',
#             'placeholder': 'Email'
#         })
#         self.fields['first_name'].widget.attrs.update({
#             'class': 'auth-form-control',
#             'placeholder': 'First Name'
#         })
#         self.fields['last_name'].widget.attrs.update({
#             'class': 'auth-form-control',
#             'placeholder': 'Last Name'
#         })
#         self.fields['nickname'].widget.attrs.update({
#             'class': 'auth-form-control',
#             'placeholder': 'Nickname (optional)'
#         })
#         self.fields['mobile_number'].widget.attrs.update({
#             'class': 'auth-form-control',
#             'placeholder': 'Mobile Number (optional)'
#         })
#         self.fields['password1'].widget.attrs.update({
#             'class': 'auth-form-control',
#             'placeholder': 'Password'
#         })

#     def save(self, request):
#         user = super().save(request)
#         user.first_name = self.cleaned_data['first_name']
#         user.last_name = self.cleaned_data['last_name']
#         user.nickname = self.cleaned_data.get('nickname')
#         user.mobile_number = self.cleaned_data.get('mobile_number')
#         user.save()
#         return user


from django import forms
from allauth.account.forms import SignupForm
from django.utils.safestring import mark_safe
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class CustomUserCreationForm(SignupForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    nickname = forms.CharField(max_length=30, required=False)
    mobile_number = forms.CharField(max_length=20, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove all labels
        for field_name in self.fields:
            self.fields[field_name].label = ''

        # Common attributes for all fields
        common_attrs = {
            'class': 'auth-form-control',
            'autocomplete': 'off'
        }

        # Update widget attributes
        field_placeholders = {
            'email': 'Email',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'nickname': 'Nickname (optional)',
            'mobile_number': 'Mobile Number (optional)',
            'password1': 'Password'
        }

        for field, placeholder in field_placeholders.items():
            self.fields[field].widget.attrs.update({
                **common_attrs,
                'placeholder': placeholder
            })

        # Special password field configuration
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

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        validate_password(password1)  # Will raise ValidationError with all messages
        return password1
    
    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.nickname = self.cleaned_data.get('nickname')
        user.mobile_number = self.cleaned_data.get('mobile_number')
        user.save()
        return user

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name',
                  'game_version', 'nickname')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove labels
        for field_name in self.fields:
            self.fields[field_name].label = ''

        # Set placeholders and classes
        self.fields['email'].widget.attrs.update({
            'class': 'auth-form-control',
            'placeholder': 'Email'
        })
        self.fields['first_name'].widget.attrs.update({
            'class': 'auth-form-control',
            'placeholder': 'First Name'
        })
        self.fields['last_name'].widget.attrs.update({
            'class': 'auth-form-control',
            'placeholder': 'Last Name'
        })
        self.fields['game_version'].widget.attrs.update({
            'class': 'auth-form-control',
            'placeholder': 'Game Version'
        })
        self.fields['nickname'].widget.attrs.update({
            'class': 'auth-form-control',
            'placeholder': 'Nickname'
        })


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Remove labels for all fields
        for field in self.fields.values():
            field.label = None  # Removes the label

        # Apply CSS classes and placeholders
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('email',
                  css_class='auth-form-control',
                  placeholder='Email',
                  wrapper_class='form-group',
                  label='',  # Explicitly remove the label from crispy form
                  ),
            Field('password',
                  css_class='auth-form-control',
                  placeholder='Password',
                  wrapper_class='form-group',
                  label='',  # Explicitly remove the label from crispy form
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
        fields = ['level', 'attempt_number', 'task_number', 'completion_status', 
                'points_scored', 'time_taken', 'max_points', 'hint_penalty_points',
                'bonus_points', 'tools_earned', 'badges', 'super_powers']
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Apply auth-form-control class to all fields
        if self.instance and self.instance.pk:
            for field in ['tools_earned', 'badges', 'super_powers']:
                if getattr(self.instance, field):
                    self.initial[field] = ', '.join(getattr(self.instance, field))
        
        # Apply auth-form-control to all fields
        for field_name, field in self.fields.items():
            if field_name not in ['tools_earned', 'badges', 'super_powers']:
                field.widget.attrs.update({'class': 'auth-form-control'})
        
        def clean(self):
            cleaned_data = super().clean()
            
            # Convert comma-separated strings back to lists
            for field in ['tools_earned', 'badges', 'super_powers']:
                if cleaned_data.get(field):
                    items = [item.strip() for item in cleaned_data[field].split(',') if item.strip()]
                    cleaned_data[field] = items
            
            return cleaned_data