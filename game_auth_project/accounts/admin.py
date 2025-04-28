from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm, LoginForm


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'nickname',
                    'game_version', 'date_registered', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_registered')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name',
         'last_name', 'nickname', 'game_version')}),
        ('Permissions', {'fields': ('is_active', 'is_staff',
         'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_registered')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'nickname', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name', 'nickname')
    ordering = ('email',)


admin.site.register(CustomUser, CustomUserAdmin)
