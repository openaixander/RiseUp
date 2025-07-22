from django import forms
from .models import Challenge, Reflection
from django.utils import timezone

class ChallengeForm(forms.ModelForm):
    """
    Form for creating and updating Challenge instances.
    """
    start_date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
            }
        ),
        initial=timezone.localtime(timezone.now()).date,
        help_text='When do you want to begin your challenge?' 
    )

    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        if start_date:
            current_date = timezone.localtime(timezone.now()).date()
            if start_date > current_date:
                raise forms.ValidationError("Start date cannot be in the future.")
        return start_date

    reminder_time = forms.TimeField(
        required=False, # make it not required if reminders are disabled
        widget=forms.TimeInput(
            attrs={
                'type':'time',
                'class':'form-control',
            },
            format='%H:%M' # Use 24-hour format 
        ),
        initial='00:00', #default to 12am
        help_text="When would you like to receive your daily reminder?"
    )


    class Meta:
        model = Challenge
        fields = [
            'name',
            'duration_days',
            'start_date',
            'enable_daily_reminder',
            'reminder_time',
        ]

        widgets= {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 30 Days Clean',
                'required': True, # Model field likely has blank=False
            }),
            'duration_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '30',
                'min': '1',       # HTML5 validation attributes
                'max': '365',     # HTML5 validation attributes
                'required': True,
            }),
            'enable_daily_reminder': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                 # The template handles the switch styling, link the id correctly
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control date-picker',
                'type': 'date',
                'required': True,
                'min': timezone.localtime(timezone.now()).date(), # HTML5 validation attributes
                # The min date is set to today, so the user can't select a past date
            }),
            # start_date and reminder_time widgets defined above for more control
        }
        labels = {
            'name': 'Challenge Title',
            'duration_days': 'Challenge Duration',
            'enable_daily_reminder': 'Enable daily check-in reminder',
            'reminder_time': 'Reminder Time',
        }
        help_texts = {
            'name': 'Give your challenge a meaningful name that inspires you.',
            'duration_days': 'How many days do you want to commit to this challenge?',
            'start_date': 'Your challenge is currently in progress, changing this will recalculate your progress.',
            # help_text for start_date and reminder_time set on the field definitions above
        }


    def clean(self):
        """
        Custom validation for the form.
        """

        # this here calls the current inherited clean class and about to override it
        cleaned_data = super().clean()
        reminders_enabled = cleaned_data.get('enable_daily_reminder')
        reminder_time = cleaned_data.get('reminder_time')


        # if the reminder are clicked(meaning they are enabled, time should be provided)
        if reminders_enabled and not reminder_time:
            self.add_error('reminder_time', 'Please provide reminder time when reminders are enabled.')

        # if the reminder are disabled, cler the time 
        if not reminders_enabled:
            cleaned_data['reminder_time'] = None

        
        return cleaned_data
    

class ReflectionForm(forms.ModelForm):
    """
    Form for submitting a new Reflection.
    """

    class Meta:
        model = Reflection
        fields = ['text', 'relapse_text']
        
        widgets = {
            'text':forms.Textarea(attrs={
                'class' : 'form-control reflection-input',
                'rows': 4,
                'placeholder':'Share your thoughts, feelings, or insights about your recovery journey...'
            }),
            'relapse_text': forms.Textarea(attrs={
                'class': 'form-control reflection-input',
                'rows': 4,
                'placeholder': 'I\'m feeling down, but I know I can get back on track. Here\'s what happened...'
            })
        }

        labels = {
            'text': '',
            'relapse_text': ''
        }

