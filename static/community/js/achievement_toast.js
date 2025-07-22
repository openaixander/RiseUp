function hideAchievementToast() {
    const toast = document.getElementById('achievement-toast');
    if (toast) { toast.classList.remove('show'); }
}
// Auto-hide after 5 seconds
setTimeout(hideAchievementToast, 5000);
// Add listener for close button
 const closeBtn = document.getElementById('close-toast');
 if(closeBtn) { closeBtn.addEventListener('click', hideAchievementToast); }