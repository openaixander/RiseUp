from django.contrib.auth.models import(
    AbstractBaseUser, BaseUserManager, PermissionsMixin
)
from django.db import models

# Create your models here.


from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
import uuid

# Custom User Manager

class CustomUserManager(BaseUserManager):
    """
    Custom manager for the CustomUser model where email is the unique identifier
    and username is automatically generated and required.
    """

    def _generate_unique_username(self, email):
        """
        Generates a unique username based on the email prefix.
        Appends numbers if the base username is already taken.
        """
        if not email:
            raise ValueError(_('Email must be provided to generate username'))
        
        base_username = email.split('@')[0]
        # clean username(allow letters, numbers, underscore)
        base_username = ''.join(filter(str.isalnum, base_username)) or 'user' # Fallback if email prefix is empty/invalid
        username = base_username
        counter = 1
        while self.model.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
            if counter > 1000: # Safety break
                 # Use UUID for very high collision cases or fallback
                 username = f"{base_username}_{uuid.uuid4().hex[:6]}"
                 # Re-check uniqueness of UUID-based username one last time
                 if self.model.objects.filter(username=username).exists():
                      raise SystemError("Failed to generate a unique username.") # Or handle differently

        return username


    def _create_user(self, email, password, username=None, **extra_fields):
        """
        Private helper method to create and save a user with the given details.
        Handles username generation if not provided.
        """
        if not email:
            raise ValueError(_('The Email Field must be set'))
        if not password:
            raise ValueError(_('The Password Field must be set'))
        
        email = self.normalize_email(email)


        if username is None:
            username = self._generate_unique_username(email)
        elif self.model.objects.filter(username=username).exists():
            # If username provided but already exists, try generating a unique one
            # Or raise an error depending on desired behavior
            # raise ValueError(_('Username already exists. Provide a unique one or let it be generated.'))
            username = self._generate_unique_username(email) # Attempt generation

        # Validate provided username format if needed
        # e.g., using validators=[...] on the model field

        user = self.model(
            email=email,
            username=username,
            **extra_fields
        )
        user.set_password(password) # Handles password hashing
        user.save(using=self._db)
        return user
    
    def create_user(self, email, password=None, username=None, **extra_fields):
        """
        Creates and saves a regular User with the given email, username (optional),
        first name, last name, and password.
        """
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', False)

        return self._create_user(email, password, username, **extra_fields)
    
    def create_superuser(self, email, password=None, username=None, **extra_fields):
        """
        Creates and saves a SuperUser with the given email, username (optional),
        first name, last name and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        # For createsuperuser command, explicitly require fields listed in REQUIRED_FIELDS
        # The command line will prompt for them if not provided here.
        # Username generation will happen if 'username' isn't provided via kwargs or prompt.

        return self._create_user(email, password, username, **extra_fields)
    

class Account(AbstractBaseUser, PermissionsMixin):
    """
    Custom User Model implementation.

    Uses Email as the unique identifier for authentication.
    Includes a unique, automatically generated username field.
    Contains standard fields like first_name, last_name, and admin flags.
    """



    # Define validators if needed, e.g., for username
    username_validator = RegexValidator(
        regex=r'^[a-zA-Z0-9_]+$', # Example: Alphanumeric + underscore
        message=_('Username must contain only letters, numbers, or underscores.'),
        code='invalid_username'
    )

    # core identification fields
    email = models.EmailField(
        _('email_address'),
        unique=True,
        db_index=True, #Index for faster lookups
        help_text=_('Required. Used for login and communication.'),
        error_messages={
            'unique': _("A user with that email already exists."),
        }
    )

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        db_index=True,
        validators=[username_validator], # Optional: Enforce format
        help_text=_('Required. 150 characters or fewer. Letters, digits and _ only.'),
         error_messages={
            'unique': _("A user with that username already exists."),
        }
    )


    first_name = models.CharField(
        _('first_name'),
        max_length=150,
    )
    last_name = models.CharField(
        _('last_name'),
        max_length=150,
    )


    is_staff = models.BooleanField(
        _('staff_status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )

    is_active = models.BooleanField(
        _('active'),
        default=False,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )

    date_joined = models.DateTimeField(_('date_joined'), default=timezone.now)


    objects = CustomUserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined', 'email'] # Example ordering

    def clean(self):
        """
        Normalize email address during model cleaning
        """
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user (usually first name)."""
        return self.first_name
    
    def __str__(self):
        """String representation of the user."""
        return self.email # Or self.username
    
    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?" #- Handled by PermissionsMixin
        # Simplest possible answer: Yes, always
        return True
    
    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?" #- Handled by PermissionsMixin
    #     # Simplest possible answer: Yes, always
        return True