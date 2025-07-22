from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse, Http404
from django.template.loader import render_to_string
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from accounts.models import UserProfile
from challenge.models import UserAchievement, Achievement
from .models import Post, Like, Comment
from .forms import PostForm, CommentForm


import logging
from django.utils import timezone
# Create your views here.

logger = logging.getLogger(__name__)


@login_required
def create_post_view(request):
    """Handles displaying the form and creating a new community post."""
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            # Create Post object but don't save to database yet
            new_post = form.save(commit=False)
            # Assign the logged-in user as the author
            new_post.author = request.user
            # Set the anonymity based on the user's profile setting
            # Access profile via the 'profile' related_name from OneToOneField
            # Ensure user profile exists (signal should handle this)
            try:
                new_post.is_anonymous = request.user.profile.post_anonymously
            except UserProfile.DoesNotExist:
                # Fallback if profile somehow doesn't exist - default to False
                new_post.is_anonymous = False

            # Save the Post object to the database
            new_post.save()

            messages.success(request, "Your post has been created successfully!")
            # Redirect to the main community page (adjust URL name if different)
            # Or redirect to the new post's detail page: return redirect(new_post.get_absolute_url())
            return redirect('community:community_list') # Assuming 'community_list' is the URL name for community.html
        else:
            # Form is invalid, re-render the page with the form containing errors
            messages.error(request, "Please correct the errors below.")
    else:
        # GET request: display a blank form
        form = PostForm()

    context = {
        'form': form
    }
    # Use the template name you provided
    return render(request, 'community/new_post.html', context)



def community_list_view(request):
    """Display a paginated list of all community posts"""
    # Fetch all posts, newest posts first. Prefetch related author and profile
    # to avoid N+1 queries when accessing author details or avatar in the template.
    # Also prefetch likes related to the current user for efficient checking.

    all_posts = Post.objects.select_related('author__profile').order_by('-created_at')
    user = request.user

    # Pagination (10 post per page)
    # I can increase it later on
    paginator = Paginator(all_posts, 10)
    page_number = request.GET.get('page')

    try:
        posts_page = paginator.page(page_number)
    except PageNotAnInteger:
        # if page is not an integer, deliver first page
        posts_page = paginator.page(1)
    except EmptyPage:
        # if page is out of range (9999), deliver last page of results
        posts_page = paginator.page(paginator.num_pages)

    # Get IDs of posts likes by the current user FOR THE POSTS ON THE CURRENT PAGE ONLY!
    # This is more efficient tha checking all posts ever liked
    liked_posts_ids = set()

    if user.is_authenticated:
        liked_posts_ids = set(
            Like.objects.filter(
                user=user,
                post__in=posts_page.object_list # Check only against posts on the current page
            ).values_list(
                'post_id', flat=True
            )
        )

    # all_posts = Post.objects.select_related('author__profile') \
    #                       .annotate(comment_count=Count('comments'), like_count=Count('likes')) \
    #                       .order_by('-created_at')
    # Then access post.comment_count and post.like_count in template.
    # For simplicity now, we'll use post.comments.count() and post.likes.count() in template.

    # Fetch a quote (optional, adapt as needed)
    # quote = Quote.objects.order_by('?').first()

    context = {
        'posts_page':posts_page,
        'liked_post_ids':liked_posts_ids,
        # 'quote':quote
    }

    return render(request, 'community/community_list.html', context)


