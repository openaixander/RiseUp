from django.contrib import admin
from .models import (
    Challenge, 
    DailyLog, 
    Achievement, 
    UserAchievement, 
    Quote, 
    TimelineEvent, 
    Reflection
)


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'start_date', 'duration_days', 'is_active', 'progress_percentage')
    list_filter = ('is_active', 'enable_daily_reminder', 'start_date')
    search_fields = ('name', 'user__email', 'user__username')
    date_hierarchy = 'start_date'
    readonly_fields = ('created_at', 'updated_at', 'end_date', 'current_day_number', 'progress_percentage')
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'is_active')
        }),
        ('Challenge Duration', {
            'fields': ('start_date', 'duration_days', 'end_date', 'current_day_number', 'progress_percentage')
        }),
        ('Reminder Settings', {
            'fields': ('enable_daily_reminder', 'reminder_time')
        }),
        ('Metadata', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(DailyLog)
class DailyLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'status', 'challenge')
    list_filter = ('status', 'date')
    search_fields = ('user__email', 'user__username', 'challenge__name')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Log Information', {
            'fields': ('user', 'challenge', 'date', 'status')
        }),
        ('Metadata', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'criteria_type', 'criteria_value', 'icon')
    list_filter = ('criteria_type',)
    search_fields = ('name', 'description')
    fieldsets = (
        ('Achievement Details', {
            'fields': ('name', 'description', 'icon')
        }),
        ('Achievement Criteria', {
            'fields': ('criteria_type', 'criteria_value')
        }),
    )


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'unlocked_at')
    list_filter = ('unlocked_at', 'achievement')
    search_fields = ('user__email', 'user__username', 'achievement__name')
    date_hierarchy = 'unlocked_at'
    readonly_fields = ('unlocked_at',)


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ('author', 'text_preview')
    search_fields = ('author', 'text')
    
    def text_preview(self, obj):
        """Return a truncated version of the quote text"""
        max_length = 50
        if len(obj.text) > max_length:
            return f"{obj.text[:max_length]}..."
        return obj.text
    
    text_preview.short_description = 'Quote Preview'


@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'title')
    list_filter = ('timestamp',)
    search_fields = ('user__email', 'user__username', 'title', 'description')
    date_hierarchy = 'timestamp'
    fieldsets = (
        ('Event Information', {
            'fields': ('user', 'timestamp', 'title')
        }),
        ('Content', {
            'fields': ('description',)
        }),
    )


@admin.register(Reflection)
class ReflectionAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'text_preview')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'user__username', 'text')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    
    def text_preview(self, obj):
        """Return a truncated version of the reflection text"""
        max_length = 50
        if len(obj.text) > max_length:
            return f"{obj.text[:max_length]}..."
        return obj.text
    
    text_preview.short_description = 'Reflection Preview'


# Optional: Customize the admin site title, header, and index title
admin.site.site_header = 'RiseUp Challenge Administration'
admin.site.site_title = 'RiseUp Admin'
admin.site.index_title = 'Challenge Management'