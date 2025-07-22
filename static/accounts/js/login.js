// Simple Password Visibility Toggle for Login Page
const passwordField = document.getElementById('{{ form.password.id_for_label }}'); // Use Django's ID
const passwordToggle = document.querySelector('.password-toggle'); 

if (passwordToggle && passwordField) {
    passwordToggle.addEventListener('click', function() {
        const icon = this.querySelector('i');
        if (passwordField.type === 'password') {
            passwordField.type = 'text';
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        } else {
            passwordField.type = 'password';
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        }
    });
} else {
    if (!passwordField) console.error("Password field not found for toggle.");
    if (!passwordToggle) console.error("Password toggle element not found.");
}

// Script to handle adding classes to form fields rendered by Django
// This is an alternative if you don't use widget_tweaks or custom template tags
document.addEventListener('DOMContentLoaded', function() {
    const usernameInput = document.getElementById('{{ form.username.id_for_label }}');
    const passwordInput = document.getElementById('{{ form.password.id_for_label }}');

    if (usernameInput) {
        usernameInput.classList.add('form-control', 'form-control-lg');
        usernameInput.setAttribute('placeholder', ' '); // For floating label
    }
        if (passwordInput) {
        passwordInput.classList.add('form-control', 'form-control-lg');
        passwordInput.setAttribute('placeholder', ' '); // For floating label
    }
});