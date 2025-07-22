from django.db import models
from django.conf import settings
from django.urls import reverse

# Create your models here.


# A model for the community post

class Post(models.Model):
    """Represents a single post in the community section."""
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_posts'
    )

    title = models.CharField(max_length=200)
    body = models.TextField()

    # Flag to respect user's privacy setting at the time of posting
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at'] #newest post should be at the top
        verbose_name = "Community Post"
        verbose_name_plural = "Community Posts"

    def __str__(self):
        return f"{self.title} by " #{self.get_display_author()}


    @property
    def get_absolute_url(self):
    #     """Returns the URL to view the detail of this post."""
    #     # Assumes you have a URL named 'post_detail' taking post's pk
        return reverse('community:post_detail', kwargs={'pk': self.pk})

    def get_display_author(self):
        """Returns 'Anonymous' or the author's username based on is_anonymous flag."""
        if self.is_anonymous:
            return "Anonymous"
        else:
            # display the username of the user
            return self.author.username
        

    # Come back to create methods for comment- like- total numbers

# model for the comment


class Comment(models.Model):
    """Represent a comment made on the community Post."""

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments' #Access via post.comments.all()
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='community_comments',
        null=True
    )

    body = models.TextField(
        max_length=2000
    )

    # Flag to respect user's privacy setting at the time of commenting

    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


    class Meta:
        ordering = ['-created_at'] # Show oldest comments first (typical thread order)
        verbose_name = 'Post Comment'
        verbose_name_plural = 'Post Comments'


    def __str__(self):
        return f"Comment by {self.get_display_author()} on '{self.post.title}'"
    
    def get_display_author(self):
        """Returns 'Anonymous' or the author's username based on is_anonymous flag."""
        if self.is_anonymous:
            return 'Anonymous'

        return self.author.username
    
# the like model

class Like(models.Model):
    """Represent a user liking a community Post"""

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='likes' #Access via post.likes.all()
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_likes'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # ensure a user can only like a post once

        unique_together = ['post', 'user']
        ordering = ['-created_at']
        verbose_name = 'Post Like'
        verbose_name_plural = 'Post Likes'

    def __str__(self):
        return f"{self.user.email} likes '{self.post.title}'"



