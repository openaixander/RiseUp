from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.views import PasswordResetView

from .models import Account
from .forms import RegistrationForm
from .utils import decode_uid
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from .tasks import send_activation_email_task, send_password_reset_email_task
import logging

# this imports are for the authentication stuff
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.forms.forms import NON_FIELD_ERRORS
from django.conf import settings



logger = logging.getLogger(__name__)

# Create your views here.
def register(request):
    """
    Handles user registration requests.
    GET: Displays the registration form.
    POST: Processes form submission, validates data, saves user (inactive),
          and sends activation email.
    """
    if request.method == 'POST':
        # Create a form instance with the submitted data
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Save the user form (creates an inactive user)
                user = form.save()
                
                # Get the email from cleaned data
                email = form.cleaned_data.get('email')
                
                # get domain for the task
                current_site = get_current_site(request)
                domain = current_site.domain

                # Pass user's primary key (serializable) and domain string
                send_activation_email_task.delay(user.pk, email, domain)
                
                # Add a success message for the user
                # messages.success(request, 'Registration successful! Please check your email to activate your account.')
                return redirect('/accounts/login/?command=verification&email='+email)
            
            except Exception as e:
                # Handle potential errors during user saving or email sending
                print(f"Error during registration (user save phase): {e}") 
                logger.error(f"Error saving user during registration: {e}", exc_info=True) # Use logger
                messages.error(request, 'An error occurred during registration. Please try again.')
                return render(request, 'accounts/registration.html', {'form': form})

        else:
            # Form is not valid, render the page again with the form instance
            # This form instance will contain validation errors
            messages.error(request, 'Please correct the errors below.')
            return render(request, 'accounts/registration.html', {'form': form})
            
    else: # GET request
        # Create an empty form instance
        form = RegistrationForm()
        
    # Render the registration template with the form
    context = {'form': form}
    return render(request, 'accounts/registration.html', context)


# the activation view 

def activate(request, uidb64, token):
    """
    Activates the user account based on the UID and token from the email link.
    Handles already active accounts and invalid links.
    """
    try:
        # decode the uid to get the user's primary key
        uid = decode_uid(uidb64)

        if uid is None:
            raise ValueError("Invalid UID encoding")
        
        # time to retrieve the user with it primary key
        user = Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist, Exception) as e:
    # Handle cases where UID is invalid or user doesn't exist
        print(f"Activation error - User/UID lookup failed: {e}") # Log the error
        user = None


    #  it checks if the user exists, token is valid, and account is not already active
    if user is not None and default_token_generator.check_token(user, token):
        if not user.is_active:
            # activate the user account
            user.is_active = True
            user.save()
            messages.success(request, 'Congratulations! Your account has been activated successfully. You can now log in.')
            logger.info(f"Account activated successfully for user {user.pk}")
        else:
            # Account was already active
            messages.info(request, 'This account has already been activated. Please log in.')
            logger.info(f"Attempt to activate already active account for user {user.pk}")
        
        # Redirect to the login page after successful activation or if already active
        return redirect(reverse('accounts:login'))

    else:
        # Activation link is invalid (user not found or token mismatch)
        messages.error(request, 'The activation link is invalid or has expired.')
        logger.warning(f"Invalid activation attempt. UIDb64: {uidb64}, Token: {token}")
        # Redirect to the registration page or login page
        return redirect(reverse('accounts:register'))


