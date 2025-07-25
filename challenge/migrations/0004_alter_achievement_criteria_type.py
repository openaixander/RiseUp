# Generated by Django 4.2.20 on 2025-04-19 05:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenge', '0003_alter_achievement_criteria_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='achievement',
            name='criteria_type',
            field=models.CharField(choices=[('TOTAL_LOGS', 'First Login'), ('FIRST_CHECKIN', 'First Check-in'), ('STREAK', 'Consecutive Clean Days Streak'), ('TOTAL_CLEAN', 'Total Clean Days'), ('PROFILE_COMPLETE', 'Profile Completion'), ('JOURNAL_ENTRIES', 'Journal Entries'), ('RELAPSE_LOGGED', 'Relapse Logged')], help_text='The type of condition required to unlock this achievement.', max_length=20),
        ),
    ]
