from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ChallengeForm, ReflectionForm
from .models import Challenge, Achievement, UserAchievement, Quote, Reflection, TimelineEvent
from .utils import (
    get_total_relapses,
    get_total_clean_days,
    calculate_current_streak,
    calculate_longest_streak
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy

# import random
from django.core.exceptions import ValidationError
from django.contrib import messages




# Create your views here.

# first we need to make sure the user is logged in
@login_required
def create_challenge(request):
    """
    View to handle the creation of a new challenge.
    Displays the form on GET, processes submitted data on POST.
    """
    if request.method == 'POST':
        form = ChallengeForm(request.POST)
        if form.is_valid():
            try:
                new_challenge = form.save(commit=False)
                new_challenge.user = request.user
                new_challenge.is_active = True

                # Deactivate any other active challenges for this user
                Challenge.objects.filter(user=request.user, is_active=True).update(is_active=False)
                
                # Save the new challenge
                new_challenge.save()

                messages.success(request, f"Challenge '{new_challenge.name}' created successfully!")
                return redirect('dashboard:dashboard')
            except ValidationError as e:
                for error in e.messages:
                    form.add_error(None, error)
        
        messages.error(request, "Please correct the errors below.")
    else:
        form = ChallengeForm()

    context = {
        'form': form
    }
    return render(request, 'challenge/create_challenge.html', context)


@login_required
def achievements_view(request):
    """
    Displays the user's achievements, journey timeline, stats,
    and handles reflection submission.
    """
    user = request.user
    reflection_form = ReflectionForm()

    if request.method == 'POST':
        # handle the reflection form submission
        form = ReflectionForm(request.POST)
        if form.is_valid():
            reflection = form.save(commit=False)
            # assign that current reflection to the user that submitted it
            reflection.user = user
            reflection.save()


            # Create a timeline event for reflection
            TimelineEvent.objects.create(
                user=user,
                event_type='REFLECTION_ADDED',
                title='Reflection Added',
                description = reflection.text[:150]
            )

            messages.success(request, "Your reflection has been saved")
            return redirect('challenge:achievement')
        else:
            # if form is invalid 
            messages.error(request, "Could not save reflection. Please check your input.")
            reflection_form = form # Pass the invalid form back to the template


    # fetch data for diplaying the page
    all_achievements = Achievement.objects.order_by('name')
    unlocked_achievements_qs = UserAchievement.objects.filter(user=user)
    unlocked_achievement_ids = set(unlocked_achievements_qs.values_list('achievement_id', flat=True))
    unlocked_achievements_map = {ua.achievement_id: ua.unlocked_at for ua in unlocked_achievements_qs}


    timeline_events = TimelineEvent.objects.filter(user=user).order_by('-timestamp')

    # statistics (using the helper functions)

    current_streak = calculate_current_streak(user)
    longest_streak = calculate_longest_streak(user)
    total_clean_days = get_total_clean_days(user)
    total_relapses = get_total_relapses(user)


    # now for the quote
    quote = Quote.objects.order_by('?').first()
    # --- Calculate Progress for Specific Locked Achievements (Example for Streaks) ---
    # This part can become complex. Only implement if essential.
    # locked_progress = {}
    # for achievement in all_achievements:
    #     if achievement.id not in unlocked_achievement_ids:
    #         # Example: Calculate remaining days for streak achievements
    #         if achievement.criteria_type == 'STREAK' and achievement.criteria_value > current_streak:
    #             remaining = achievement.criteria_value - current_streak
    #             if remaining > 0:
    #                  locked_progress[achievement.id] = f"{remaining} days remaining"
    #         # Add logic for other criteria types if needed (e.g., total clean days, etc.)


    context = {
        'all_achievements': all_achievements,
        'unlocked_achievement_ids': unlocked_achievement_ids,
        'unlocked_achievements_map': unlocked_achievements_map,
        'timeline_events':timeline_events,
        'current_streak':current_streak,
        'longest_streak':longest_streak,
        'total_clean_days':total_clean_days,
        'total_relapses':total_relapses,
        'quote':quote,
        'reflection_form': reflection_form,
    }
    
    return render(request, 'challenge/achievement.html', context)



@login_required  
def edit_challenge(request, challenge_id):
    """
    View to handle the editing of an existing challenge.
    """
    challenge = get_object_or_404(Challenge, id=challenge_id, user=request.user)

    # check if the user is the owner of the challenge
    if request.user != challenge.user:
        messages.error(request, "You do not have permission to edit this challenge.")
        return redirect('dashboard:dashboard')
    if request.method == 'POST':
        form = ChallengeForm(request.POST, instance=challenge)
        if form.is_valid():
            try:
                updated_challenge = form.save(commit=False)

                updated_challenge.save()
                messages.success(request, f"Challenge '{updated_challenge.name}' updated successfully!")
                return redirect('dashboard:dashboard')
            except ValidationError as e:
                for error in e.messages:
                    form.add_error(None, error) # Show model-level validation errors
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ChallengeForm(instance=challenge)
    # Pass the form to the template
    context = {
        'form': form,
        'challenge': challenge,
        'is_editing': True,
    }
    
    return render(request, 'challenge/edit_challenge.html', context)

@login_required
def delete_challenge(request, challenge_id):
    """
    View to handle the deletion of a challenge.
    """
    challenge = get_object_or_404(Challenge, id=challenge_id, user=request.user)

    # check if the user is the owner of the challenge
    if request.user != challenge.user:
        messages.error(request, "You do not have permission to delete this challenge.")
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        # Deactivate the challenge instead of deleting it
        challenge_name = challenge.name
        challenge.delete()
        messages.success(request, f"Challenge '{challenge.name}' deleted successfully!")
        return redirect('dashboard:dashboard')
    else:
        # if the view is accessed via GET, it's not the intended flow (JS should ensure that it is POST)
        # Redirect back to the edit page or dashboard to prevent accidental direct GET access
        messages.error(request, "Invalid request method.")
        return redirect('challenge:edit_challenge', challenge_id=challenge.id)

    context = {
        'challenge': challenge,
    }
    
    return render(request, 'challenge/delete_challenge.html', context)