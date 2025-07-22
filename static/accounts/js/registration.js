// Example: If Django renders password field with id="id_password"
const passwordField = document.getElementById('{{ form.password.id_for_label }}'); // Use Django's ID
const confirmPasswordField = document.getElementById('{{ form.confirm_password.id_for_label }}'); // Use Django's ID
const passwordToggle = document.querySelector('.password-toggle'); // Keep if class based
const strengthBars = document.querySelectorAll('.strength-bar'); // Keep if class based
const strengthText = document.querySelector('.strength-text'); // Keep if class based

if (passwordField) {
  passwordField.addEventListener('input', function() {
      const password = this.value;
      // Reset all bars
      strengthBars.forEach(bar => bar.classList.remove('active'));
      
      if (password.length === 0) {
          strengthText.textContent = 'Password strength: Type to check';
          return;
      }
      
      let strength = 0;
      if (password.length > 6) strength++;
      if (password.length > 10) strength++;
      if (password.match(/[a-z]/) && password.match(/[A-Z]/)) strength++;
      if (password.match(/\d/)) strength++;
      if (password.match(/[^a-zA-Z\d]/)) strength++;
      
      // Clamp strength to the number of bars
      strength = Math.min(strength, strengthBars.length); 

      for (let i = 0; i < strength; i++) {
          if (strengthBars[i]) strengthBars[i].classList.add('active');
      }
      
      const strengthLabels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong']; // Adjusted labels
      strengthText.textContent = `Password strength: ${strengthLabels[Math.max(0, strength - 1)] || 'Very Weak'}`;
  });
}

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
}