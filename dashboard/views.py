from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from challenge.models import Challenge, DailyLog, Achievement, UserAchievement, TimelineEvent
from challenge.forms import ReflectionForm
from challenge.utils import (
    calculate_current_streak,
    calculate_longest_streak,
    get_total_relapses
)
import calendar
import logging

# Create your views here.

logger = logging.getLogger(__name__)

@login_required
def dashboard_view(request):
    """
    Displays the main user dashboard and handles daily check-ins.
    """

    user = request.user
    today = timezone.now().date()
    active_challenge = Challenge.objects.filter(user=user, is_active=True).first()
    today_log = DailyLog.objects.filter(user=user, date=today).first()
    today_log_status = today_log.status if today_log else None

    # time to handle the request(GET and POST)
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'check_in_clean':
            if today_log:
                messages.info(request, 'You have already checked in for today.')
            elif not active_challenge:
                messages.warning(request, "Please create or activate a challenge before checking in.")
            else:
                # create a clean daily log in
                DailyLog.objects.create(
                    user=user,
                    date=today,
                    status='CLEAN',
                    challenge=active_challenge
                )
                messages.success(request, 'Checked in successfully! Stay strong')
                # Achievement check is handled by the signal automatically post_save
            # Redirect back to dashboard GET to show updated state
            return redirect('dashboard:dashboard')
    
    # fetch stats
    current_streak = calculate_current_streak(user)
    longest_streak = calculate_longest_streak(user)
    total_relapses_count = get_total_relapses(user)


    # calendar data
    year = today.year
    month = today.month
    month_name = calendar.month_name[month]
    cal = calendar.Calendar(firstweekday=0) #  0 = Monday
    calendar_weeks = cal.monthdatescalendar(year, month) #gets week with date objects

    # create a map of {day_number: status} for days logged this month
    logs_this_month = DailyLog.objects.filter(
        user=user,
        date__year=year,
        date__month=month
    )
    logs_map = {log.date.day: log.status.lower() for log in logs_this_month} # Use lower() for CSS class

    # achievement toast logic
    show_toast = False
    toast_achievement = None

    latest_unlock = UserAchievement.objects.filter(
        user=user,
        unlocked_at__date=today
    ).order_by('-unlocked_at').first()

    if latest_unlock:
        time_since_unlock = timezone.now() - latest_unlock.unlocked_at
        # show toast if unlocked within the last few seconds 
        if time_since_unlock.total_seconds() < 40:
            show_toast = True
            toast_achievement = latest_unlock.achievement
        
    
    # render the dashboard template with all the context data
    context = {
        'user': user, # Pass the user object
        'active_challenge': active_challenge,
        'today_log_status': today_log_status,
        'current_streak': current_streak,
        'longest_streak': longest_streak,
        'total_relapses': total_relapses_count,
        'calendar_year': year,
        'calendar_month_name': month_name,
        'calendar_weeks': calendar_weeks, # List of weeks (each week is list of date objects)
        'calendar_logs_map': logs_map, # Dict mapping day number to status string
        'today_date': today, # Pass today's date object
        'show_toast': show_toast,
        'toast_achievement': toast_achievement,
    }

    return render(request, 'dashboard/dashboard.html', context)



@login_required
@transaction.atomic # Use transaction.atomic to ensure that all database operations are atomic
def log_relapse_confirm(request):
    """
    Loads the initial relapse page with all sections (most hidden),
    including the reflection form.
    """
    active_challenge = Challenge.objects.filter(user=request.user, is_active=True).first()
    # It's good practice to still check if there's an active challenge,
    # although the button to get here might only show if one exists.
    if not active_challenge:
        messages.info(request, "Please create or activate a challenge before logging a relapse.")
        return redirect('dashboard:dashboard')
    
    # we don't need to handle any form submission here
    # just show the confirmation page
    # render the confirmation template
    reflection_form = ReflectionForm() #Create instance to pass to the template

    # it has been modified to use a single view for all relapse logging
    context = {
        'reflection_form': reflection_form,
    }
    return render(request, 'dashboard/relapse.html', context)


