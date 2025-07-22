from .models import DailyLog, UserAchievement, Achievement, TimelineEvent
from accounts.models import Account
from django.utils import timezone
from django.db.models import Count
import datetime

import logging

logger = logging.getLogger(__name__)


def calculate_current_streak(user:Account) -> int:
    """Calculates the user's current consecutive clean day streak ending today or yesterday."""
    today = timezone.now()
    streak = 0
    
    
    # Fetch logs relevant to the current potential streak, ordered newest first
    logs = DailyLog.objects.filter(user=user, date__lte=today).order_by('-date')

    expected_date = today
    has_logged_today = False

    for log in logs:
        # if a log has been entered, note it then
        if log.date == today:
            has_logged_today = True

        # If the log date doesn't match the expected consecutive date, the streak is broken
        if log.date != expected_date:
            # Exception: If we expect today but find yesterday's clean log, the streak continues from yesterday.
            if expected_date == today and log.date == today - datetime.timedelta(days=1) and log.status == 'CLEAN':
                streak += 1
                expected_date -= datetime.timedelta(days=1)
                continue # Continue checking from the day before yesterday
            # Any other gap breaks the streak from this point backward.
            break


        # if the log is for the expected date:
        if log.status == 'CLEAN':
            streak += 1
            expected_date -= datetime.timedelta(days=1) # Look for the previous day next
        else: #  Status is RELAPSE
            # If the relapse was today, current streak is 0
            if log.date == today:
                return 0
            # If relapse was before today, the streak counted so far is incorrect, break loop.
            # The streak actually ended the day *before* this relapse log.
            # But since we iterate backwards, simply breaking gives the streak *up to* the relapse.
            # We need the streak *before* the relapse. Let's refine.
            # If we find a relapse on expected_date, the streak ended the day *after* it.
            # But our loop counts backwards, so breaking here correctly excludes the relapse day
            # and the streak variable holds the count *before* this relapse.
            break
    
    # If today hasn't been logged AND the streak counted ends yesterday, that's the current streak.
    # If today WAS logged and was clean, the streak count is correct.
    # If today was logged and was a relapse, streak would be 0 from the logic above.
    return streak


def calculate_longest_streak(user: Account) -> int:
    """Calculates the user's longest consecutive clean day streak ever."""
    logs = DailyLog.objects.filter(user=user).order_by('date') #order from the oldest to newest
    longest_streak = 0
    current_streak = 0
    expected_date = None


    for log in logs:
        if log.status == 'CLEAN':
            # check for consectiveness
            if expected_date is None or log.date == expected_date:
                current_streak += 1
            else: # Gap detected, reset current streak
                current_streak = 1
            # update expected date from the next iteration
            expected_date = log.date + datetime.timedelta(days=1)
        else:
            # status is RELAPSE
            # current streak ends, compare with the longest
            longest_streak = max(longest_streak, current_streak)
            # reset current streak and expected date
            current_streak = 0
            expected_date = None # next clean day needs to start a new streak

    # Final check in case the longest streak continued to the last log
    longest_streak = max(longest_streak, current_streak)
    return longest_streak


def get_total_clean_days(user: Account) -> int:
    """Counts the total number of clean days logged by the user."""
    return DailyLog.objects.filter(user=user, status='CLEAN').count()

def get_total_relapses(user:Account) -> int:
    """Counts the total number of relapses logged by the user."""
    return DailyLog.objects.filter(user=user, status='RELAPSE').count()


def check_and_award_achievements(user):
    """
    Checks all defined achievements against the user's current status
    and awards any that are newly met.
    """
    # get the IDs of the achievements already unlocked by the user

    unlocked_ids = set(UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True))

    # get all the potential achievements not yet unlocked
    achievements_to_check = Achievement.objects.exclude(id__in=unlocked_ids)


    if not achievements_to_check.exists():
        # No achievements to check
        return
    
    # get user's current state 
    # try to cache this later on for if this is called many times, it might make your app slow
    current_streak = calculate_current_streak(user)
    total_logs = DailyLog.objects.filter(user=user).count()
    total_relapses = get_total_relapses(user)


    newly_unlocked_count = 0

    for achievement in achievements_to_check:
        unlocked = False # Flag false to check if criteria is met

        # check criteria based on type

        if achievement.criteria_type == 'STREAK':
            if current_streak >= achievement.criteria_value:
                unlocked = True
        elif achievement.criteria_type == 'TOTAL_LOGS':
             if total_logs >= achievement.criteria_value:
                unlocked = True
        elif achievement.criteria_type == 'RELAPSE_LOGGED':
            # This might be triggered specifically when a relapse occurs,
            # or check if at least one relapse exists. Let's assume check for > 0.
            if total_relapses >= achievement.criteria_value: # criteria_value likely 1
                 unlocked = True
        elif achievement.criteria_type == 'FIRST_CHECKIN': # Same as TOTAL_LOGS == 1 ?
             if total_logs >= 1:
                 unlocked = True


        try:
            # if criteria is met, award the achievement
            if unlocked:
                # Create a new UserAchievement instance
                UserAchievement.objects.create(user=user, achievement=achievement)
                newly_unlocked_count += 1
                
                logger.info(f"User {user.username} unlocked achievement: {achievement.name}")


                # create a timeline event for the unlock

                TimelineEvent.objects.create(
                    user=user,
                    event_type='ACHIEVEMENT_UNLOCKED',
                    title=f"Achievement Unlocked: {achievement.name}",
                    description=achievement.description
                )

        except Exception as e:
            # Handle potential race conditions or other errors if needed
            logger.error(f"Error awarding achievement {achievement.name} to user {user.email}: {e}")

    if newly_unlocked_count > 0:
        logger.info(f"Awarded {newly_unlocked_count} new achievements to user {user.email}")