from django.test import TestCase, override_settings
from django.core import mail
from django.urls import reverse
from django.conf import settings

from .models import CustomUser, EmailVerificationToken, PasswordResetToken
from .views import send_verification_email, send_password_reset_email, send_account_activity_email
from .validators import ISO27001PasswordValidator, MaximumLengthValidator


# Usar backend de memoria para capturar emails en los tests
@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class EmailVerificationTests(TestCase):
    """Tests para el envío de correo de verificación de email."""

    def setUp(self):
        """Crear usuario de prueba."""
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='TestPass123!',
            is_email_verified=False,
        )
        self.token = EmailVerificationToken.objects.create(user=self.user)

    def test_send_verification_email_success(self):
        """Verificar que se envía el correo de verificación correctamente."""
        send_verification_email(self.user, self.token)

        # Verificar que se envió exactamente 1 correo
        self.assertEqual(len(mail.outbox), 1)

    def test_verification_email_subject(self):
        """Verificar que el asunto del correo es correcto."""
        send_verification_email(self.user, self.token)

        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Verifica tu cuenta - Dimensional Chaos TCG')

    def test_verification_email_recipient(self):
        """Verificar que el correo se envía al email del usuario."""
        send_verification_email(self.user, self.token)

        email = mail.outbox[0]
        self.assertIn(self.user.email, email.to)

    def test_verification_email_from(self):
        """Verificar que el remitente es el correo configurado."""
        send_verification_email(self.user, self.token)

        email = mail.outbox[0]
        self.assertEqual(email.from_email, settings.DEFAULT_FROM_EMAIL)

    def test_verification_email_contains_token_url(self):
        """Verificar que el correo contiene el enlace de verificación."""
        send_verification_email(self.user, self.token)

        email = mail.outbox[0]
        expected_url = f'{settings.SITE_URL}/user/verify-email/{self.token.token}/'
        self.assertIn(expected_url, email.body)

    def test_verification_email_contains_username(self):
        """Verificar que el correo contiene el nombre de usuario."""
        send_verification_email(self.user, self.token)

        email = mail.outbox[0]
        self.assertIn(self.user.username, email.body)

    def test_verification_email_has_html_content(self):
        """Verificar que el correo incluye contenido HTML."""
        send_verification_email(self.user, self.token)

        email = mail.outbox[0]
        # Django almacena html_message en alternatives
        self.assertTrue(len(email.alternatives) > 0)
        html_content = email.alternatives[0][0]
        self.assertIn('Dimensional Chaos TCG', html_content)
        self.assertIn(self.user.username, html_content)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class RegisterEmailTests(TestCase):
    """Tests para el envío de email durante el registro."""

    def test_register_sends_verification_email(self):
        """Verificar que al registrarse se envía un correo de verificación."""
        response = self.client.post(reverse('user:register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })

        # Verificar que se envió el correo de verificación
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['newuser@example.com'])

    def test_register_creates_verification_token(self):
        """Verificar que al registrarse se crea un token de verificación."""
        self.client.post(reverse('user:register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })

        user = CustomUser.objects.get(email='newuser@example.com')
        self.assertTrue(EmailVerificationToken.objects.filter(user=user).exists())

    def test_registered_user_email_not_verified(self):
        """Verificar que un usuario recién registrado no tiene email verificado."""
        self.client.post(reverse('user:register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        })

        user = CustomUser.objects.get(email='newuser@example.com')
        self.assertFalse(user.is_email_verified)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class VerifyEmailViewTests(TestCase):
    """Tests para la vista de verificación de email."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='TestPass123!',
            is_email_verified=False,
        )
        self.token = EmailVerificationToken.objects.create(user=self.user)

    def test_verify_email_valid_token(self):
        """Verificar que un token válido activa el email del usuario."""
        response = self.client.get(
            reverse('user:verify_email', kwargs={'token': self.token.token})
        )

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)

    def test_verify_email_marks_token_used(self):
        """Verificar que el token se marca como usado después de verificar."""
        self.client.get(
            reverse('user:verify_email', kwargs={'token': self.token.token})
        )

        self.token.refresh_from_db()
        self.assertTrue(self.token.used)

    def test_verify_email_redirects_to_login(self):
        """Verificar que la verificación redirige al login."""
        response = self.client.get(
            reverse('user:verify_email', kwargs={'token': self.token.token})
        )

        self.assertRedirects(response, reverse('user:login'))

    def test_verify_email_invalid_token(self):
        """Verificar que un token inválido muestra error."""
        import uuid
        fake_token = uuid.uuid4()
        response = self.client.get(
            reverse('user:verify_email', kwargs={'token': fake_token})
        )

        self.assertRedirects(response, reverse('user:login'))

    def test_verify_email_used_token(self):
        """Verificar que un token ya usado no permite verificar de nuevo."""
        self.token.used = True
        self.token.save()

        response = self.client.get(
            reverse('user:verify_email', kwargs={'token': self.token.token})
        )

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_email_verified)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ResendVerificationTests(TestCase):
    """Tests para el reenvío de correo de verificación."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='TestPass123!',
            is_email_verified=False,
        )

    def test_resend_verification_sends_email(self):
        """Verificar que el reenvío envía un nuevo correo."""
        response = self.client.post(
            reverse('user:resend_verification'),
            {'email': self.user.email}
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])

    def test_resend_verification_creates_new_token(self):
        """Verificar que el reenvío crea un nuevo token."""
        # Crear token antiguo
        old_token = EmailVerificationToken.objects.create(user=self.user)

        self.client.post(
            reverse('user:resend_verification'),
            {'email': self.user.email}
        )

        # El token antiguo debe estar marcado como usado
        old_token.refresh_from_db()
        self.assertTrue(old_token.used)

        # Debe existir un nuevo token activo
        new_token = EmailVerificationToken.objects.filter(
            user=self.user, used=False
        ).first()
        self.assertIsNotNone(new_token)

    def test_resend_verification_already_verified(self):
        """Verificar que no se reenvía si el email ya está verificado."""
        self.user.is_email_verified = True
        self.user.save()

        self.client.post(
            reverse('user:resend_verification'),
            {'email': self.user.email}
        )

        self.assertEqual(len(mail.outbox), 0)

    def test_resend_verification_nonexistent_email(self):
        """Verificar que no se revela si un email no existe."""
        response = self.client.post(
            reverse('user:resend_verification'),
            {'email': 'nonexistent@example.com'}
        )

        # No debe enviar correo
        self.assertEqual(len(mail.outbox), 0)
        # Debe redirigir sin error (seguridad)
        self.assertEqual(response.status_code, 302)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class LoginUnverifiedEmailTests(TestCase):
    """Tests para el login con email no verificado."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='TestPass123!',
            is_email_verified=False,
        )

    def test_login_unverified_email_fails(self):
        """Verificar que no se puede hacer login sin email verificado."""
        response = self.client.post(reverse('user:login'), {
            'username': 'testuser@example.com',
            'password': 'TestPass123!',
        })

        # No debe redirigir (login fallido, se muestra el form con mensaje de verificación)
        self.assertEqual(response.status_code, 200)
        # Verificar que se muestra la opción de reenviar verificación
        self.assertTrue(response.context.get('show_resend', False))

    def test_login_verified_email_succeeds(self):
        """Verificar que se puede hacer login con email verificado."""
        self.user.is_email_verified = True
        self.user.save()

        response = self.client.post(reverse('user:login'), {
            'username': 'testuser@example.com',
            'password': 'TestPass123!',
        })

        # Debe redirigir al index (login exitoso)
        self.assertEqual(response.status_code, 302)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PasswordResetTests(TestCase):
    """Tests para la recuperación de contraseña."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='TestPass123!',
            is_email_verified=True,
        )

    def test_password_reset_request_creates_token(self):
        """Verificar que solicitar reset crea un token."""
        self.client.post(reverse('user:password_reset_request'), {
            'email': self.user.email,
        })

        self.assertTrue(PasswordResetToken.objects.filter(user=self.user).exists())

    def test_password_reset_request_sends_email(self):
        """Verificar que solicitar reset envía un correo."""
        self.client.post(reverse('user:password_reset_request'), {
            'email': self.user.email,
        })

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])

    def test_password_reset_email_subject(self):
        """Verificar que el asunto del correo de reset es correcto."""
        self.client.post(reverse('user:password_reset_request'), {
            'email': self.user.email,
        })

        self.assertEqual(mail.outbox[0].subject, 'Recupera tu contraseña - Dimensional Chaos TCG')

    def test_password_reset_email_contains_reset_url(self):
        """Verificar que el correo contiene el enlace de recuperación."""
        self.client.post(reverse('user:password_reset_request'), {
            'email': self.user.email,
        })

        token = PasswordResetToken.objects.filter(user=self.user, used=False).first()
        expected_url = f'{settings.SITE_URL}/user/password-reset/{token.token}/'
        self.assertIn(expected_url, mail.outbox[0].body)

    def test_password_reset_email_has_html_content(self):
        """Verificar que el correo de reset incluye contenido HTML."""
        self.client.post(reverse('user:password_reset_request'), {
            'email': self.user.email,
        })

        email = mail.outbox[0]
        self.assertTrue(len(email.alternatives) > 0)
        html_content = email.alternatives[0][0]
        self.assertIn('Restablecer contrase', html_content)

    def test_send_password_reset_email_function(self):
        """Verificar la función send_password_reset_email directamente."""
        token = PasswordResetToken.objects.create(user=self.user)
        send_password_reset_email(self.user, token)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, settings.DEFAULT_FROM_EMAIL)
        self.assertIn(self.user.email, mail.outbox[0].to)

    def test_password_reset_request_invalidates_old_tokens(self):
        """Verificar que un nuevo request invalida tokens anteriores."""
        old_token = PasswordResetToken.objects.create(user=self.user)

        self.client.post(reverse('user:password_reset_request'), {
            'email': self.user.email,
        })

        old_token.refresh_from_db()
        self.assertTrue(old_token.used)

    def test_password_reset_request_nonexistent_email(self):
        """Verificar que no se revela si un email no existe."""
        response = self.client.post(reverse('user:password_reset_request'), {
            'email': 'fake@example.com',
        })

        # Debe redirigir sin error (seguridad)
        self.assertEqual(response.status_code, 302)

    def test_password_reset_confirm_valid_token(self):
        """Verificar que se puede cambiar la contraseña con un token válido."""
        token = PasswordResetToken.objects.create(user=self.user)

        response = self.client.post(
            reverse('user:password_reset_confirm', kwargs={'token': token.token}),
            {
                'new_password1': 'NewSecurePass456!',
                'new_password2': 'NewSecurePass456!',
            }
        )

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecurePass456!'))

    def test_password_reset_confirm_marks_token_used(self):
        """Verificar que el token se marca como usado después de cambiar contraseña."""
        token = PasswordResetToken.objects.create(user=self.user)

        self.client.post(
            reverse('user:password_reset_confirm', kwargs={'token': token.token}),
            {
                'new_password1': 'NewSecurePass456!',
                'new_password2': 'NewSecurePass456!',
            }
        )

        token.refresh_from_db()
        self.assertTrue(token.used)

    def test_password_reset_confirm_invalid_token(self):
        """Verificar que un token inválido redirige con error."""
        import uuid
        fake_token = uuid.uuid4()

        response = self.client.get(
            reverse('user:password_reset_confirm', kwargs={'token': fake_token})
        )

        self.assertRedirects(response, reverse('user:login'))


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class EmailTokenExpirationTests(TestCase):
    """Tests para la expiración de tokens de email."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='TestPass123!',
            is_email_verified=False,
        )

    def test_email_verification_token_valid_initially(self):
        """Verificar que un token recién creado es válido."""
        token = EmailVerificationToken.objects.create(user=self.user)
        self.assertTrue(token.is_valid)

    def test_email_verification_token_expired(self):
        """Verificar que un token expira después de 48 horas."""
        from datetime import timedelta
        from django.utils import timezone

        token = EmailVerificationToken.objects.create(user=self.user)
        # Forzar fecha de creación a más de 48 horas atrás
        EmailVerificationToken.objects.filter(pk=token.pk).update(
            created_at=timezone.now() - timedelta(hours=49)
        )
        token.refresh_from_db()

        self.assertTrue(token.is_expired)
        self.assertFalse(token.is_valid)

    def test_password_reset_token_valid_initially(self):
        """Verificar que un token de reset recién creado es válido."""
        token = PasswordResetToken.objects.create(user=self.user)
        self.assertTrue(token.is_valid)

    def test_password_reset_token_expired(self):
        """Verificar que un token de reset expira después de 24 horas."""
        from datetime import timedelta
        from django.utils import timezone

        token = PasswordResetToken.objects.create(user=self.user)
        PasswordResetToken.objects.filter(pk=token.pk).update(
            created_at=timezone.now() - timedelta(hours=25)
        )
        token.refresh_from_db()

        self.assertTrue(token.is_expired)
        self.assertFalse(token.is_valid)

    def test_used_token_is_invalid(self):
        """Verificar que un token usado no es válido."""
        token = EmailVerificationToken.objects.create(user=self.user)
        token.used = True
        token.save()

        self.assertFalse(token.is_valid)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AccountActivityEmailTests(TestCase):
    """Tests para el correo de notificación de actividad de cuenta."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='TestPass123!',
            is_email_verified=True,
        )

    def test_send_account_activity_email_success(self):
        """Verificar que se envía el correo de actividad correctamente."""
        send_account_activity_email(self.user, 'Inicio de sesión', '127.0.0.1')

        self.assertEqual(len(mail.outbox), 1)

    def test_account_activity_email_subject(self):
        """Verificar que el asunto del correo de actividad es correcto."""
        send_account_activity_email(self.user, 'Inicio de sesión', '127.0.0.1')

        self.assertEqual(mail.outbox[0].subject, 'Actividad en tu cuenta - Dimensional Chaos TCG')

    def test_account_activity_email_recipient(self):
        """Verificar que el correo se envía al email del usuario."""
        send_account_activity_email(self.user, 'Inicio de sesión', '192.168.1.1')

        self.assertIn(self.user.email, mail.outbox[0].to)

    def test_account_activity_email_contains_activity_type(self):
        """Verificar que el correo contiene el tipo de actividad."""
        send_account_activity_email(self.user, 'Inicio de sesión', '127.0.0.1')

        email = mail.outbox[0]
        html_content = email.alternatives[0][0]
        self.assertIn('Inicio de sesi', html_content)

    def test_account_activity_email_contains_ip(self):
        """Verificar que el correo contiene la dirección IP."""
        send_account_activity_email(self.user, 'Inicio de sesión', '192.168.1.100')

        email = mail.outbox[0]
        html_content = email.alternatives[0][0]
        self.assertIn('192.168.1.100', html_content)

    def test_account_activity_email_contains_username(self):
        """Verificar que el correo contiene el nombre de usuario."""
        send_account_activity_email(self.user, 'Cambio de contraseña', '127.0.0.1')

        email = mail.outbox[0]
        html_content = email.alternatives[0][0]
        self.assertIn(self.user.username, html_content)

    def test_account_activity_email_contains_support_info(self):
        """Verificar que el correo contiene la info de soporte."""
        send_account_activity_email(self.user, 'Inicio de sesión', '127.0.0.1')

        email = mail.outbox[0]
        html_content = email.alternatives[0][0]
        self.assertIn('dimensionalchaostcg@gmail.com', html_content)
        self.assertIn('No reconoces esta actividad', html_content)

    def test_login_sends_activity_email(self):
        """Verificar que al iniciar sesión se envía email de actividad."""
        self.client.post(reverse('user:login'), {
            'username': 'testuser@example.com',
            'password': 'TestPass123!',
        })

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Actividad en tu cuenta', mail.outbox[0].subject)

    def test_password_reset_confirm_sends_activity_email(self):
        """Verificar que al cambiar contraseña se envía email de actividad."""
        token = PasswordResetToken.objects.create(user=self.user)

        self.client.post(
            reverse('user:password_reset_confirm', kwargs={'token': token.token}),
            {
                'new_password1': 'NewSecurePass456!',
                'new_password2': 'NewSecurePass456!',
            }
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Actividad en tu cuenta', mail.outbox[0].subject)

    def test_activity_email_for_password_change_type(self):
        """Verificar que el email de cambio de contraseña muestra el tipo correcto."""
        token = PasswordResetToken.objects.create(user=self.user)

        self.client.post(
            reverse('user:password_reset_confirm', kwargs={'token': token.token}),
            {
                'new_password1': 'NewSecurePass456!',
                'new_password2': 'NewSecurePass456!',
            }
        )

        email = mail.outbox[0]
        html_content = email.alternatives[0][0]
        self.assertIn('Cambio de contrase', html_content)


class ISO27001PasswordValidatorTests(TestCase):
    """Tests para el validador de contraseñas ISO 27001."""

    def setUp(self):
        self.validator = ISO27001PasswordValidator(min_length=12)

    # --- Tests de longitud ---
    def test_password_too_short(self):
        """Contraseña menor a 12 caracteres debe fallar."""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate('Abc1!short')
        codes = [e.code for e in ctx.exception.error_list]
        self.assertIn('password_too_short', codes)

    def test_password_minimum_length(self):
        """Contraseña de exactamente 12 caracteres válidos debe pasar."""
        # 12 chars: mayúscula, minúscula, número, especial, sin secuencias
        self.validator.validate('Xpm1r9!@Wz3k')  # No debe lanzar excepción

    # --- Tests de mayúscula ---
    def test_password_no_uppercase(self):
        """Contraseña sin mayúscula debe fallar."""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate('abcdef1234!@')
        codes = [e.code for e in ctx.exception.error_list]
        self.assertIn('password_no_upper', codes)

    # --- Tests de minúscula ---
    def test_password_no_lowercase(self):
        """Contraseña sin minúscula debe fallar."""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate('ABCXYZ1234!@')
        codes = [e.code for e in ctx.exception.error_list]
        self.assertIn('password_no_lower', codes)

    # --- Tests de número ---
    def test_password_no_digit(self):
        """Contraseña sin número debe fallar."""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate('Abcdefghij!@')
        codes = [e.code for e in ctx.exception.error_list]
        self.assertIn('password_no_digit', codes)

    # --- Tests de carácter especial ---
    def test_password_no_special_char(self):
        """Contraseña sin carácter especial debe fallar."""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate('Abcdefgh1234')
        codes = [e.code for e in ctx.exception.error_list]
        self.assertIn('password_no_special', codes)

    # --- Tests de caracteres repetidos ---
    def test_password_repeated_chars(self):
        """Contraseña con 4+ caracteres iguales consecutivos debe fallar."""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate('Aaaaa1234!@bc')
        codes = [e.code for e in ctx.exception.error_list]
        self.assertIn('password_repeated_chars', codes)

    def test_password_three_repeated_chars_ok(self):
        """Contraseña con 3 caracteres iguales consecutivos debe pasar."""
        self.validator.validate('Aaab9173!@cd')  # No debe lanzar excepción

    # --- Tests de secuencias numéricas ---
    def test_password_sequential_digits_ascending(self):
        """Contraseña con secuencia numérica ascendente (1234) debe fallar."""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate('Abcx1234!@zz')
        codes = [e.code for e in ctx.exception.error_list]
        self.assertIn('password_sequential_digits', codes)

    def test_password_sequential_digits_descending(self):
        """Contraseña con secuencia numérica descendente (4321) debe fallar."""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate('Abcx4321!@zz')
        codes = [e.code for e in ctx.exception.error_list]
        self.assertIn('password_sequential_digits', codes)

    def test_password_non_sequential_digits_ok(self):
        """Contraseña con números no secuenciales debe pasar."""
        self.validator.validate('Abcx9173!@zz')  # No debe lanzar excepción

    # --- Tests de secuencias alfabéticas ---
    def test_password_sequential_letters_ascending(self):
        """Contraseña con secuencia alfabética ascendente (abcd) debe fallar."""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate('Xabcd917!@zz')
        codes = [e.code for e in ctx.exception.error_list]
        self.assertIn('password_sequential_letters', codes)

    def test_password_sequential_letters_descending(self):
        """Contraseña con secuencia alfabética descendente (dcba) debe fallar."""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate('Xdcba917!@zz')
        codes = [e.code for e in ctx.exception.error_list]
        self.assertIn('password_sequential_letters', codes)

    def test_password_non_sequential_letters_ok(self):
        """Contraseña con letras no secuenciales debe pasar."""
        self.validator.validate('Xpmrz9173!@w')  # No debe lanzar excepción

    # --- Tests de contraseña completamente válida ---
    def test_valid_strong_password(self):
        """Una contraseña fuerte que cumple todos los requisitos debe pasar."""
        self.validator.validate('M!p@ssW0rd#9x')  # No debe lanzar excepción

    def test_multiple_errors_at_once(self):
        """Una contraseña que falla en múltiples reglas debe reportar todos los errores."""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate('abc')  # Falla: corta, sin mayúscula, sin número, sin especial
        # Debe tener múltiples errores
        self.assertGreater(len(ctx.exception.error_list), 1)

    # --- Test de get_help_text ---
    def test_help_text(self):
        """Verificar que el texto de ayuda contiene las reglas."""
        help_text = self.validator.get_help_text()
        self.assertIn('12', help_text)
        self.assertIn('mayúscula', help_text)
        self.assertIn('minúscula', help_text)
        self.assertIn('número', help_text)
        self.assertIn('especial', help_text)


class MaximumLengthValidatorTests(TestCase):
    """Tests para el validador de longitud máxima."""

    def setUp(self):
        self.validator = MaximumLengthValidator(max_length=128)

    def test_password_within_max_length(self):
        """Contraseña dentro del límite máximo debe pasar."""
        self.validator.validate('A' * 128)  # No debe lanzar excepción

    def test_password_exceeds_max_length(self):
        """Contraseña que excede el límite máximo debe fallar."""
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.validator.validate('A' * 129)

    def test_help_text(self):
        """Verificar texto de ayuda del validador de longitud máxima."""
        help_text = self.validator.get_help_text()
        self.assertIn('128', help_text)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PasswordPolicyIntegrationTests(TestCase):
    """Tests de integración: política de contraseña en registro y reset."""

    def test_register_weak_password_fails(self):
        """Registro con contraseña débil debe fallar."""
        response = self.client.post(reverse('user:register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'simple',
            'password2': 'simple',
        })
        # No debe crear el usuario
        self.assertFalse(CustomUser.objects.filter(email='newuser@example.com').exists())

    def test_register_strong_password_succeeds(self):
        """Registro con contraseña fuerte debe funcionar."""
        self.client.post(reverse('user:register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'M!p@ssW0rd#9x',
            'password2': 'M!p@ssW0rd#9x',
        })
        self.assertTrue(CustomUser.objects.filter(email='newuser@example.com').exists())

    def test_password_reset_weak_password_fails(self):
        """Cambio de contraseña con contraseña débil debe fallar."""
        user = CustomUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='M!p@ssW0rd#9x',
            is_email_verified=True,
        )
        token = PasswordResetToken.objects.create(user=user)

        self.client.post(
            reverse('user:password_reset_confirm', kwargs={'token': token.token}),
            {
                'new_password1': 'weak',
                'new_password2': 'weak',
            }
        )

        # La contraseña no debe haber cambiado
        user.refresh_from_db()
        self.assertTrue(user.check_password('M!p@ssW0rd#9x'))

    def test_password_reset_strong_password_succeeds(self):
        """Cambio de contraseña con contraseña fuerte debe funcionar."""
        user = CustomUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='M!p@ssW0rd#9x',
            is_email_verified=True,
        )
        token = PasswordResetToken.objects.create(user=user)

        self.client.post(
            reverse('user:password_reset_confirm', kwargs={'token': token.token}),
            {
                'new_password1': 'N3w$ecureP@ss!',
                'new_password2': 'N3w$ecureP@ss!',
            }
        )

        user.refresh_from_db()
        self.assertTrue(user.check_password('N3w$ecureP@ss!'))