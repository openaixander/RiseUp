document.addEventListener('DOMContentLoaded', function() {
            // --- Challenge Duration Logic ---
            const durationOptionCards = document.querySelectorAll('.option-card[data-duration-option]');
            const customDurationContainer = document.getElementById('custom-duration-container');
            const durationDaysInput = document.querySelector('[name="duration_days"]'); // More robust selector for the form field

            function updateDurationSelection() {
                const currentValue = parseInt(durationDaysInput.value, 10);
                let customSelected = true;

                durationOptionCards.forEach(card => {
                    const optionValue = card.dataset.durationOption;
                    if (optionValue === String(currentValue)) {
                        card.classList.add('selected');
                        customSelected = false;
                    } else {
                        card.classList.remove('selected');
                    }
                });

                if (customSelected && !isNaN(currentValue)) { // If current value is not 30 and is a number
                    document.querySelector('.option-card[data-duration-option="custom"]').classList.add('selected');
                    customDurationContainer.style.display = 'block';
                } else if (!customSelected && currentValue === 30) { // If 30 days is selected
                     document.querySelector('.option-card[data-duration-option="30"]').classList.add('selected');
                    customDurationContainer.style.display = 'none';
                } else { // Default to custom if no value or non-30 value
                    document.querySelector('.option-card[data-duration-option="custom"]').classList.add('selected');
                    customDurationContainer.style.display = 'block';
                    if(isNaN(currentValue)) durationDaysInput.value = ''; // Clear if not a number
                }
                 // If 30 days is selected, ensure input value is 30, even if custom container is hidden
                if (document.querySelector('.option-card[data-duration-option="30"]').classList.contains('selected')) {
                    durationDaysInput.value = 30; // ensure value is set for form submission
                    customDurationContainer.style.display = 'none';
                }
            }

            durationOptionCards.forEach(card => {
                card.addEventListener('click', function() {
                    durationOptionCards.forEach(c => c.classList.remove('selected'));
                    this.classList.add('selected');
                    
                    if (this.dataset.durationOption === 'custom') {
                        customDurationContainer.style.display = 'block';
                        // Don't clear durationDaysInput.value, let user type or it keeps existing custom value
                        if (durationDaysInput.value === "30") durationDaysInput.value = ""; // Clear if it was previously 30
                        durationDaysInput.focus();
                    } else {
                        customDurationContainer.style.display = 'none';
                        durationDaysInput.value = this.dataset.durationOption; // Set to 30
                    }
                });
            });
            
            // Initial state for duration
            if (durationDaysInput) {
                updateDurationSelection();
            }

            // --- Reminder Time Visibility ---
            const enableReminderCheckbox = document.getElementById('{{ form.enable_daily_reminder.id_for_label }}'); // Get ID from form
            const reminderTimeContainer = document.getElementById('reminder-time-container');
            
            function toggleReminderTime() {
                if (enableReminderCheckbox && reminderTimeContainer) {
                    reminderTimeContainer.style.display = enableReminderCheckbox.checked ? 'block' : 'none';
                }
            }

            if (enableReminderCheckbox) {
                enableReminderCheckbox.addEventListener('change', toggleReminderTime);
                toggleReminderTime(); // Initial check
            }

            // --- Form submission handler (example, your view handles actual save) ---
            // The original script had an alert and redirect. This is now handled by Django's redirect on success.
            // You could add client-side validation here if desired, but Django handles server-side.
            // document.getElementById('edit-challenge-form').addEventListener('submit', function(e) {
            //     // e.preventDefault(); // Only if doing pure client-side handling before AJAX
            //     console.log('Form submitted'); 
            // });

            // --- Delete Challenge Confirmation ---
            const deleteButton = document.getElementById('deleteChallengeBtn');
            const deleteChallengeForm = document.getElementById('deleteChallengeForm');

            if (deleteButton && deleteChallengeForm) {
                deleteButton.addEventListener('click', function(e) {
                    e.preventDefault(); // Prevent default button action
                    if (confirm('Are you sure you want to delete this challenge? This action cannot be undone.')) {
                        deleteChallengeForm.submit();
                    }
                });
            }
        });