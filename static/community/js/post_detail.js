document.addEventListener('DOMContentLoaded', function() {
    // --- Like Button AJAX ---
    const likeUrl = "{% url 'community:ajax_toggle_like' %}";
    const likeCsrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const likeMessagesContainer = document.getElementById('page-messages'); // Use main messages container

    document.body.addEventListener('click', function(event) {
        const likeButton = event.target.closest('.like-button');
        if (!likeButton) return;

        event.preventDefault();
        likeButton.disabled = true;
        const postId = likeButton.dataset.postId;
        const heartIcon = likeButton.querySelector('.fa-heart'); // Get the icon

        const formData = new FormData();
        formData.append('post_id', postId);

        fetch(likeUrl, {
            method: 'POST',
            headers: { 'X-CSRFToken': likeCsrfToken, 'X-Requested-With': 'XMLHttpRequest' },
            body: formData
        })
        .then(response => {
            if (!response.ok) { return response.json().then(errData => { throw new Error(errData.message || `HTTP error ${response.status}`); }); }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                const likeCountElement = document.getElementById(`like-count-${postId}`);
                if (likeCountElement) { likeCountElement.textContent = data.new_like_count; }

                if (data.liked) {
                    likeButton.classList.add('liked');
                    heartIcon.classList.remove('far'); // Switch to solid icon
                    heartIcon.classList.add('fas');
                    heartIcon.classList.add('like-animation'); // Add animation class
                } else {
                    likeButton.classList.remove('liked');
                    heartIcon.classList.remove('fas'); // Switch to regular icon
                    heartIcon.classList.add('far');
                    heartIcon.classList.remove('like-animation'); // Remove animation class
                }
                 // Remove animation class after it finishes
                 heartIcon.addEventListener('animationend', () => {
                    heartIcon.classList.remove('like-animation');
                });
            } else {
                displayPageMessage(data.message || 'Could not update like.', 'warning');
            }
        })
        .catch(error => {
            console.error('Fetch error (like):', error);
            displayPageMessage(error.message || 'Network error, please try again.', 'danger');
        })
        .finally(() => {
            likeButton.disabled = false;
        });
    });

    // --- Comment Form AJAX ---
    const commentForm = document.getElementById('comment-form');
    const commentTextArea = commentForm ? commentForm.querySelector('textarea') : null;
    const submitCommentBtn = document.getElementById('submit-comment-btn');
    const commentsList = document.getElementById('comments-list');
    const commentFormError = document.getElementById('comment-form-error');
    const noCommentsMessage = document.getElementById('no-comments-message');
    const commentCountSpan = document.getElementById('comment-count-{{ post.pk }}'); // For updating count in footer
    const repliesHeader = document.getElementById('replies-header-text'); // For updating header count

    if (commentForm && commentTextArea && submitCommentBtn && commentsList) {
        commentForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Stop traditional form submission
            submitCommentBtn.disabled = true;
            submitCommentBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Posting...';
            if (commentFormError) commentFormError.textContent = ''; // Clear previous errors

            const commentData = new FormData(commentForm); // Collect form data

            fetch(commentForm.action, { // URL comes from form's action attribute
                method: 'POST',
                headers: {
                    // FormData sets Content-Type correctly
                    'X-CSRFToken': likeCsrfToken, // Reuse CSRF token
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: commentData
            })
            .then(response => {
                 if (!response.ok) {
                     // Handle non-JSON errors or server errors first
                     if (response.headers.get("content-type")?.includes("application/json")) {
                          return response.json().then(errData => { throw new Error(errData.message || `Error ${response.status}`); });
                     } else {
                          throw new Error(`Server error: ${response.status} ${response.statusText}`);
                     }
                 }
                 return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    // Success! Add the comment HTML
                    if (noCommentsMessage) {
                        noCommentsMessage.remove(); // Remove 'no comments' message if it exists
                    }
                    commentsList.insertAdjacentHTML('beforeend', data.comment_html); // Add new comment HTML
                    commentTextArea.value = ''; // Clear the textarea

                    // Highlight the new comment briefly
                    const newCommentElement = commentsList.lastElementChild;
                    if(newCommentElement) {
                        newCommentElement.classList.add('new-comment-highlight');
                         setTimeout(() => {
                            newCommentElement.classList.remove('new-comment-highlight');
                        }, 2000); // Remove highlight after 2 seconds
                    }

                    // Update comment counts
                    if (commentCountSpan) commentCountSpan.textContent = data.comment_count;
                    if (repliesHeader) repliesHeader.textContent = `Replies (${data.comment_count})`;

                    displayPageMessage("Your reply has been posted!", 'success');

                } else {
                    // Handle form validation errors from backend
                    const message = data.message || 'Could not post reply. Please check your input.';
                    if (commentFormError) commentFormError.textContent = message;
                    displayPageMessage(message, 'warning'); // Also show at top
                }
            })
            .catch(error => {
                 console.error('Fetch error (comment):', error);
                 const message = error.message || 'Network error, please try again.';
                 if (commentFormError) commentFormError.textContent = message;
                 displayPageMessage(message, 'danger');
            })
            .finally(() => {
                 // Re-enable button
                 submitCommentBtn.disabled = false;
                 submitCommentBtn.innerHTML = 'Post Reply';
            });
        });
    }

    // Helper to display messages at the top of the page
    function displayPageMessage(message, level = 'danger') {
        const messageContainer = document.getElementById('page-messages');
        if (messageContainer) {
             const alertHtml = `
                <div class="alert alert-${level} alert-dismissible fade show" role="alert">
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>`;
             // Prepend new message
             messageContainer.insertAdjacentHTML('afterbegin', alertHtml);
        }
    }

}); // End DOMContentLoaded