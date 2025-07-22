from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Challenge
from accounts.models import Account

from django.db.models.functions import ExtractHour, ExtractMinute
import logging


logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_checkin_reminder(self, challenge_id):
    """
    sends a check-in reminder email for a specific challenge
    """

    try:
        # retrieve the challenge, ensuring it's still valid for reminders
        challenge = Challenge.objects.get(
            pk=challenge_id,
            is_active=True,
            enable_daily_reminder=True
        )

        user = challenge.user #get the related user 


        subject = f"Reminder: Check-in for '{challenge.name}'"

        message = f"Hi {user.first_name or user.username}, \n\n" \
                  f"This is your friendly reminder to check in for your challenge: {challenge.name}. \n\n" \
                  f"Keep up the great work!\n\n" \
                  f"Your RiseUp Team" #Customize as needed
        
        receipient_list = [user.email]


        # send the email using django's send_mail
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list=receipient_list,
            fail_silently=False
        )

        logger.info(f"Successfully sent check-in reminder for challenge {challenge_id} to {user.email}")
        return f"Reminder sent for challenge {challenge_id}"

    except Challenge.DoesNotExist:
        # Challenge might have been deleted or deactivated since scheduling
        logger.warning(f"Challenge {challenge_id} not found or no longer valid for reminder task.")
        # No retry needed if the challenge doesn't exist
        return f"Challenge {challenge_id} not found or invalid."
    except Exception as exc:
        # Handle other potential errors (e.g., email sending failure)
        logger.error(f"Error sending reminder for challenge {challenge_id}: {exc}")
        # Retry the task after a delay (e.g., 60 seconds)
        self.retry(exc=exc, countdown=60)


@shared_task
def queue_reminders(self):
    """
    Checks for challenges needing reminders at the current time and queues them.
    This task is intended to be run frequently by Celery Beat (e.g., every minute).
    """
    now = timezone.now()
    current_hour = now.hour
    current_minute = now.minute

    logger.info(f"Running queue_reminders at {now.strftime('%Y-%m-%d %H:%M:%S %Z')}. Checking for reminders matching {current_hour:02d}:{current_minute:02d}.")

    target_challenges = Challenge.objects.filter(
        is_active=True,
        enable_daily_reminder=True,
        reminder_time__hour=current_hour,
        reminder_time__minute=current_minute
    )

    queued_count = 0

    for challenge in target_challenges:
        logger.info(f"Queueing reminder for Challenge ID: {challenge.id} for user {challenge.user.email} at {challenge.reminder_time.strftime('%H:%M')}")
        # Queue the actual email sending task
        send_checkin_reminder.delay(challenge.id)
        queued_count+=1

    logger.info(f"Finished queue_reminders. Queued {queued_count} reminder tasks.")
    return f"Queued {queued_count} reminders for {current_hour:02d}:{current_minute:02d}."
                