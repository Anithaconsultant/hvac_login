from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser,Group
from .forms import CustomUserCreationForm, CustomUserChangeForm


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


    
from .models import ActiveSession,WebGLSession

@admin.register(ActiveSession)
class ActiveSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "session_key", "login_time")
    search_fields = ("user__username", "user__email")

@admin.register(WebGLSession)
class WebGLSessionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "session_id",
        "status",
        "is_alive",
        "started_at",
        "last_ping",
    )

    list_filter = (
        "status",
        "is_alive",
        "started_at",
    )

    search_fields = (
        "user__email",
        "session_id",
        "browser_session_key",
    )

    ordering = ("-last_ping",)

    readonly_fields = (
        "started_at",
        "last_ping",
    )

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):

    list_display = (
        'group_id',
        'group_name',
        'organisation',
        'user_count'
    )

    readonly_fields = ('group_id', 'user_count')

admin.site.register(CustomUser, CustomUserAdmin)



