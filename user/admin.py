from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, PasswordResetToken, EmailVerificationToken


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin personalizado para el modelo CustomUser."""
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_email_verified', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'is_email_verified', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {
            'fields': ('avatar', 'bio', 'date_of_birth', 'is_email_verified'),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información adicional', {
            'fields': ('email', 'avatar', 'bio', 'date_of_birth'),
        }),
    )


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'used', 'is_expired')
    list_filter = ('used', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('token', 'created_at')

    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expirado'


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'used', 'is_expired')
    list_filter = ('used', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('token', 'created_at')

    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = 'Expirado'