# your_app/management/commands/create_custom_superuser.py

import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

class Command(BaseCommand):
    """
    Custom Django command to create a superuser non-interactively.

    This command is designed for deployment environments like Render where you
    can set environment variables for the superuser's credentials. It uses
    the custom user model and manager you've defined.

    Reads the following environment variables:
    - SUPERUSER_EMAIL
    - SUPERUSER_PASSWORD
    - SUPERUSER_FIRST_NAME
    - SUPERUSER_LAST_NAME
    """
    help = 'Creates a superuser non-interactively from environment variables.'

    def handle(self, *args, **options):
        """
        The main logic of the command.
        """
        User = get_user_model()  # Gets your custom 'Account' model

        # --- Get credentials from environment variables ---
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        first_name = os.environ.get('DJANGO_SUPERUSER_FIRST_NAME')
        last_name = os.environ.get('DJANGO_SUPERUSER_LAST_NAME')

        # --- Validate that all required variables are set ---
        if not all([email, password, first_name, last_name]):
            self.stdout.write(self.style.ERROR(
                'Missing one or more required environment variables: '
                'DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD, DJANGO_SUPERUSER_FIRST_NAME, DJANGO_SUPERUSER_LAST_NAME'
            ))
            # Exit the command gracefully if variables are missing
            return

        # --- Check if a user with that email already exists ---
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(
                f'A user with the email "{email}" already exists. Skipping superuser creation.'
            ))
            return

        # --- Create the superuser ---
        try:
            self.stdout.write(f'Creating superuser for email: {email}...')

            # Your CustomUserManager's create_superuser method will be called here.
            # It will handle username generation automatically based on your logic.
            User.objects.create_superuser(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            self.stdout.write(self.style.SUCCESS(
                f'Successfully created superuser: {email}'
            ))

        except ValidationError as e:
            # Handle potential validation errors from the model
            self.stdout.write(self.style.ERROR(
                f'Validation Error: Could not create superuser. {e}'
            ))
        except Exception as e:
            # Handle other potential errors
            self.stdout.write(self.style.ERROR(
                f'An unexpected error occurred: {e}'
            ))

