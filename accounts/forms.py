from django import forms
from django.contrib.auth.forms import SetPasswordForm
from .models import Account


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