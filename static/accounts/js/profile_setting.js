{% load static %}

// Preview uploaded avatar
const avatarUpload = document.getElementById('{{ profile_form.avatar.id_for_label }}'); // Use Django form ID
const avatarPreview = document.getElementById('avatarPreview');
const initialAvatarSrc = avatarPreview ? avatarPreview.src : ''; // Store initial if needed

if (avatarUpload && avatarPreview) {
    avatarUpload.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                avatarPreview.src = e.target.result;
            }
            reader.readAsDataURL(file);
        } else {
             if (!avatarUpload.value && initialAvatarSrc) {
                avatarPreview.src = initialAvatarSrc;
             }
        }
    });
}

// Active state for sidebar navigation using URL hash
const sidebarLinks = document.querySelectorAll('.list-group-item[href^="#"]');
function setActiveSidebarLink() {
    let hash = window.location.hash || '#accountInfo'; // Default section
    let foundActive = false;
    sidebarLinks.forEach(link => {
        // Check if the target element for the hash exists
        const targetElement = document.querySelector(link.getAttribute('href'));
        if (link.getAttribute('href') === hash && targetElement) {
            link.classList.add('active');
            foundActive = true;
        } else {
            link.classList.remove('active');
        }
    });
    // Fallback to first link if hash is invalid or element not found
    if (!foundActive && sidebarLinks.length > 0) {
        sidebarLinks[0].classList.add('active');
    }
}
window.addEventListener('DOMContentLoaded', setActiveSidebarLink);
window.addEventListener('hashchange', setActiveSidebarLink);
