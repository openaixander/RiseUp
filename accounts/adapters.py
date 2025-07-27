from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter for handling social account login and signup.
    """

    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a
        social provider, but before the login is actually processed.

        We use this to check if a user with the same email already exists.
        If so, we connect the social account to the existing user.
        """
        User = get_user_model()
        email = sociallogin.account.extra_data.get('email')

        if email:
            # Check if a user with this email already exists
            try:
                user = User.objects.get(email=email)

                # if the social is not already connected to the user
                if not sociallogin.is_existing:
                    # Connect the social account to the existing user
                    sociallogin.connect(request, user)
                    
            except User.DoesNotExist:
                # If no user exists, allow the signup to proceed
                pass
    
    def save_user(self, request, sociallogin, form=None):
        """
        Saves a new user instance when a user signs up via a social account.
        This method is overridden to use our custom user manager.
        """
        User = get_user_model()

        # Extact user data from the social account
        extra_data = sociallogin.account.extra_data
        email = extra_data.get('email')
        first_name = extra_data.get('given_name', '') or extra_data.get('first_name', '')
        last_name = extra_data.get('family_name', '') or extra_data.get('last_name', '')

        # fallback for Apple which provides name in a nested dict
        if 'name' in extra_data and isinstance(extra_data['name'], dict):
            first_name = first_name or extra_data['name'].get('firstName', '')
            last_name = last_name or extra_data['name'].get('lastName', '')

        
        if not email:
            # If the provider doesn't give an email, you might want to redirect
            # to a form where the user can enter one. For now, we'll raise an error.
            # You can customize this behavior.
            # For example, redirect to a custom form:
            # request.session['social_account_data'] = extra_data
            # return redirect(reverse('your_custom_email_form'))
            raise ValueError("Social account does not provide an email address.")
        

        # Use custom user manager to create the user
        user = User.objects.create_user(
            email=email,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            username=email,  # Use email as username
        )

        # Set the user to active immediately since they verified via social provider
        user.is_active = True
        user.save()

        # Connect the social account to the newly created user
        sociallogin.user = user
        sociallogin.save(request)

        return user
