/* global $, jQuery, sessionStorage,  Promise,  URLSearchParams  */
$(document).ready(function() {
    // Form submission
    $('#loginForm').on('submit', function(e) {
        e.preventDefault();
        const form = $(this);

        // Clear previous invalid states
        $('.is-invalid').removeClass('is-invalid');

        // New validations
        const email = $('#email').val().trim();
        const password = $('#password').val();

        if (!email) {
            $('#email').addClass('is-invalid');
            return;
        }

        if (!password) {
            $('#password').addClass('is-invalid');
            return;
        }

        if (form[0].checkValidity() === false) {
            e.stopPropagation();
            form.addClass('was-validated');
            return;
        }

        // Show loading state
        $('#loginText').addClass('d-none');
        $('#loginSpinner').removeClass('d-none');
        $('button[type="submit"]').prop('disabled', true);

        // Perform login
        $.ajax({
            type: 'post',
            url: '/assess/tokens/token/',
            // contentType: 'application/x-www-form-urlencoded',
            data: {
                username: $('#email').val().trim(),
                password: $('#password').val()
            },
            success: function(response) {
                sessionStorage.setItem('access_token', response.access_token);
                sessionStorage.setItem('session_id', response.session_id);  // ← Critical!
                window.location.href = '/assess/main/';
        },
            error: handleLoginError,
            complete: resetLoginForm
        });
    });

    // Auto-focus email field
    $('#email').focus();

    // ========== Password Reset Modal Handling ========== //
    $('#forgotPasswordLink').on('click', function(e) {
        e.preventDefault();

        // Reset the modal state
        $('#resetRequestForm')[0].reset();
        $('#resetConfirmForm')[0].reset();
        $('#resetStep1').removeClass('d-none');
        $('#resetStep2').addClass('d-none');
        $('.invalid-feedback').hide();
        $('.is-invalid').removeClass('is-invalid');

        // Show the modal
        $('#resetPasswordModal').modal('show');
    });

    // Step 1: Request reset code
    $('#resetRequestForm').on('submit', function(e) {
        e.preventDefault();
        const email = $('#resetEmail').val().trim();

        if (!email) {
            $('#resetEmail').addClass('is-invalid');
            return;
        }

        // Show loading state
        $('#requestText').addClass('d-none');
        $('#requestSpinner').removeClass('d-none');
        $('#resetRequestForm button').prop('disabled', true);

        // Call your backend API
        $.ajax({
            type: 'post',
            url: '/assess/tokens/request',
            contentType: 'application/json',
            data: JSON.stringify({email: $('#resetEmail').val().trim()}),
            success: function() {
                // Switch to step 2
                $('#resetStep1').addClass('d-none');
                $('#resetStep2').removeClass('d-none');
                // Store email for step 2
                $('#resetStep2').data('email', email);
            },
            error: function(xhr) {
                const errorMsg = xhr.responseJSON?.detail || 'Failed to send reset code';
                alert(errorMsg);
            },
            complete: function() {
                $('#requestText').removeClass('d-none');
                $('#requestSpinner').addClass('d-none');
                $('#resetRequestForm button').prop('disabled', false);
            }
        });
    });

    // Step 2: Confirm reset
    $('#resetConfirmForm').on('submit', function(e) {
        e.preventDefault();
        const code = $('#resetCode').val().trim();
        const newPassword = $('#newPassword').val();
        const email = $('#resetStep2').data('email');

        // Validation
        let valid = true;
        if (!code) {
            $('#resetCode').addClass('is-invalid');
            valid = false;
        }
        if (!newPassword || newPassword.length < 8) {
            $('#newPassword').addClass('is-invalid');
            valid = false;
        }
        if (!valid) return;

        // Show loading state
        $('#confirmText').addClass('d-none');
        $('#confirmSpinner').removeClass('d-none');
        $('#resetConfirmForm button').prop('disabled', true);

        // Call your backend API
        $.ajax({
            type: 'post',
            url: '/assess/tokens/confirm',
            contentType: 'application/json',
            data: JSON.stringify({
                token: $('#resetCode').val().trim(),
                new_password: $('#newPassword').val()
            }),
            success: function() {
                alert('Password updated successfully!');
                $('#resetPasswordModal').modal('hide');
            },
            error: function(xhr) {
                const errorMsg = xhr.responseJSON?.detail || 'Failed to reset password';
                alert(errorMsg);
            },
            complete: function() {
                $('#confirmText').removeClass('d-none');
                $('#confirmSpinner').addClass('d-none');
                $('#resetConfirmForm button').prop('disabled', false);
            }
        });
    });

    // Clear validation on input
    $('.modal input').on('input', function() {
        $(this).removeClass('is-invalid');
    });

    // ========== Helper Functions ========== //
    function handleLoginError(xhr) {
        let errorMsg = xhr.responseJSON?.detail || 'Login failed. Please try again.';
        if (xhr.status === 401) {
            errorMsg = 'Invalid email or password';
        }
        showAlert(errorMsg);
    }

    function resetLoginForm() {
        $('#loginText').removeClass('d-none');
        $('#loginSpinner').addClass('d-none');
        $('button[type="submit"]').prop('disabled', false);
    }

    function showAlert(message) {
        const alertHtml = `
            <div class="alert alert-danger alert-dismissible fade show mt-3" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>`;
        $('#loginForm').after(alertHtml);
    }
});