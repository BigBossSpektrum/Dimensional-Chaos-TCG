import os

from django.apps import AppConfig

# Comandos de gestión que no deben arrancar el scheduler
_SKIP_COMMANDS = {
    'migrate', 'makemigrations', 'test', 'shell', 'dbshell',
    'collectstatic', 'createsuperuser', 'fetch_all_cards', 'check',
}


class ApiYugiohConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_yugioh'

    def ready(self):
        import sys

        # No arrancar el scheduler durante comandos de gestión
        if len(sys.argv) > 1 and sys.argv[1] in _SKIP_COMMANDS:
            return

        # En runserver con autoreload Django lanza dos procesos:
        # el padre (vigilante de archivos) y el hijo (RUN_MAIN=true, el servidor real).
        # Solo arrancar en el hijo para evitar duplicados.
        # En producción (gunicorn, etc.) RUN_MAIN no está definido, así que también arranca.
        if os.environ.get('RUN_MAIN') == 'false':
            return

        from . import scheduler
        scheduler.start()
