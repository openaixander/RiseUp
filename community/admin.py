from django.contrib import admin
from django.utils.html import format_html
from .models import Post, Comment, Like


class CommentInline(admin.TabularInline):
    """Inline admin for comments, showing them on the post admin page."""
    model = Comment
    extra = 0  # Don't show any empty forms
    readonly_fields = ('created_at',)
    fields = ('author', 'body', 'is_anonymous', 'created_at')
    raw_id_fields = ('author',)  # Use a search widget for better UX with many users


class LikeInline(admin.TabularInline):
    """Inline admin for likes, showing them on the post admin page."""
    model = Like
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('user', 'created_at')
    raw_id_fields = ('user',)  # Use a search widget for better UX with many users


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Admin configuration for the Post model."""
    list_display = ('title', 'display_author', 'created_at', 'updated_at', 'comment_count', 'like_count')
    list_filter = ('is_anonymous', 'created_at', 'updated_at')
    search_fields = ('title', 'body', 'author__username', 'author__email')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    raw_id_fields = ('author',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'body')
        }),
        ('Author Information', {
            'fields': ('author', 'is_anonymous')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [CommentInline, LikeInline]
    
    def display_author(self, obj):
        """Returns the display name of the author (respecting anonymity setting)."""
        return obj.get_display_author()
    display_author.short_description = 'Author'
    
    def comment_count(self, obj):
        """Returns the number of comments for a post."""
        count = obj.comments.count()
        return format_html('<a href="?post__id__exact={}">{}</a>', obj.id, count)
    comment_count.short_description = 'Comments'
    
    def like_count(self, obj):
        """Returns the number of likes for a post."""
        count = obj.likes.count()
        return format_html('<a href="?post__id__exact={}">{}</a>', obj.id, count)
    like_count.short_description = 'Likes'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin configuration for the Comment model."""
    list_display = ('id', 'truncated_body', 'display_author', 'post_title', 'created_at')
    list_filter = ('is_anonymous', 'created_at')
    search_fields = ('body', 'author__username', 'author__email', 'post__title')
    readonly_fields = ('created_at',)
    raw_id_fields = ('author', 'post')
    
    fieldsets = (
        (None, {
            'fields': ('post', 'body')
        }),
        ('Author Information', {
            'fields': ('author', 'is_anonymous')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
        }),
    )
    
    def display_author(self, obj):
        """Returns the display name of the author (respecting anonymity setting)."""
        return obj.get_display_author()
    display_author.short_description = 'Author'
    
    def post_title(self, obj):
        """Returns a link to the associated post."""
        return format_html('<a href="{}">{}</a>', 
                          f'/admin/community/post/{obj.post.id}/change/',
                          obj.post.title)
    post_title.short_description = 'Post'
    
    def truncated_body(self, obj):
        """Returns a truncated version of the comment body."""
        if len(obj.body) > 50:
            return f"{obj.body[:50]}..."
        return obj.body
    truncated_body.short_description = 'Comment'


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    """Admin configuration for the Like model."""
    list_display = ('id', 'user_display', 'post_title', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email', 'post__title')
    readonly_fields = ('created_at',)
    raw_id_fields = ('user', 'post')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'post', 'created_at')
        }),
    )
    
    def user_display(self, obj):
        """Returns the username of the user who liked."""
        return obj.user.username
    user_display.short_description = 'User'
    
    def post_title(self, obj):
        """Returns a link to the associated post."""
        return format_html('<a href="{}">{}</a>', 
                          f'/admin/community/post/{obj.post.id}/change/',
                          obj.post.title)
    post_title.short_description = 'Post'