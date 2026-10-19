function isString(value) {
  return typeof value === "string";
}

function getCookie(cName) {
    const name = cName + "=";
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split('; ');

    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        if (c.indexOf(name) === 0) {
            return c.substring(name.length);
        }
    }
    return "";
}

function getCSRFToken(
    callback,
    sessionIdCookie = 'session_id',
) {
     const sessionId = getCookie(sessionIdCookie);
     $.ajax({
         url: '/assess/csrf/',
         type: 'post',
         contentType: 'application/json',
         data: JSON.stringify({
             session_id: sessionId
         }),
         success: function(response) {
             callback(null, response.csrf_token);
         },
         error: function(response) {
             console.error("get CSRF error:", response);
             callback(new Error(response.responseText || "Failed to get CSRF token"), null);
         }
     });
}

function withCsrfToken(callback) {
    getCSRFToken(function(error, token) {
        if (error) {
            console.error("Error:", error);
            return;
        }
        callback(token);
    });
}

function showServiceUnavailable() {
    $('#serviceUnavailableMessage').removeClass('d-none');
    $('.assess-interface').addClass('d-none');
    $('.stats-panel').addClass('d-none');
}
