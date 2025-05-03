# kuhl_haus/magpie/web/management/commands/bootstrap.py
import os

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.conf import settings

from kuhl_haus.magpie.web.settings import (
    DJANGO_SUPERUSER_USERNAME,
    DJANGO_SUPERUSER_EMAIL,
    DJANGO_SUPERUSER_PASSWORD,
)


class Command(BaseCommand):
    help = 'Bootstrap the application (initialize database and create superuser)'

    def handle(self, *args, **options):
        self.stdout.write('Initializing database...')
        call_command('makemigrations', interactive=False)

        self.stdout.write("Running Django migrations...")
        call_command('migrate', interactive=False)

        static_dir = settings.STATIC_ROOT
        if not os.path.exists(static_dir):
            os.mkdir(static_dir)

        self.stdout.write("Initializing Django static files...")
        call_command('collectstatic', interactive=False)

        self.stdout.write('Creating superuser...')
        self._create_default_superuser()

        self.stdout.write(self.style.SUCCESS('Bootstrap complete'))

    def _create_default_superuser(self):
        """
        Create a default superuser from environment variables if one doesn't exist.

        Environment variables:
        - DJANGO_SUPERUSER_USERNAME: Username for the superuser (default: admin)
        - DJANGO_SUPERUSER_EMAIL: Email for the superuser (default: admin@example.com)
        - DJANGO_SUPERUSER_PASSWORD: Password for the superuser (required)
        """
        from django.contrib.auth.models import User

        if not DJANGO_SUPERUSER_PASSWORD:
            self.stdout.write("DJANGO_SUPERUSER_PASSWORD not set. Skipping superuser creation.")
            return

        try:
            if not User.objects.filter(username=DJANGO_SUPERUSER_USERNAME).exists():
                User.objects.create_superuser(DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD)
                self.stdout.write(f"Superuser '{DJANGO_SUPERUSER_USERNAME}' created successfully")
            else:
                self.stdout.write(f"Superuser '{DJANGO_SUPERUSER_USERNAME}' already exists")
        except Exception as e:
            self.stdout.write(f"Failed to create superuser: {e}")
