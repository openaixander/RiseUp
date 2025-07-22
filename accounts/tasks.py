from celery import shared_task
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
import logging

from django.conf import settings


from .models import Account

# instance of a logger

logger = logging.getLogger(__name__)


# use shared_task decorator for tasks reusable across apps
@shared_task(bind=True, default_retry_delay=30, max_retries=3)
def send_activation_email_task(self, user_pk, email, domain):
    """
    Celery task to send the activation email asynchronously.
    Includes retry logic.

    Args:
        self (celery.Task): The task instance (available via bind=True).
        user_pk (int): Primary key of the user account.
        email (str): The email address to send to.
        domain (str): The domain of the current site.
    """

    try:
        # retrieve the user object from the database using the primary key
        user = Account.objects.get(pk=user_pk)

        mail_subject = 'Please activate your account.'

        # Use the domain passed as an argument
        context = {
            'user': user,
            'domain': domain, # Use the passed domain string
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
            'protocol': 'http' if 'localhost' not in domain else 'https', # Determine protocol dynamically or pass it
        }

        # Render the email body from the template
        message = render_to_string('accounts/account_verification_email.html', context)

        # Create the EmailMessage object
        email_message = EmailMessage(mail_subject, message, to=[email])
        email_message.content_subtype = "html"

        # fire the email
        email_message.send()
        logger.info(f"Activation email sent successfully to {email} for user {user_pk}")
        return f"Activation email sent to {email}"
    
    except Account.DoesNotExist:
        logger.error(f"Cannot send activation email: User with pk={user_pk} not found.")
        # Do not retry if user doesn't exist
        return f"Failed: User {user_pk} not found."
    
    except Exception as exc:
        # log the exception
        logger.error(f"Error sending activation email to {email} for user {user_pk}: {exc}", exc_info=True)

        # Retry the task using Celery's built-in mechanism
        # self.retry() will re-queue the task based on decorator settings
        # (default_retry_delay, max_retries)
        # The 'exc' argument passes the exception for logging/debugging in Celery
        try:
            self.retry(exc=exc)
        except Exception as retry_exc:
            logger.error(f"Failed to retry task for user {user_pk} after exception: {retry_exc}")
            return f"Failed to send/retry email for user {user_pk}."
        

@shared_task(bind=True, default_retry_delay=2, max_retries=3)
def send_password_reset_email_task(self, user_pk, subject_template_name, email_template_name, context, from_email, to_email):
    """
    Celery task to send password reset email asynchronously.
    """

    logger.info(f"Executing password reset task for user PK: {user_pk}, email: {to_email}")
    try:
        # --- Retrieve user object inside the task ---
        try:
            user = Account.objects.get(pk=user_pk)
            logger.debug(f"Found user: {user.email} for PK: {user_pk}")
        except Account.DoesNotExist:
            # If user was deleted between view and task execution
            logger.warning(f"Password reset email task: User with pk={user_pk} not found. Aborting task.")
            return f"User {user_pk} not found."
        # --- End Retrieve user ---

        # --- Add the fetched user object to the context ---
        # The email template needs access to the user object (e.g., user.first_name)
        context['user'] = user
        context['email'] = user.email # Ensure email is in context if template uses it directly
        # --- End Add user ---
        logger.debug(f"Context for rendering email templates: {context}")

        # Render email subject
        subject = render_to_string(subject_template_name, context)
        subject = ''.join(subject.splitlines())
        logger.debug(f"Rendered subject: {subject}")

        # Render email body
        body = render_to_string(email_template_name, context)
        # logger.debug(f"Rendered body: {body}") # Can be very long

        # Create EmailMessage
        email_message = EmailMessage(
            subject,
            body,
            from_email or settings.DEFAULT_FROM_EMAIL,
            [to_email] # Ensure it's a list
        )
        email_message.content_subtype = "html"
        # Send the email
        email_message.send()
        logger.info(f"Password reset email sent successfully to {to_email} (User PK: {user_pk})")
        return f"Password reset email sent to {to_email}"

    # Catch specific exceptions if needed, e.g., template rendering errors
    except Exception as exc:
        logger.error(f"Error sending password reset email to {to_email} (User PK: {user_pk}): {exc}", exc_info=True)
        try:
            # Retry the task according to decorator settings
            self.retry(exc=exc)
        except Exception as retry_exc:
             logger.error(f"Failed to retry password reset task for {to_email} (User PK: {user_pk}) after exception: {retry_exc}")
             # Decide if you want to raise the retry_exc or just return a failure message
             return f"Failed to send/retry password reset email for {to_email}."