document.addEventListener('DOMContentLoaded', function() {

    // --- DOM Elements ---
    const confirmBtn = document.getElementById('confirm-relapse');
    const submitReflectionBtn = document.getElementById('submit-reflection');
    const skipReflectionBtn = document.getElementById('skip-reflection');
    const continueToRestartBtn = document.getElementById('continue-to-restart');
    
    // MODIFICATION: Get elements that hold the data attributes
    const confirmationCard = document.getElementById('confirmation-card');
    const reflectionCard = document.getElementById('reflection-card');

    // MODIFICATION: Use the static ID that Django generates for the form field.
    // Assuming your form field is named 'relapse_text', its ID will be 'id_relapse_text'.
    // Inspect your page in the browser to confirm this ID if it doesn't work.
    const reflectionTextArea = document.getElementById('id_relapse_text'); 
    
    // This element seems to be missing from your HTML, you may want to add it.
    // For now, I'll add a check to prevent errors if it's not found.
    const messageContainer = document.getElementById('relapse-messages'); 
    const reflectionErrorContainer = document.getElementById('reflection-errors');

    const steps = {
        confirm: confirmationCard,
        reflect: reflectionCard,
        badge: document.getElementById('badge-card'),
        restart: document.getElementById('restart-card')
    };

    // --- Configuration ---
    // MODIFICATION: Read URLs from the data attributes in the HTML.
    const processUrl = confirmationCard.dataset.processUrl;
    const reflectUrl = reflectionCard.dataset.reflectUrl;
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // --- Helper Functions ---
    function showStep(stepName) {
        Object.values(steps).forEach(el => el.classList.add('hidden'));
        if (steps[stepName]) {
            steps[stepName].classList.remove('hidden');
        } else {
            console.error("Unknown step:", stepName);
        }
        if (messageContainer) messageContainer.innerHTML = '';
        if(reflectionErrorContainer) reflectionErrorContainer.innerHTML = '';
    }

    function displayMessage(text, level = 'danger') {
        // This function needs a 'messageContainer' element to exist in the HTML.
        if (messageContainer) {
             messageContainer.innerHTML = `<div class="alert alert-${level}">${text}</div>`;
        } else {
            // Fallback to a simple alert if the container is missing.
            alert(text);
            console.error("Message container 'relapse-messages' not found in HTML.");
        }
    }

    // --- Event Listeners ---

    // 1. Confirm Relapse ("Yes, I did")
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            confirmBtn.disabled = true;
            confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Processing...';

            fetch(processUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showStep(data.next_step);
                } else {
                    displayMessage(data.message || 'An error occurred.');
                    confirmBtn.disabled = false;
                    confirmBtn.innerHTML = '<i class="fas fa-check me-2"></i> Yes, I did';
                }
            })
            .catch(error => {
                console.error('Error processing relapse:', error);
                displayMessage('A network error occurred. Please try again.');
                confirmBtn.disabled = false;
                confirmBtn.innerHTML = '<i class="fas fa-check me-2"></i> Yes, I did';
            });
        });
    }

    // 2. Submit Reflection
    if (submitReflectionBtn) {
        submitReflectionBtn.addEventListener('click', function() {
            const reflectionText = reflectionTextArea.value;
            submitReflectionBtn.disabled = true;
            submitReflectionBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Submitting...';

            const formData = new FormData();
            formData.append('action', 'submit');
            formData.append('relapse_text', reflectionText); // Use the actual field name

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
                    showStep(data.next_step);
                } else {
                     displayMessage(data.message || 'An error occurred saving reflection.');
                     if (data.errors && data.errors.relapse_text) {
                         if(reflectionErrorContainer) {
                             reflectionErrorContainer.textContent = data.errors.relapse_text[0];
                         }
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
    }

    // 3. Skip Reflection
    if (skipReflectionBtn) {
        skipReflectionBtn.addEventListener('click', function() {
             skipReflectionBtn.disabled = true;

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
                    showStep(data.next_step);
                } else {
                    displayMessage(data.message || 'An error occurred.');
                    skipReflectionBtn.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error skipping reflection:', error);
                displayMessage('A network error occurred. Please try again.');
                skipReflectionBtn.disabled = false;
            });
        });
    }

    // 4. Continue to Restart Options (from Badge step)
    if (continueToRestartBtn) {
        continueToRestartBtn.addEventListener('click', function() {
            showStep('restart');
        });
    }
});
