document.addEventListener('DOMContentLoaded', function() {
    const likeUrl = "{% url 'community:ajax_toggle_like' %}"; // URL for the AJAX view
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value; // Get CSRF token
    const likeMessagesContainer = document.getElementById('like-messages');

    // Use event delegation for like buttons
    document.body.addEventListener('click', function(event) {
        const likeButton = event.target.closest('.like-button'); // Find closest like button if clicked

        if (!likeButton) {
            return; // Exit if the click wasn't on a like button or its icon
        }

        event.preventDefault(); // Prevent default button action
        likeButton.disabled = true; // Disable button during request

        const postId = likeButton.dataset.postId; // Get post ID from data attribute

        // Prepare data to send
        const formData = new FormData();
        formData.append('post_id', postId);

        // Send AJAX request using Fetch API
        fetch(likeUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest', // Identify as AJAX
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                 // Handle HTTP errors (e.g., 404, 500)
                 console.error("HTTP Error:", response.status, response.statusText);
                 return response.json().then(errData => {
                     throw new Error(errData.message || `HTTP error ${response.status}`);
                 });
            }
            return response.json(); // Parse JSON response
        })
        .then(data => {
            // Handle successful response from Django view
            if (data.status === 'success') {
                // Update like count
                const likeCountElement = document.getElementById(`like-count-${postId}`);
                if (likeCountElement) {
                    likeCountElement.textContent = data.new_like_count;
                }

                // Update button appearance (toggle 'liked' class)
                if (data.liked) {
                    likeButton.classList.add('liked'); // Add 'liked' class for animation/styling
                } else {
                    likeButton.classList.remove('liked'); // Remove 'liked' class
                }
                 // Clear any previous error messages
                 if (likeMessagesContainer) likeMessagesContainer.innerHTML = '';
            } else {
                // Handle error reported by Django view
                console.error("Liking error:", data.message);
                if (likeMessagesContainer) {
                    likeMessagesContainer.innerHTML = `<div class="alert alert-warning alert-dismissible fade show" role="alert">${data.message || 'Could not update like.'}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>`;
                }
            }
        })
        .catch(error => {
            // Handle network errors or other fetch issues
            console.error('Fetch error:', error);
             if (likeMessagesContainer) {
                 likeMessagesContainer.innerHTML = `<div class="alert alert-danger alert-dismissible fade show" role="alert">${error.message || 'Network error, please try again.'}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>`;
             }
        })
        .finally(() => {
             // Re-enable button regardless of success or failure
             likeButton.disabled = false;
        });
    }); // End event listener

}); // End DOMContentLoaded