import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class ISO27001PasswordValidator:
    """
    Validador de contraseñas basado en la política ISO 27001.
    
    Requisitos:
    - Mínimo 12 caracteres
    - Al menos 1 letra mayúscula
    - Al menos 1 letra minúscula
    - Al menos 1 número
    - Al menos 1 carácter especial (!@#$%^&*()_+-=[]{}|;:',.<>?/~`)
    - No puede contener más de 3 caracteres consecutivos iguales
    - No puede contener secuencias numéricas (123, 321)
    - No puede contener secuencias alfabéticas (abc, cba)
    """

    def __init__(self, min_length=12):
        self.min_length = min_length

    def validate(self, password, user=None):
        errors = []

        # Longitud mínima
        if len(password) < self.min_length:
            errors.append(
                ValidationError(
                    _('La contraseña debe tener al menos %(min_length)d caracteres.'),
                    code='password_too_short',
                    params={'min_length': self.min_length},
                )
            )

        # Al menos una mayúscula
        if not re.search(r'[A-Z]', password):
            errors.append(
                ValidationError(
                    _('La contraseña debe contener al menos una letra mayúscula (A-Z).'),
                    code='password_no_upper',
                )
            )

        # Al menos una minúscula
        if not re.search(r'[a-z]', password):
            errors.append(
                ValidationError(
                    _('La contraseña debe contener al menos una letra minúscula (a-z).'),
                    code='password_no_lower',
                )
            )

        # Al menos un número
        if not re.search(r'[0-9]', password):
            errors.append(
                ValidationError(
                    _('La contraseña debe contener al menos un número (0-9).'),
                    code='password_no_digit',
                )
            )

        # Al menos un carácter especial
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:\'",.<>?/~`\\]', password):
            errors.append(
                ValidationError(
                    _('La contraseña debe contener al menos un carácter especial (!@#$%%^&*...).'),
                    code='password_no_special',
                )
            )

        # No más de 3 caracteres consecutivos iguales (aaaa, 1111)
        if re.search(r'(.)\1{3,}', password):
            errors.append(
                ValidationError(
                    _('La contraseña no puede contener más de 3 caracteres consecutivos iguales.'),
                    code='password_repeated_chars',
                )
            )

        # No secuencias numéricas ascendentes o descendentes (1234, 4321)
        if self._has_sequential_chars(password, sequence_type='digits'):
            errors.append(
                ValidationError(
                    _('La contraseña no puede contener secuencias numéricas (ej: 1234 o 4321).'),
                    code='password_sequential_digits',
                )
            )

        # No secuencias alfabéticas ascendentes o descendentes (abcd, dcba)
        if self._has_sequential_chars(password, sequence_type='letters'):
            errors.append(
                ValidationError(
                    _('La contraseña no puede contener secuencias alfabéticas (ej: abcd o dcba).'),
                    code='password_sequential_letters',
                )
            )

        if errors:
            raise ValidationError(errors)

    def _has_sequential_chars(self, password, sequence_type='digits', seq_length=4):
        """
        Detecta secuencias ascendentes o descendentes de caracteres.
        """
        chars = password.lower() if sequence_type == 'letters' else password

        for i in range(len(chars) - seq_length + 1):
            substring = chars[i:i + seq_length]

            if sequence_type == 'digits' and not substring.isdigit():
                continue
            if sequence_type == 'letters' and not substring.isalpha():
                continue

            # Verificar secuencia ascendente
            is_ascending = all(
                ord(substring[j + 1]) - ord(substring[j]) == 1
                for j in range(len(substring) - 1)
            )
            # Verificar secuencia descendente
            is_descending = all(
                ord(substring[j]) - ord(substring[j + 1]) == 1
                for j in range(len(substring) - 1)
            )

            if is_ascending or is_descending:
                return True

        return False

    def get_help_text(self):
        return _(
            'Tu contraseña debe cumplir con la política de seguridad ISO 27001:\n'
            '• Mínimo %(min_length)d caracteres\n'
            '• Al menos 1 letra mayúscula (A-Z)\n'
            '• Al menos 1 letra minúscula (a-z)\n'
            '• Al menos 1 número (0-9)\n'
            '• Al menos 1 carácter especial (!@#$%%^&*...)\n'
            '• Sin más de 3 caracteres iguales consecutivos\n'
            '• Sin secuencias numéricas o alfabéticas (1234, abcd)'
        ) % {'min_length': self.min_length}


class MaximumLengthValidator:
    """
    Validador que limita la longitud máxima de la contraseña.
    Previene ataques DoS por contraseñas extremadamente largas.
    """

    def __init__(self, max_length=128):
        self.max_length = max_length

    def validate(self, password, user=None):
        if len(password) > self.max_length:
            raise ValidationError(
                _('La contraseña no puede tener más de %(max_length)d caracteres.'),
                code='password_too_long',
                params={'max_length': self.max_length},
            )

    def get_help_text(self):
        return _(
            'Tu contraseña no puede tener más de %(max_length)d caracteres.'
        ) % {'max_length': self.max_length}
