from django.db import models
from accounts.models import Account
import datetime
from django.utils import timezone
from django.core.exceptions import ValidationError
# Create your models here.


class Challenge(models.Model):
    """
    Represents a specific challenge a user undertakes.
    Includes notification preferences specific to this challenge.
    """
    user = models.ForeignKey(
        Account, 
        on_delete=models.CASCADE,
        related_name='challenges',
        help_text="The user who initated this challenge."
    )

    name = models.CharField(
        max_length=200,
        help_text="The name or title of the challenge",
    )

    start_date = models.DateField(
        help_text="The date the challenge officially began."
    )

    duration_days = models.PositiveIntegerField(
        help_text="The total duration of the challenge in days"
    )

    is_active = models.BooleanField(
        default=True, #usually, a newly created challenge becomes the active one
        help_text="Is this the user's current, current challenge?" 
    )

    enable_daily_reminder = models.BooleanField(
        default=True,
        help_text="Should daily check-in reminders be sent for this challenge?"
    )

    reminder_time = models.TimeField(
        null=True,
        blank=True,
        default="12:00:00",
        help_text="Preferred time for the daily check-in reminder"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)


    @property
    def end_date(self):
        """Calculates the end date of the challenge."""
        if self.start_date and self.duration_days:
            return self.start_date + datetime.timedelta(days=self.duration_days - 1)
        return None
    
    @property
    def current_day_number(self):
        """Calculates the current day number within the challenge duration."""
        today = timezone.now().date()
        if not self.is_active or not self.start_date or today < self.start_date:
            return 0
        
        days_passed = (today - self.start_date).days + 1

        return min(days_passed, self.duration_days) if self.duration_days else days_passed
    

    @property
    def progress_percentage(self):
        """Calculates the completion percentage of the challenge."""
        if not self.duration_days or self.duration_days == 0:
            return 0

        percentage = (self.current_day_number / self.duration_days) * 100
        return min(percentage, 100)
    
    def clean(self):
        """
        Ensures that a user can only have one active challenge at a time.
        Also ensure reminder time is cleared if reminders are disabled.
        """
        if hasattr(self, 'user') and self.user is not None and self.is_active:
            active_challenges = Challenge.objects.filter(
                user=self.user, 
                is_active=True
            ).exclude(pk=self.pk if self.pk else None)
            
            if active_challenges.exists():
                raise ValidationError(f"{self.user} already has an active challenge. Please deactivate it before activating a new one.")
        
        if not self.enable_daily_reminder:
            self.reminder_time = None

        # Use localized time for date comparison
        if self.start_date:
            current_date = timezone.localtime(timezone.now()).date()
            if self.start_date > current_date:
                raise ValidationError("Start date cannot be in the future.")

        super().clean()


    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.name} ({self.user}) - Active: {self.is_active}"


    class Meta:
        ordering = ['-start_date']
        verbose_name = "Challenge"
        verbose_name_plural = "Challenges"



