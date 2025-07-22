document.addEventListener('DOMContentLoaded', function() {
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const dd = String(today.getDate()).padStart(2, '0');
    const formattedDate = `${yyyy}-${mm}-${dd}`;

    const startDateInput = document.getElementById('{{ form.start_date.id_for_label }}'); // Use Django form field ID
    const startTodayCheckbox = document.getElementById('startToday');
    const reminderCheckbox = document.getElementById('{{ form.enable_daily_reminder.id_for_label }}'); // Use Django form field ID
    const reminderTimeContainer = document.getElementById('reminderTimeContainer');

    // Set initial state for start date
    //startDateInput.value = formattedDate; // Form initial value handles this
    startDateInput.disabled = startTodayCheckbox.checked;

    // Link "Start Today" checkbox to date input
    startTodayCheckbox.addEventListener('change', function() {
        if (this.checked) {
            startDateInput.value = formattedDate; // Set value if checked
            startDateInput.disabled = true;
        } else {
            startDateInput.disabled = false;
        }
    });

    // Initial state for reminder time
    reminderTimeContainer.style.display = reminderCheckbox.checked ? 'block' : 'none';

    // Toggle reminder time based on checkbox
    reminderCheckbox.addEventListener('change', function() {
        reminderTimeContainer.style.display = this.checked ? 'block' : 'none';
    });

    // Recommended duration buttons - Ensure they target the correct ID
    document.querySelectorAll('.btn-outline-primary[onclick*="challengeDuration"]').forEach(button => {
        button.setAttribute('onclick', `document.getElementById('${ '{{ form.duration_days.id_for_label }}' }').value='${button.textContent.match(/\d+/)[0]}'`);
    });
});

// This should be in your create_challenge.js file
document.addEventListener('DOMContentLoaded', function() {
    // Get references to the elements
    const startDateInput = document.getElementById('{{ form.start_date.id_for_label }}');
    const startTodayCheckbox = document.getElementById('startToday');
    
    // Function to set today's date in the format yyyy-mm-dd
    function setTodayDate() {
        const today = new Date();
        const yyyy = today.getFullYear();
        const mm = String(today.getMonth() + 1).padStart(2, '0');
        const dd = String(today.getDate()).padStart(2, '0');
        return `${yyyy}-${mm}-${dd}`;
    }
    
    // Set initial state
    if (startTodayCheckbox.checked) {
        startDateInput.value = setTodayDate();
        startDateInput.disabled = true;
    }
    
    // Add event listener for checkbox changes
    startTodayCheckbox.addEventListener('change', function() {
        if (this.checked) {
            // If checkbox is checked, set date to today and disable field
            startDateInput.value = setTodayDate();
            startDateInput.disabled = true;
        } else {
            // If unchecked, enable field but keep today's date as default
            startDateInput.disabled = false;
        }
    });
    
    // Also add an event listener to the form submit
    document.querySelector('form').addEventListener('submit', function() {
        // Make sure the date field is enabled before submitting
        // otherwise the value won't be included in the POST data
        startDateInput.disabled = false;
    });
});