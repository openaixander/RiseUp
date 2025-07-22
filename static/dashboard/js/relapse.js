document.addEventListener('DOMContentLoaded', function() {

    // --- Configuration ---
    const processUrl = "{% url 'dashboard:ajax_log_relapse_process' %}";
    const reflectUrl = "{% url 'dashboard:ajax_log_relapse_reflect' %}";
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value; // Get CSRF token

    // --- DOM Elements ---
    const confirmBtn = document.getElementById('confirm-relapse');
    const submitReflectionBtn = document.getElementById('submit-reflection');
    const skipReflectionBtn = document.getElementById('skip-reflection');
    const continueToRestartBtn = document.getElementById('continue-to-restart');
    const reflectionTextArea = document.getElementById('{{ reflection_form.relapse_text.id_for_label }}'); // Use Django form ID
    const messageContainer = document.getElementById('relapse-messages');
    const reflectionErrorContainer = document.getElementById('reflection-errors');

    const steps = {
        confirm: document.getElementById('confirmation-card'),
        reflect: document.getElementById('reflection-card'),
        badge: document.getElementById('badge-card'),
        restart: document.getElementById('restart-card')
    };

    // --- Helper Functions ---
    function showStep(stepName) {
        // Hide all steps
        Object.values(steps).forEach(el => el.classList.add('hidden'));
        // Show the target step
        if (steps[stepName]) {
            steps[stepName].classList.remove('hidden');
        } else {
            console.error("Unknown step:", stepName);
        }
         // Clear previous messages
        messageContainer.innerHTML = '';
        if(reflectionErrorContainer) reflectionErrorContainer.innerHTML = '';
    }

    function displayMessage(text, level = 'danger') {
         messageContainer.innerHTML = `<div class="alert alert-${level}">${text}</div>`;
    }

    // --- Event Listeners ---

    // 1. Confirm Relapse ("Yes, I did")
    confirmBtn.addEventListener('click', function() {
        confirmBtn.disabled = true; // Prevent double-clicks
        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Processing...';

        fetch(processUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest', // Standard header for AJAX
            },
            // No body needed as the action is implied by the URL
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showStep(data.next_step); // Move to reflection step
            } else {
                displayMessage(data.message || 'An error occurred.');
                confirmBtn.disabled = false; // Re-enable on error
                confirmBtn.innerHTML = '<i class="fas fa-check me-2"></i> Yes, I did';
            }
        })
        .catch(error => {
            console.error('Error processing relapse:', error);
            displayMessage('A network error occurred. Please try again.');
            confirmBtn.disabled = false; // Re-enable on error
            confirmBtn.innerHTML = '<i class="fas fa-check me-2"></i> Yes, I did';
        });
    });

    // 2. Submit Reflection
    submitReflectionBtn.addEventListener('click', function() {
        const reflectionText = reflectionTextArea.value;
        submitReflectionBtn.disabled = true;
        submitReflectionBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Submitting...';

        const formData = new FormData();
        formData.append('action', 'submit');
        formData.append('text', reflectionText);
        // CSRF token is sent via header

        fetch(reflectUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData // Send as form data
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showStep(data.next_step); // Move to badge step
            } else {
                 displayMessage(data.message || 'An error occurred saving reflection.');
                 if (data.errors) {
                    // Handle potential form errors (e.g., from form.errors.as_json())
                    try {
                         const errors = JSON.parse(data.errors);
                         if(errors.text && reflectionErrorContainer) {
                             reflectionErrorContainer.textContent = errors.text[0].message;
                         }
                    } catch(e) { console.error("Error parsing form errors", e)}
                 }
                submitReflectionBtn.disabled = false;
                submitReflectionBtn.innerHTML = '<i class="fas fa-paper-plane me-2"></i> Submit & Continue';
            }
        })
        .catch(error => {
             console.error('Error submitting reflection:', error);
             displayMessage('A network error occurred. Please try again.');
             submitReflectionBtn.disabled = false;
             submitReflectionBtn.innerHTML = '<i class="fas fa-paper-plane me-2"></i> Submit & Continue';
        });
    });

    // 3. Skip Reflection
    skipReflectionBtn.addEventListener('click', function() {
         skipReflectionBtn.disabled = true; // Prevent double-clicks

         const formData = new FormData();
         formData.append('action', 'skip');

         fetch(reflectUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showStep(data.next_step); // Move to badge step
            } else {
                displayMessage(data.message || 'An error occurred.');
                skipReflectionBtn.disabled = false; // Re-enable
            }
        })
        .catch(error => {
            console.error('Error skipping reflection:', error);
            displayMessage('A network error occurred. Please try again.');
            skipReflectionBtn.disabled = false; // Re-enable
        });
    });

    // 4. Continue to Restart Options (from Badge step)
    continueToRestartBtn.addEventListener('click', function() {
        showStep('restart'); // Just show the next step, no backend needed
    });

    // --- Initial State ---
    // Show only the confirm step initially (handled by default 'hidden' classes)
    // showStep('confirm'); // Not needed if HTML defaults to showing confirm card

}); // End DOMContentLoaded