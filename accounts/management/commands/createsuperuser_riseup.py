import os
import sys
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import DEFAULT_DB_ALIAS

class Command(BaseCommand):
    help = 'Creates a superuser, and allows setting a password in a single command.'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.UserModel = get_user_model()
        self.username_field = self.UserModel._meta.get_field(self.UserModel.USERNAME_FIELD)

    def add_arguments(self, parser):
        parser.add_argument(
            f'--{self.UserModel.USERNAME_FIELD}',
            dest=self.UserModel.USERNAME_FIELD,
            required=True,
            help='Specifies the login for the superuser.',
        )
        parser.add_argument(
            '--password',
            dest='password',
            help='Specifies the password for the superuser. If not provided, it will be prompted for.',
        )
        # Add arguments for all other required fields
        for field_name in self.UserModel.REQUIRED_FIELDS:
            parser.add_argument(
                f'--{field_name}',
                dest=field_name,
                required=True,
                help=f'Specifies the {field_name} for the superuser.',
            )

    def handle(self, *args, **options):
        database = options.get('database', DEFAULT_DB_ALIAS)
        password = options.get('password')
        email = options[self.UserModel.USERNAME_FIELD]
        
        user_data = {
            self.UserModel.USERNAME_FIELD: email,
            'password': password
        }

        # Collect data for required fields
        for field_name in self.UserModel.REQUIRED_FIELDS:
            user_data[field_name] = options[field_name]

        # Use the custom manager's create_superuser method
        try:
            self.UserModel._default_manager.db_manager(database).create_superuser(**user_data)
            self.stdout.write(self.style.SUCCESS(f"Superuser '{email}' created successfully."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error creating superuser: {e}"))
            sys.exit(1)