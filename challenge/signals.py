from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings # To check if the sender is the User model if needed
from .models import DailyLog # The model whose save triggers the check
from .utils import check_and_award_achievements # Import the checking function
import logging


logger = logging.getLogger(__name__)


# This receiver function will run *after* a DailyLog instance is saved
@receiver(post_save, sender=DailyLog)
def daily_log_post_save(sender, instance, created, **kwargs):
    """
    Check for achievements after a DailyLog is saved.
    'instance' is the DailyLog object that was just saved.
    'created' is True if a new record was created, False if updated.
    """

    user = instance.user
    logger.debug("Signal Triggered:Dailylog saved for user %s", user.username)

    try:
        # Call the central checking function for the user associated with the log
        check_and_award_achievements(user)
    except Exception as e:
        # Log any errors during the check to avoid breaking the save operation
        logger.error(f"Error in check_and_award_achievements signal for user {user.email}: {e}", exc_info=True)

