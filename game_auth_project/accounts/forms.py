from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser
from allauth.account.forms import SignupForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field


class CustomUserCreationForm(SignupForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    nickname = forms.CharField(max_length=30, required=False)
    mobile_number = forms.CharField(max_length=20, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in self.fields:
            self.fields[field_name].label = ''

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
        self.fields['nickname'].widget.attrs.update({
            'class': 'auth-form-control',
            'placeholder': 'Nickname (optional)'
        })
        self.fields['mobile_number'].widget.attrs.update({
            'class': 'auth-form-control',
            'placeholder': 'Mobile Number (optional)'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'auth-form-control',
            'placeholder': 'Password'
        })

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
