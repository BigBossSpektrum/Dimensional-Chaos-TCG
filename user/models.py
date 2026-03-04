import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


class CustomUser(AbstractUser):
    """
    Modelo de usuario personalizado que extiende AbstractUser.
    Incluye campos adicionales para el perfil del usuario.
    """
    email = models.EmailField('correo electrónico', unique=True)
    avatar = models.ImageField(
        'avatar',
        upload_to='avatars/',
        blank=True,
        null=True,
        default='avatars/default_avatar.png'
    )
    bio = models.TextField('biografía', max_length=500, blank=True)
    date_of_birth = models.DateField('fecha de nacimiento', blank=True, null=True)
    is_email_verified = models.BooleanField('email verificado', default=False)

    # Usar email como campo de login en lugar de username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Retorna el nombre completo del usuario."""
        full_name = f'{self.first_name} {self.last_name}'.strip()
        return full_name if full_name else self.username


class PasswordResetToken(models.Model):
    """
    Token para la recuperación de contraseña.
    Expira después de 24 horas.
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
        verbose_name='usuario'
    )
    token = models.UUIDField('token', default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField('creado en', auto_now_add=True)
    used = models.BooleanField('usado', default=False)

    class Meta:
        verbose_name = 'token de recuperación'
        verbose_name_plural = 'tokens de recuperación'
        ordering = ['-created_at']

    def __str__(self):
        return f'Token para {self.user.email} - {"Usado" if self.used else "Activo"}'

    @property
    def is_expired(self):
        """Verifica si el token ha expirado (24 horas)."""
        return timezone.now() > self.created_at + timedelta(hours=24)

    @property
    def is_valid(self):
        """Verifica si el token es válido (no usado y no expirado)."""
        return not self.used and not self.is_expired


class EmailVerificationToken(models.Model):
    """
    Token para la verificación de email al registrarse.
    Expira después de 48 horas.
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='email_verification_tokens',
        verbose_name='usuario'
    )
    token = models.UUIDField('token', default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField('creado en', auto_now_add=True)
    used = models.BooleanField('usado', default=False)

    class Meta:
        verbose_name = 'token de verificación de email'
        verbose_name_plural = 'tokens de verificación de email'
        ordering = ['-created_at']

    def __str__(self):
        return f'Verificación para {self.user.email} - {"Usado" if self.used else "Activo"}'

    @property
    def is_expired(self):
        """Verifica si el token ha expirado (48 horas)."""
        return timezone.now() > self.created_at + timedelta(hours=48)

    @property
    def is_valid(self):
        """Verifica si el token es válido (no usado y no expirado)."""
        return not self.used and not self.is_expired
