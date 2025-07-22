from django import forms
from django.contrib.auth.forms import SetPasswordForm
from django.utils.translation import gettext_lazy as _
from .models import Account, UserProfile
import pytz


class RegistrationForm(forms.ModelForm):
    """
    Form for the user registration. Includes password confirmation and terms agreement.
    """
    # password field with passwordInput widget for hiding input
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': ' ',# For floating label
            'class': 'form-control form-control-lg',
            'id':'password'
        }),
        label="Password"
    )

    # confirm password field, also using PasswordInput
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': ' ',
            'class': 'form-control form-control-lg',
            'id': 'confirmPassword', # Match template id
        }),
        label="Confirm Password"
    )

    terms = forms.BooleanField(
        required=True,
        error_messages={
            'required':'You must agree to the terms and conditions.'
        },
        widget=forms.CheckboxInput(
            {
                'class': 'form-check-input',
                'id': 'terms'
            }
        )
    )

    class Meta:
        model = Account
        # fields from the Account model to include in the form
        fields = ['first_name', 'last_name', 'email']

        # define widgets and attributes for model fields to match the html structure
        widgets = {
            'first_name': forms.TextInput(attrs={
                'placeholder': ' ',
                'class': 'form-control form-control-lg',
                'id':'firstName',
            }),

            'last_name': forms.TextInput(attrs={
                'placeholder': ' ',
                'class': 'form-control form-control-lg',
                'id':'lastName',
            }),

            'email': forms.TextInput(attrs={
                'placeholder': ' ',
                'class': 'form-control form-control-lg',
                'id':'email',
            }),
        }

        # Define labels for model fields if needed (floating labels handle this visually)
        labels = {
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'email': 'Email Address',
        }

    # defining the clean method
    def clean(self):
        """
        Custom validation method to check if passwords match
        """
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if  password != confirm_password:
            # Raise a validation error if passwords dont match
            raise forms.ValidationError("Password do not match.")
        
        if len(password) < 8:
            raise forms.ValidationError('Password must be atleast 8 characters long.')
        
        # ensure the base class clean method is called

        return cleaned_data
    
    def save(self, commit=True):
        """
        Creates the user using the CustomUserManager's create_user method
        to ensure username generation and password hashing occur correctly.
        """
        email = self.cleaned_data.get('email')
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')
        password = self.cleaned_data.get('password')


        if not (email and first_name and last_name and password):
            # Should ideally be caught by form validation, but good safeguard
             raise ValueError("Required fields are missing to create a user.")
        
        # we need to pass whatever data we got from the field to equate it,
        # with what is in the db

        user = Account.objects.create_user(
            email = email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        return user


# ... (Keep other forms like RegistrationForm, LoginForm, etc. if you have them) ...

class CustomSetPasswordForm(SetPasswordForm):
    """
    A custom SetPasswordForm that removes the default help text 
    explaining password validation rules, while keeping the validation active.
    """
    def __init__(self, *args, **kwargs):
        # Initialize the parent form first
        super().__init__(*args, **kwargs)
        
        # Access the new_password1 field instance after initialization
        # and remove its help text so it doesn't render in the template.
        # The actual validation defined in settings.AUTH_PASSWORD_VALIDATORS
        # will still be performed when the form is cleaned.
        if 'new_password1' in self.fields:
            self.fields['new_password1'].help_text = None 

class UserProfileForm(forms.ModelForm):
    """
    Handles updates for UserProfile fields and specific Account fields (username, names).
    """

    username = forms.CharField(
        label=_("Username/Display Name"),
        max_length=150,
        validators=[Account.username_validator], # Use validator from Account model
        required=True,
        help_text=_('Required 150 characters or fewer. Letters, digits and _ only'),
        widget=forms.TextInput(attrs={
            'class':'form-control'
        })
    )

    first_name = forms.CharField(label=_("First Name"), max_length=150, required=False, widget=forms.TextInput(attrs={
            'class':'form-control'
        }))
    last_name = forms.CharField(label=_("Last Name"), max_length=150, required=False, widget=forms.TextInput(attrs={
            'class':'form-control'
        }))

    class Meta:
        model = UserProfile
        fields = ['avatar', 'post_anonymously', 'default_challenge_length', 'enable_global_reminders', 'timezone']


    class Meta:
        model = UserProfile
        fields = [
            'avatar',
            'post_anonymously',
            'default_challenge_length',
            'enable_global_reminders',
        ]

        # define the widgets that match the template
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={
                'accept':'image/*',
                'id': 'avatarUpload',
                'class': 'form-control avatar-upload visually-hidden',
            }),
            'post_anonymously':forms.CheckboxInput(attrs={
                'role': 'switch',
                'id': 'hideUsername',
                'class': 'form-check-input',
            }),
            'default_challenge_length': forms.Select(attrs={
                'class':'form-select',
                'id':'defaultChallenge'
            }),
            'enable_global_reminders':forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role':'switch',
                'id':'dailyCheckin'
            }),
        }

        labels = {
            'post_anonymously':_('Hide my username from public spaces'),
            'enable_global_reminders': _('Enable Daily Check-in Notifications'),
            'default_challenge_length': _('Default Challenge Length'),
        }

        # define help texts explicitly if they differ from model help_text
        help_texts = {
            'post_anonymously': _('Your posts will show as "Anonymous" in public community sections.'),
            'enable_global_reminders': _('Master switch for daily check-in email reminders.'),
            'default_challenge_length': _('Set your preferred default duration (in days) when creating new challenges.'),
        }


    def __init__(self, *args, **kwargs):
        """
        Initialize the form, populating Account fields from the user instance.
        """
        # pop the user instance passed from the view
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)


        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['avatar'].initial = self.instance.avatar
            self.fields['username'].initial = self.user.username



    def clean_username(self):
        """
        Validate that the username is unique, excluding the current user.
        """
        username = self.cleaned_data['username']
        if not self.user:
            # This should not happen if the form is instantiated correctly in the view
            raise forms.ValidationError("User context is missing.")
        
        # check if another user already has this username
        if Account.objects.filter(username=username).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError(_("This username is already taken. Please choose another."))
        return username
    
    def save(self, commit=True):
        """
        Save changes to both UserProfile (instance) and the related Account (self.user).
        """
        # profile holds the Userprofile instance
        profile = super().save(commit=False)

        # Update the fields 
        if self.user:
            self.user.username = self.cleaned_data['username']
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            
            if commit:
                self.user.save()

        if commit:
            profile.save()

        return profile
    

class AccountDeleteForm(forms.Form):
    """
    Form requiring email and password confirmation for account deletion.
    """
    email_confirm = forms.EmailField(
        label="Type your email to confirm",
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'id': 'deleteConfirmEmail'})
    )

    password_confirm = forms.CharField(
        label="Enter your password to confirm",
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'deletePasswordConfirm'})
    )


    def __init__(self, *args, **kwargs):
        # Get the user instance passed from the view
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    
    def clean_email_confirm(self):
        """Checks if the entered email matches the user's current email."""
        email = self.cleaned_data.get('email_confirm')
        if not self.user:
            raise forms.ValidationError("User context missing.") # Should be passed from view
        # Use normalized email for comparison if necessary
        if email.lower() != self.user.email.lower():
            raise forms.ValidationError("Email does not match the account email.")
        return email

    def clean_password_confirm(self):
        """Checks if the entered password is correct."""
        password = self.cleaned_data.get('password_confirm')
        if not self.user:
             raise forms.ValidationError("User context missing.")
        if not self.user.check_password(password):
            raise forms.ValidationError("Incorrect password.")
        return password # Password is valid, but don't return it from clean method