@login_required
@require_POST #This ensures that this view only accepts POSTs request
def toggle_like_ajax(request):
    """Handles liking/unliking a post via AJAX."""
    post_id = request.POST.get('post_id')

    if not post_id:
        return JsonResponse(
            {
                'status':'error',
                'message':'Post ID missing.'
            }, status=400
        )
    
    try:
        post = get_object_or_404(Post, pk=post_id)
        user = request.user

        # check if the user already liked this post
        like_instance = Like.objects.filter(post=post, user=user).first()

        if like_instance:
            # User already liked it, so unlike (delete the Like instance)
            like_instance.delete()
            liked = False
            logger.debug(f"User {user.email} unliked post {post_id}")
        else:
            # User hasn't liked the post, so like it(create a like instance)
            Like.objects.create(post=post, user=user)
            liked=True
            logger.debug(f"User {user.email} liked post {post_id}")

        # Get the updated like count for the specific post
        # Refresh post instance to potentially get updated count if using denormalized field later
        post.refresh_from_db()
        new_like_count = post.likes.count() #calculate the count dyamically

        return JsonResponse(
            {
                'status':'success',
                'liked':liked, # True if now liked, False if now unliked
                'new_like_count': new_like_count
            }
        )
    
    except Post.DoesNotExist:
        return JsonResponse({
            'status':'error',
            'message':'Post not found.'
        }, status=404)
    
    except Exception as e:
        logger.error(f"Error toggling like for user {request.user.email} on post {post_id}: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': 'An error occurred.'}, status=500)


@login_required
def post_detail_view(request, pk):
    """
    Displays a single post, its comments, comment form, like status,
    and similar posts.
    """
    user = request.user
    post = get_object_or_404(
        Post.objects.select_related('author__profile'),
        pk=pk
        )
    
    # Fetch comments, ordered by creation time
    comments = Comment.objects.filter(post=post) \
                              .select_related('author__profile') \
                              .order_by('created_at') #older first
    
    # Check if the current user has liked this post
    user_liked_post = Like.objects.filter(post=post, user=user).exists()

    # prepare the comment form
    comment_form = CommentForm()

    # Fetch "Similar" Post(well, this is just a simple version of it)
    similar_posts = Post.objects.select_related('author__profile')\
                              .exclude(pk=pk)\
                              .order_by('-created_at')[:5] #get 5 most recent while excluding the current post

    # Achievement Toast Logic (same as dashboard, check for recent unlocks)
    show_toast = False
    toast_achievement = None
    latest_unlock = UserAchievement.objects.filter(user=user).order_by('-unlocked_at').first()
    if latest_unlock:
        time_since_unlock = timezone.now() - latest_unlock.unlocked_at
        if time_since_unlock.total_seconds() < 10: # Adjust time window
            show_toast = True
            toast_achievement = latest_unlock.achievement

    context = {
        'post': post,
        'comments': comments,
        'comment_form':comment_form,
        'user_liked_post':user_liked_post,
        'similar_posts':similar_posts,
        'show_toast':show_toast,
        'toast_achievement':toast_achievement
    }
    return render(request, 'community/post_detail.html', context)



@login_required
def add_comment_ajax(request, pk):
    """
    Handles submitting a new comment via AJAX for a specific post (pk).
    Returns JSON response including the rendered comment HTML.
    """
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    user = request.user


    if form.is_valid():
        try:
            comment = form.save(commit=False)
            comment.post = post
            comment.author = user

            # Set anonymity based on user's profile preference
            comment.is_anonymous = user.profile.post_anonymously
            comment.save()


            logger.info(f"User {user.email} added comment {comment.id} to post {post.pk}")

            # render the new comment to HTML to send back to the client
            # Create a seperate template snippet for rendering a single comment
            comment_html = render_to_string(
                'community/includes/html_docs/comment_snippet.html', {
                    'comment':comment,
                    'user':user,
                }
            )


            # Optionally update post's comment count if denormalized later

            return JsonResponse(
                {
                    'status':'success',
                    'comment_html':comment_html,
                    'comment_count':post.comments.count()
                }
            )
        except Exception as e:
            logger.error(f"Error saving comment via AJAX for user {user.email} on post {pk}: {e}", exc_info=True)
            return JsonResponse({
                'status':'error',
                'message':'Error saving comment.'
            }, status=500)
    else:
        # Form is invalid
        # Extract errors to send back(can be more specific if needed)
        error_message = 'Comment cannot be empty.'
        if 'body' in form.errors:
            error_message = form.errors['body'][0] #Get the first error for the body
        return JsonResponse({
            'status':'error',
            'message':error_message
        }, status=400)