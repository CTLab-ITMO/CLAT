$(document).ready(function() {
    $('#registerForm').on('submit', function(e) {
        e.preventDefault();
        const form = $(this);

        // Validate passwords match
        if ($('#password').val() !== $('#confirmPassword').val()) {
            $('#confirmPassword').addClass('is-invalid');
            return;
        }

        if (form[0].checkValidity() === false) {
            e.stopPropagation();
            form.addClass('was-validated');
            return;
        }

        // Show loading state
        $('#registerText').addClass('d-none');
        $('#registerSpinner').removeClass('d-none');
        $('button[type="submit"]').prop('disabled', true);

        // Get form values
        const email = $('#email').val();
        const password = $('#password').val();

        // Submit registration
        withCsrfToken(
            (csrfToken) => $.ajax({
                url: '/assess/users/register/',
                type: 'post',
                contentType: 'application/json',
                headers: {
                    'X-CSRF-Token': csrfToken
                },
                data: JSON.stringify({
                    email: email,
                    password: password
                }),
                success: function(response) {
                    console.log("Registration success:", response);
                    window.location.href = '/assess/users/confirm_email/';
                },
                error: function(response) {
                    console.error("Registration error:", response);
                    handleRegisterError(response)
                },
                complete: function() {
                    $('#registerText').removeClass('d-none');
                    $('#registerSpinner').addClass('d-none');
                    $('button[type="submit"]').prop('disabled', false);
                }
            })
        )
    });

    function handleRegisterError(response) {
        let errorMsg = response.responseJSON?.detail || null;
        if (!isString(errorMsg)) {
            errorMsg = errorMsg[0]?.msg || 'Registration failed. Please try again.';
        }
        if (errorMsg === 'Email not confirmed') {
            window.location.href = '/assess/users/confirm_email';
            return
        }
        showAlert(errorMsg);
    }

    function resetRegisterForm() {
        $('#registerText').removeClass('d-none');
        $('#registerSpinner').addClass('d-none');
        $('button[type="submit"]').prop('disabled', false);
    }

    function showAlert(message) {
        const alertHtml = `
            <div class="alert alert-danger alert-dismissible fade show mt-3" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>`;
        $('#registerForm').after(alertHtml);
    }
});