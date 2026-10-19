$(document).ready(function() {
    $('#confirm_email').on('click', function (e) {
        e.preventDefault();

        const email = $('#email').val();
        const token = $('#token').val();
        if (!token) {
            showAlert("Token is required")
            return
        }

        $('#registerText').addClass('d-none');
        $('#registerSpinner').removeClass('d-none');
        $('button[type="submit"]').prop('disabled', true);


        withCsrfToken(
            (csrfToken) => $.ajax({
                url: '/assess/users/confirm_email/',
                type: 'post',
                contentType: 'application/json',
                headers: {
                    'X-CSRF-Token': csrfToken
                },
                data: JSON.stringify({
                    email: email,
                    token: token
                }),
                success: function(response) {
                    console.log("Confirm success:", response);
                    window.location.href = '/assess/users/auth/';
                },
                error: function(response) {
                    console.error("Confirm error:", response);
                    handleError(response)
                },
                complete: function() {
                    $('#registerText').removeClass('d-none');
                    $('#registerSpinner').addClass('d-none');
                    $('button[type="submit"]').prop('disabled', false);
                }
            })
        )
    })

    $('#resend_token').on('click', function (e) {
        e.preventDefault();

        $('#registerText').addClass('d-none');
        $('#registerSpinner').removeClass('d-none');
        $('button[type="submit"]').prop('disabled', true);

        const email = $('#email').val();

        withCsrfToken(
            (csrfToken) => $.ajax({
                url: '/assess/users/resend_code/',
                type: 'post',
                contentType: 'application/json',
                headers: {
                    'X-CSRF-Token': csrfToken
                },
                data: JSON.stringify({
                    email: email
                }),
                success: function(response) {
                    console.log("Resend success:", response);
                    window.location.reload();
                },
                error: function(response) {
                    console.error("Resend error:", response);
                    handleError(response)
                },
                complete: function() {
                    $('#registerText').removeClass('d-none');
                    $('#registerSpinner').addClass('d-none');
                    $('button[type="submit"]').prop('disabled', false);
                }
            })
        )
    })

    function handleError(response) {
        let errorMsg = response.responseJSON?.detail || null;
        if (!isString(errorMsg)) {
            errorMsg = errorMsg[0]?.msg || 'Request failed. Please try again.';
        }
        showAlert(errorMsg);
    }

    function showAlert(message) {
        const alertHtml = `
            <div class="alert alert-danger alert-dismissible fade show mt-3" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>`;
        $('#confirmEmailForm').after(alertHtml);
    }
});