def login_view(request):
    """
    Handles user login attempts, redirection for authenticated users,
    and displays appropriate validation errors, including for inactive accounts.

    Args:
        request: HttpRequest object.

    Returns:
        HttpResponse object (renders login template or redirects).
    """
    # --- Pre-computation and Initial Checks ---

    # Redirect authenticated users immediately
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        logger.debug(f"Authenticated user {request.user.email} redirected from login page.")
        return redirect(settings.LOGIN_REDIRECT_URL)

    # Determine where to redirect after successful login
    # Check 'next' in POST data first (if form submitted), then GET data
    next_url = request.POST.get('next', request.GET.get('next', ''))
    # Use the 'next' URL if provided, otherwise default to LOGIN_REDIRECT_URL
    redirect_to = next_url or settings.LOGIN_REDIRECT_URL

    # Initialize form variable - will hold either empty form (GET) or submitted form (POST)
    form = None

    # --- Handle POST Request (Login Attempt) ---
    if request.method == 'POST':
        # Instantiate the AuthenticationForm with request and submitted data
        form = AuthenticationForm(request, data=request.POST)

        # Validate the form: checks credentials and user.is_active
        if form.is_valid():
            # Form is valid: User authenticated and active
            user = form.get_user()
            auth_login(request, user) # Create the user's session
            logger.info(f"User '{user.email}' logged in successfully.")
            # Optional: Add a welcome message
            # messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect(redirect_to) # Redirect to dashboard or 'next' URL
        else:
            # Form is invalid: Handle errors (wrong password, inactive user, etc.)
            logger.warning(f"Login form invalid for username/email: {request.POST.get('username')}")
            # Log the specific reason if possible (optional detail)
            non_field_errors = form.errors.get(NON_FIELD_ERRORS)
            if non_field_errors and any(e.code == 'inactive' for e in non_field_errors.as_data()):
                 logger.warning(f"Login failure reason: Inactive account ({request.POST.get('username')})")
            else:
                 logger.warning(f"Login failure reason: Invalid credentials ({request.POST.get('username')})")
            
            # *** Important: DO NOT add messages here using django.contrib.messages ***
            # The AuthenticationForm itself adds the appropriate error message 
            # (e.g., "This account is inactive." or "Please enter a correct email...")
            # to form.non_field_errors. We will let the template render these form errors.

    # --- Handle GET Request or Prepare Form for Re-rendering after Invalid POST ---
    else: # request.method == 'GET'
        # Create an empty form instance for the initial page load
        form = AuthenticationForm(request)

    # This section is reached for GET requests OR after an invalid POST attempt.
    # The 'form' variable will either be an empty form or the invalid form with errors.
    context = {
        'form': form,
        'next': next_url, # Pass 'next' value for the hidden form field
    }
    return render(request, 'accounts/login.html', context)


def logout_view(request):
    """ Logs the user out and redirects to the login page. """
    if request.user.is_authenticated:
        user_email = request.user.email
        auth_logout(request)
        messages.success(request, 'You have successfully logged out.')
        logger.info(f"User '{user_email}' logged out successfully.")
    else:
         messages.info(request, 'You were not logged in.') # Optional message if accessed while not logged in
         
    return redirect(reverse('accounts:login')) # Redirect to login page


class CustomPasswordResetView(PasswordResetView):
    """
    Overrides form_valid to send the password reset email via Celery task
    instead of synchronously.
    """
    def form_valid(self, form):
        """
        Generates context, options and calls the Celery task to send mail.
        Then redirects to the success URL.
        """
        try:
            opts = {
                'use_https': self.request.is_secure(),
                'token_generator':self.token_generator,
                'from_email': self.from_email,
                'email_template_name': self.get_email_template_name(),
                'subject_template_name': self.get_subject_template_name(),
                'request': self.request,
                # Include domain and site_name in the context
                'domain_override': self.request.get_host(), # Get current host
                'extra_email_context': self.get_extra_email_context(),

            }

            email = form.cleaned_data["email"]
            # gets the email of the matching user
            user_generator = form.get_users(email)
            
            # assuming only one user per email, get the first one
            active_user = next(user_generator)
            context_for_task = {
                'domain': get_current_site(self.request).domain, # Pass domain string
                'site_name': get_current_site(self.request).name, # Pass site name string
                'uidb64': urlsafe_base64_encode(force_bytes(active_user.pk)),
                'token': opts['token_generator'].make_token(active_user),
                'protocol': 'https' if opts['use_https'] else 'http',
                **(opts['extra_email_context'] or {}),
            }


            # call the celery task
            send_password_reset_email_task.delay(
                user_pk=active_user.pk,
                subject_template_name=opts['subject_template_name'],
                email_template_name=opts['email_template_name'],
                context=context_for_task,
                from_email=opts['from_email'],
                to_email=active_user.email
            )
            logger.info(f"Password reset email task queued for {active_user.email}")
        
        except Exception as e:
            logger.error(f"Error preparing password reset email for {email}: {e}", exc_info=True)
            messages.error(self.request, "An error occurred while requesting the password reset. Please try again later.")
            # Redirect back to the form or show a generic error
            return self.form_invalid(form) # Or redirect to success_url to not reveal email validity? Check security implications. Let's redirect for now.
            
        # Redirect to the success page (password_reset_done)
        return redirect(self.get_success_url())


    def get_email_template_name(self):
    # Helper to get template name potentially overridden in urls.py or class attribute
        return self.email_template_name

    def get_subject_template_name(self):
        # Helper
        return self.subject_template_name

    def get_extra_email_context(self):
        # Helper
        return self.extra_email_context
