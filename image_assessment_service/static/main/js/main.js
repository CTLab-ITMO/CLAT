/* global $, jQuery, sessionStorage,  Promise,  URLSearchParams  */

// Immediate auth check when script loads
$(function() {
    // Immediate auth check
    const token = sessionStorage.getItem('access_token');
    const sessionId = sessionStorage.getItem('session_id');

    if (!token || !sessionId) {
        sessionStorage.clear();
        window.location.replace('/assess/users/auth/');
        return;
    }

    document.getElementById('home-btn')?.addEventListener('click', () => {
        window.location.replace('/assess/main/');
    });

    // Logout function - using jQuery for consistency
    $(document).on('click', '#logout-btn', function(e) {
        e.preventDefault();
        sessionStorage.clear();
        window.location.replace('/assess/users/auth/');
    });
});
