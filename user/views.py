from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

from .forms import LoginForm, RegisterForm, PasswordResetRequestForm, PasswordResetConfirmForm
from .models import CustomUser, PasswordResetToken, EmailVerificationToken


def send_verification_email(user, token):
    """Envía el correo de verificación de email al usuario."""
    verification_url = f'{settings.SITE_URL}/user/verify-email/{token.token}/'
    
    html_message = render_to_string('user/emails/verification_email.html', {
        'user': user,
        'verification_url': verification_url,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject='Verifica tu cuenta - Dimensional Chaos TCG',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def user_login(request):
    """Vista para iniciar sesión."""
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # Verificar si el email está verificado
            if not user.is_email_verified:
                messages.error(
                    request,
                    'Debes verificar tu correo electrónico antes de iniciar sesión. '
                    'Revisa tu bandeja de entrada o solicita un nuevo enlace.'
                )
                return render(request, 'user/login.html', {
                    'form': form,
                    'show_resend': True,
                    'unverified_email': user.email,
                })
            
            # Manejar "Recordar sesión"
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)  # Sesión expira al cerrar navegador
            login(request, user)
            messages.success(request, f'¡Bienvenido, {user.username}!')
            return redirect('/')
        else:
            messages.error(request, 'Email o contraseña incorrectos.')
    else:
        form = LoginForm()

    return render(request, 'user/login.html', {'form': form})


def user_register(request):
    """Vista para registrar un nuevo usuario."""
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_email_verified = False
            user.is_active = True
            user.save()

            # Crear token de verificación de email y enviar correo
            token = EmailVerificationToken.objects.create(user=user)
            try:
                send_verification_email(user, token)
            except Exception as e:
                # Si falla el envío, el usuario aún puede solicitar reenvío
                pass

            messages.success(
                request,
                'Cuenta creada exitosamente. Revisa tu correo para verificar tu cuenta.'
            )
            return redirect('user:verification_sent')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = RegisterForm()

    return render(request, 'user/register.html', {'form': form})


@login_required
def user_logout(request):
    """Vista para cerrar sesión."""
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('/')


def password_reset_request(request):
    """Vista para solicitar recuperación de contraseña."""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                # Invalidar tokens anteriores
                PasswordResetToken.objects.filter(user=user, used=False).update(used=True)
                # Crear nuevo token
                token = PasswordResetToken.objects.create(user=user)
                # TODO: Enviar email con el link de recuperación
                # send_password_reset_email(user, token)
                messages.success(
                    request,
                    'Se ha enviado un enlace de recuperación a tu correo electrónico.'
                )
            except CustomUser.DoesNotExist:
                # No revelar si el email existe o no (seguridad)
                messages.success(
                    request,
                    'Si el correo existe en nuestro sistema, recibirás un enlace de recuperación.'
                )
            return redirect('user:login')
    else:
        form = PasswordResetRequestForm()

    return render(request, 'user/password_reset_request.html', {'form': form})


def password_reset_confirm(request, token):
    """Vista para confirmar el reset de contraseña con un token."""
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'El enlace de recuperación no es válido.')
        return redirect('user:login')

    if not reset_token.is_valid:
        messages.error(request, 'El enlace de recuperación ha expirado o ya fue utilizado.')
        return redirect('user:password_reset_request')

    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            user = reset_token.user
            user.password = make_password(form.cleaned_data['new_password1'])
            user.save()
            reset_token.used = True
            reset_token.save()
            messages.success(request, 'Contraseña actualizada correctamente. Ya puedes iniciar sesión.')
            return redirect('user:login')
    else:
        form = PasswordResetConfirmForm()

    return render(request, 'user/password_reset_confirm.html', {'form': form, 'token': token})


def verify_email(request, token):
    """Vista para verificar el email del usuario."""
    try:
        verification_token = EmailVerificationToken.objects.get(token=token)
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, 'El enlace de verificación no es válido.')
        return redirect('user:login')

    if not verification_token.is_valid:
        messages.error(request, 'El enlace de verificación ha expirado o ya fue utilizado.')
        return redirect('user:login')

    user = verification_token.user
    user.is_email_verified = True
    user.save()
    verification_token.used = True
    verification_token.save()

    messages.success(request, '¡Email verificado correctamente! Ya puedes iniciar sesión.')
    return redirect('user:login')


def verification_sent(request):
    """Vista que muestra la página de confirmación de envío de verificación."""
    return render(request, 'user/verification_sent.html')


def resend_verification(request):
    """Vista para reenviar el correo de verificación."""
    if request.method == 'POST':
        email = request.POST.get('email', '')
        try:
            user = CustomUser.objects.get(email=email)
            if user.is_email_verified:
                messages.info(request, 'Tu correo ya está verificado. Puedes iniciar sesión.')
                return redirect('user:login')
            
            # Invalidar tokens anteriores
            EmailVerificationToken.objects.filter(user=user, used=False).update(used=True)
            # Crear nuevo token y enviar email
            token = EmailVerificationToken.objects.create(user=user)
            try:
                send_verification_email(user, token)
                messages.success(
                    request,
                    'Se ha reenviado el correo de verificación. Revisa tu bandeja de entrada.'
                )
            except Exception:
                messages.error(
                    request,
                    'Hubo un error al enviar el correo. Intenta de nuevo más tarde.'
                )
        except CustomUser.DoesNotExist:
            # No revelar si el email existe (seguridad)
            messages.success(
                request,
                'Si el correo existe en nuestro sistema, recibirás un enlace de verificación.'
            )
        return redirect('user:login')
    
    return redirect('user:login')