// Simple script to show success message when check-in button is clicked
document.querySelector('.check-in-btn').addEventListener('click', function() {
    document.getElementById('success-message').style.display = 'block';
    this.disabled = true;
    this.innerHTML = '<i class="fas fa-check-circle me-2"></i> Checked In!';
    this.classList.remove('btn-success');
    this.classList.add('btn-secondary');
});

// Check if this is the user's first login
function checkFirstTimeLogin() {
    // Check if user has logged in before using localStorage
    const hasLoggedInBefore = localStorage.getItem('hasLoggedInBefore');
    
    if (!hasLoggedInBefore) {
        // This is the first login
        showAchievementToast();
        
        // Set the flag that user has logged in before
        localStorage.setItem('hasLoggedInBefore', 'true');
    }
}

// Show the achievement toast notification
function showAchievementToast() {
    const toast = document.getElementById('achievement-toast');
    
    // Display the toast after a short delay
    setTimeout(() => {
        toast.classList.add('show');
        
        // Auto-hide the toast after 5 seconds (matches the progress bar animation)
        setTimeout(() => {
            hideAchievementToast();
        }, 5000);
    }, 1000);
}

// Hide the achievement toast notification
function hideAchievementToast() {
    const toast = document.getElementById('achievement-toast');
    if (toast) {
        toast.classList.remove('show');
        // Remove the toast from DOM after animation
        setTimeout(() => {
            toast.parentElement.remove();
        }, 500);
    }
}

// Auto-hide after 5 seconds
setTimeout(hideAchievementToast, 7000);

// Show achievement toast if it exists
document.addEventListener('DOMContentLoaded', function() {
    const toast = document.getElementById('achievement-toast');
    if (toast) {
        // Add show class after a brief delay
        setTimeout(() => {
            toast.classList.add('show');
        }, 500);

        // Auto-hide after 5 seconds
        setTimeout(() => {
            hideAchievementToast();
        }, 7000);
    }
});

// // Check for first-time login when the page loads
// window.addEventListener('load', function() {
//     checkFirstTimeLogin();
    
//     // Additional initialization code can go here
    
//     // Add smooth scrolling for navbar links
//     document.querySelectorAll('.navbar .nav-link').forEach(link => {
//         link.addEventListener('click', function(e) {
//             const href = this.getAttribute('href');
//             if (href.startsWith('#') && href !== '#') {
//                 e.preventDefault();
//                 const targetElement = document.querySelector(href);
//                 if (targetElement) {
//                     window.scrollTo({
//                         top: targetElement.offsetTop - 80,
//                         behavior: 'smooth'
//                     });
//                 }
//             }
//         });
//     });
    
//     // Initialize tooltips if you want to use them
//     if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
//         const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
//         tooltipTriggerList.map(function(tooltipTriggerEl) {
//             return new bootstrap.Tooltip(tooltipTriggerEl);
//         });
//     }
    
//     // Update current date in the check-in section
//     const currentDate = new Date();
//     const options = { year: 'numeric', month: 'long', day: 'numeric' };
//     const formattedDate = currentDate.toLocaleDateString('en-US', options);
//     const checkInDateElements = document.querySelectorAll('.check-in-card p.text-muted');
//     checkInDateElements.forEach(element => {
//         if (element.textContent.includes('Record your progress for today')) {
//             element.textContent = `Record your progress for today, ${formattedDate}`;
//         }
//     });
// });