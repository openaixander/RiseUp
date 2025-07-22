from django import forms

from .models import Post, Comment



class PostForm(forms.ModelForm):
    """Form for creating a new community Post."""
    class Meta:
        model = Post
        fields = ['title', 'body']

        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class':'form-control',
                    'id':'post-title',
                    'placeholder':'Enter a clear, specific title for your post'
                }
            ),
            'body': forms.Textarea(
                attrs={
                    'class':'form-control',
                    'id':'post-body',
                    'placeholder':'Share your thoughts, questions, or experiences...',
                    'rows':8
                }
            )
        }

        labels = {
            'title': 'Post Title',
            'body': 'Post Content'
        }

class CommentForm(forms.ModelForm):
    """Form for submitting a new comment on a post"""
    
    class Meta:
        model = Comment
        fields = ['body'] #User only needs to input the comment body
        widgets = {
            'body':forms.Textarea(
                attrs={
                    'class':'form-control',
                    'rows': 4,
                    'placeholder':'Share your thoughts, advice, or encouragement...',
                    'required':True, #Ensure comment is not empty
                }
            )
        }

        labels = {
            'body': ''
        }