class DailyLog(models.Model):
    """
    Records the user's status for a specific day (Clean or Relapse).
    Linked to the specific challenge active at the time of logging.
    """
    STATUS_CHOICES = [
        ('CLEAN', 'Clean Day'),
        ('RELAPSE', 'Relapse Day'),
    ]

    user = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='daily_logs',
        help_text='The user this log belongs to'
    )


    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs',
        help_text="The challenge this log entry is associated with."
    )

    date = models.DateField(
        help_text="The specific date this log entry refers to"
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        help_text="The user's status for this day"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        challenge_name = f" (Challenge: {self.challenge.name})" if self.challenge else ""
        return f"{self.user} - {self.date} - {self.get_status_display()}{challenge_name}"
    

    class Meta:
        ordering = ['date']
        unique_together = ('user', 'date')
        verbose_name = "Daily Log"
        verbose_name_plural = "Daily Logs"


class Achievement(models.Model):
    CRITERIA_TYPE_CHOICES = [
        ('TOTAL_LOGS', 'First Login'),
        ('FIRST_CHECKIN', 'First Check-in'),
        ('STREAK', 'Consecutive Clean Days Streak'),
        ('TOTAL_CLEAN', 'Total Clean Days'),
        ('PROFILE_COMPLETE', 'Profile Completion'),
        ('JOURNAL_ENTRIES', 'Journal Entries'),
        ('RELAPSE_LOGGED', 'Relapse Logged'),
    ]


    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="The name of the achievement (e.g., '3 Days Clean')."
    )

    description = models.TextField(
        blank=True,
        help_text="A brief description of how to earn the achievement."
    )

    icon = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Icon representation (e.g., emoji '🔥' or FontAwesome class 'fas fa-trophy')."
    )

    criteria_type = models.CharField(
        max_length=20,
        choices=CRITERIA_TYPE_CHOICES,
        help_text="The type of condition required to unlock this achievement."
    )

    criteria_value = models.PositiveIntegerField(
        help_text="The value associated with the criteria (e.g., 3 for a 3-day streak)."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['criteria_type', 'criteria_value']
        verbose_name = "Achievement"
        verbose_name_plural = "Achievements"


    

class UserAchievement(models.Model):
    """
    Links a User (Account) to an Achievement they have unlocked.
    """

    user = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='achievements',
        help_text="The user who unlocked the achievement."
    )


    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='unlocked_by',
        help_text="The achievement that was unlocked."
    )

    unlocked_at = models.DateTimeField(
        auto_now_add=True,
        help_text="The timestamp when the achievement was unlocked."
    )

    def __str__(self):
        # Using user.__str__() which defaults to email in your Account model
        return f"{self.user} unlocked '{self.achievement.name}'"
    
    class Meta:
        ordering = ['-unlocked_at']
        # A user can unlock each achievement only once
        unique_together = ('user', 'achievement')
        verbose_name = "User Achievement"
        verbose_name_plural = "User Achievements"


class Quote(models.Model):
    author = models.CharField(max_length=50)
    text = models.TextField(blank=True)

    def __str__(self):
        return self.author

class TimelineEvent(models.Model):
    """
    Represents a significant event in the user's journey for display in the timeline.
    Instances are created programmatically when specific actions occur.
    """
    EVENT_TYPE_CHOICES = [
        ('JOINED', 'User Joined'),
        ('CHALLENGE_STARTED', 'Challenge Started'),
        ('CHALLENGE_COMPLETED', 'Challenge Completed'), # Added for completeness
        ('ACHIEVEMENT_UNLOCKED', 'Achievement Unlocked'),
        ('RELAPSE_LOGGED', 'Relapse Logged'),
        ('CLEAN_DAY_LOGGED', 'Clean Day Logged'),
        ('REFLECTION_ADDED', 'Reflection Added'),
        ('JOURNAL_ENTRY_ADDED', 'Journal Entry Added'),
        ('STREAK_MILESTONE', 'Streak Milestone Reached'),
    ]

    user = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='timeline_events',
        help_text="The user associated with this timeline event."
    )

    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When the event occurred."
    )

    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPE_CHOICES,
        help_text="The type of event that occurred."
    )


    title = models.CharField(
        max_length=255,
        help_text="A short title for the timeline entry (e.g., '3-Day Streak Achieved!')."
    )

    description = models.TextField(
        blank=True,
        help_text="Optional longer description or context for the event."
    )

    # Optional: Link to related objects if needed for direct navigation from timeline
    # challenge = models.ForeignKey(Challenge, null=True, blank=True, on_delete=models.SET_NULL)
    # achievement = models.ForeignKey(Achievement, null=True, blank=True, on_delete=models.SET_NULL)
    # daily_log = models.ForeignKey(DailyLog, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.user} at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp'] # Show newest events first
        verbose_name = "Timeline Event"
        verbose_name_plural = "Timeline Events"

    
class Reflection(models.Model):
    """
    Stores a user's reflection text entered on the achievements page or elsewhere.
    """
    user = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='reflections',
        help_text="The user who wrote this reflection."
    )

    text = models.TextField(
        help_text="The content of the user's reflection."
    )

    relapse_text = models.TextField(
        blank=True,
        help_text="Optional text for the relapse reflection."
    )
    # Optional: Link to related objects if needed for direct navigation from timeline
    created_at = models.DateTimeField(
        auto_now_add=True, # Automatically set when created
        db_index=True, # Index for potentially ordering/filtering by date
        help_text="When the reflection was saved."
    )


    def __str__(self):
        return f"Reflection by {self.user} on {self.created_at.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-created_at'] # Show most recent reflections first
        verbose_name = "Reflection"
        verbose_name_plural = "Reflections"
