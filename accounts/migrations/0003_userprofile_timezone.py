# Generated by Django 4.2.20 on 2025-04-27 00:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_userprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='timezone',
            field=models.CharField(default='UTC', help_text="User's preferred timezone for dates and times.", max_length=50, verbose_name='timezone'),
        ),
    ]