@login_required
@transaction.atomic # Use transaction.atomic to ensure that all database operations are atomic
def log_relapse_process_ajax(request):
    """
    Handles the AJAX POST when user confirms 'Yes, I did'.
    Returns JSON response.
    """

    if request.method != 'POST':
        # if the request is not POST, redirect to the dashboard
       return JsonResponse({
           'status': 'error',
           'message': 'Invalid request method.'
       }, status=405)
    
    user = request.user
    today = timezone.now().date()
    active_challenge = Challenge.objects.filter(user=user, is_active=True).first()

    if not active_challenge:
        return JsonResponse({
            'status': 'error',
            'message': 'No active challenge found.'
        }, status=400)

    try:
        challenge_name_ended = active_challenge.name #store the name of the challenge that ended    
        # create the relapse log(or update if it exists)
        # use update_or_create to avoid duplicates
        daily_log, created = DailyLog.objects.update_or_create(
            user=user,
            date=today,
            defaults={
                'status': 'RELAPSE',
                'challenge': active_challenge
            }
        )

        logger.info(f"Relapse logged for user {user.email} on {today} for challenge {active_challenge.id}. Created: {created}")
        

        # 2. Deactivate the current challenge
        active_challenge.is_active = False
        active_challenge.save()
        logger.info(f"Challenge {active_challenge.id} deactivated for user {user.email}.")
        


        # create Timeline event for relapse
        TimelineEvent.objects.create(
            user=user,
            event_type='RELAPSE_LOGGED',
            title="Relapse Logged",
            description=f"Relapse occurred during challenge: '{challenge_name_ended}'"
        )

        logger.info(f"Processed relapse via AJAX for user {user.email}")
        # Indicate success and the next step for JS
        return JsonResponse(
            {
                'status': 'success',
                'next_step': 'reflect',  # this will take it to the next step
            }
        )
    
    except Exception as e:
        # Handle any exceptions that occur during the process
        logger.error(f"Error processing relapse for user {user.email}: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': 'An error occurred while processing the relapse.'}, status=500)
    

# view to handle the reflection submission
@login_required
def log_relapse_reflect_ajax(request):
    """
    Handles the AJAX POST for submitting or skipping reflection.
    Returns JSON response.
    """

    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method.'
        }, status=405)
    
    action = request.POST.get('action') # 'submit' or 'skip'

    if action == 'submit':
        form = ReflectionForm(request.POST)
        if form.is_valid():
            try:
                # save the reflection
                reflection = form.save(commit=False)
                reflection.user = request.user
                reflection.save()
                messages.success(request, "Reflection saved.")
        
                # create a timeline event for the reflection
                TimelineEvent.objects.create(
                    user=request.user,
                    event_type='RELAPSE_LOGGED',
                    title='Reflection Added After Relapse',
                    description=reflection.text[:150]
                )

                logger.info(f"Saved reflection via AJAX for user {request.user.email}")
                return JsonResponse({'status': 'success', 'message': 'Reflection saved.', 'next_step': 'badge'})
            except Exception as e:
                # Handle any exceptions that occur during the process
                logger.error(f"Error saving reflection for user {request.user.email}: {e}", exc_info=True)
                return JsonResponse({'status': 'error', 'message': 'An error occurred while saving the reflection.'}, status=500)
        else:
            # the form is invalid, show the error
            # Return form errors as JSON
            errors = form.errors.as_json()
            return JsonResponse({'status': 'error', 'message': 'Invalid reflection text.', 'errors': errors}, status=400)
    
    elif action == 'skip':
        # user chose to skip reflection
        # create a timeline event for skipping reflection
        TimelineEvent.objects.create(
            user=request.user,
            event_type='RELAPSE_LOGGED',
            title='Reflection Skipped After Relapse',
            description='User chose to skip reflection.'
        )

        logger.info(f"Skipped reflection via AJAX for user {request.user.email}")
        return JsonResponse({'status': 'success', 'message': 'Reflection skipped.', 'next_step': 'badge'})
    else:
        # if the action is not recognized, return an error    
        return JsonResponse({'status': 'error', 'message': 'Invalid action.'}, status=400)