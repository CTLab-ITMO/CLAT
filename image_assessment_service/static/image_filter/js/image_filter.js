/* global $, jQuery, sessionStorage,  Promise,  URLSearchParams  */
$(function () {
    // Strict session check
    const token = sessionStorage.getItem('access_token');
    const storedSessionId = sessionStorage.getItem('session_id');

    if (!token || !storedSessionId) {
        sessionStorage.clear();
        window.location.href = '/assess/users/auth/';
        return;
    }

    // Verify session ID matches token (add to AJAX headers)
    $.ajaxSetup({
        headers: {
            'Authorization': token,
            'X-Session-ID': storedSessionId  // ← Backend will verify this
        }
    });

    let current_fid = null;
    let isLoading = false;

    const showLoading = (show) => {
        isLoading = show;
        $('.btn-rating').prop('disabled', show);
        if (show) {
            $('#loadingIndicator').removeClass('d-none');
        } else {
            $('#loadingIndicator').addClass('d-none');
        }
    };

    const showError = (message) => {
        $('#errorAlert').text(message).removeClass('d-none');
        setTimeout(() => $('#errorAlert').addClass('d-none'), 5000);
    };

    const get_next_fn = function () {
        showLoading(true);

        return new Promise((resolve) => {
            $.ajax({
                url: '/assess/image_filter/get?' + $.param({token: token}),
                type: 'get',
                cache: false,
                timeout: 60000,
                success: function (data) {
                    console.log("retrieve new anno data");
                    console.dir(data)
                    current_fid=null;
                    var img_url = 'img/document.e9ed1d59.png';
                    if (data['fid'] !== 'null') {
                        current_fid = data['fid'];
                        img_url = '/assess/image_filter/file?s=' + data['file']['storage'] + '&p=' + data['file']['path'] + '&f=' + data['file']['name'];
                    }
                    $('#sample_img').attr('src', img_url);
                    if (data['metrics']) {
                        let m = data['metrics'];
                        $('#metrics_label').text(
                            'Количество ваших ответов: ' + m['user_answers']
                        );
                    }
                    resolve(current_fid);
                },
                error: function (xhr) {
                    console.log("retrieve new anno fail");
                    if (xhr.status === 401) {
                        sessionStorage.removeItem('access_token');
                        window.location.href = '/';
                    } else {
                        showError('Failed to load next image. Please try again.');
                    }
                    resolve(null);
                },
                complete: function() {
                    showLoading(false);
                }
            });
        });
    };

    const mark_fn = async function (type, fid) {
        if (isLoading) return;

        if (!fid) {
            fid = await get_next_fn();
            if (!fid) return;
        }

        showLoading(true);

        $.ajax({
            url: '/assess/image_filter/mark?'  + $.param({fid: fid, type: type, token: token}) ,
            type: 'post',
            // data: {fid: fid, type: type, token: token},
            cache: false,
            timeout: 60000,
            success: async function () {
                console.log("success mark " + type + " [" + fid + "]");
                current_fid=null;
                await updateStatsAfterRating(); // Wait for stats to update
                get_next_fn();
            },
            error: function (xhr) {
                console.log("error mark " + type + " [" + fid + "]");
                if (xhr.status === 401) {
                    sessionStorage.removeItem('access_token');
                    window.location.href = '/assess/users/auth';
                } else {
                    showError('Failed to submit rating. Please try again.');
                }
            },
            complete: function() {
                showLoading(false);
            }
        });
    };

    // Statistics Panel Management
    let statsPanelVisible = false;

    function toggleStatsPanel() {
      statsPanelVisible = !statsPanelVisible;
      $('#statsToggle i').toggleClass('bi-chevron-left bi-chevron-right');
      $('.stats-panel').toggleClass('active');
    }

    // Initialize stats panel
    $('#statsToggle').click(toggleStatsPanel);

    // Load and display statistics
    function loadStatistics() {
        $.ajax({
            url: '/assess/image_filter/stats?' + $.param({token: token}),
            type: 'get',
            success: function(data) {
                const statsList = $('.stats-list');
                statsList.empty();

                // Get current user from backend response
                const currentUser = data.current_user_nickname;

                data.stats.forEach(stat => {
                    const isCurrentUser = stat.nickname === currentUser;
                    const item = $('<li>')
                        .text(`${stat.nickname}: ${stat.count}`)
                        .toggleClass('current-user-stat', isCurrentUser)
                        .data('nickname', stat.nickname)
                        .click(function() {
                            // Remove highlight from all items
                            $('.stats-list li').removeClass('user-highlight');
                            // Add highlight to clicked item
                            $(this).addClass('user-highlight');
                        });

                    // Highlight current user by default if no other user is clicked
                    if (isCurrentUser && !$('.user-highlight').length) {
                        item.addClass('user-highlight');
                    }

                    statsList.append(item);
                });

                if (data.stats.length === 0) {
                    statsList.append('<li>No statistics available</li>');
                }
            },
            error: function(xhr) {
                $('.stats-list').html('<li>Error loading statistics</li>');
                console.error('Failed to load statistics:', xhr.statusText);
            }
        });
    }

    // Cache management
    let lastStatsUpdate = 0;
    const statsCacheDuration = 5 * 60 * 1000; // 5 minutes

    function refreshStatistics() {
        const now = Date.now();
        if (now - lastStatsUpdate > statsCacheDuration) {
            loadStatistics();
            lastStatsUpdate = now;
        }
    }

    // Update stats after rating
    function updateStatsAfterRating() {
        return new Promise((resolve) => {
            // Store which user is currently highlighted
            const highlightedUser = $('.user-highlight').data('nickname');

            // Reload statistics completely to ensure counts are accurate
            $.ajax({
                url: '/assess/image_filter/stats?' + $.param({token: token}),
                type: 'get',
                success: function(data) {
                    const statsList = $('.stats-list');
                    statsList.empty();

                    // Get current user from backend response
                    const currentUser = data.current_user_nickname;

                    data.stats.forEach(stat => {
                        const isCurrentUser = stat.nickname === currentUser;
                        const item = $('<li>')
                            .text(`${stat.nickname}: ${stat.count}`)
                            .toggleClass('current-user-stat', isCurrentUser)
                            .data('nickname', stat.nickname)
                            .click(function() {
                                $('.stats-list li').removeClass('user-highlight');
                                $(this).addClass('user-highlight');
                            });

                        if (isCurrentUser && !highlightedUser) {
                            item.addClass('user-highlight');
                        } else if (stat.nickname === highlightedUser) {
                            item.addClass('user-highlight');
                        }

                        statsList.append(item);
                    });

                    if (data.stats.length === 0) {
                        statsList.append('<li>No statistics available</li>');
                    }
                    resolve();
                },
                error: function(xhr) {
                    $('.stats-list').html('<li>Error loading statistics</li>');
                    console.error('Failed to load statistics:', xhr.statusText);
                    resolve(); // Still resolve to continue the flow
                }
            });
        });
    }

    // Initial load
    refreshStatistics();

    // Attach event after DOM loads
    document.getElementById('logout-btn')?.addEventListener('click', () => {
        sessionStorage.clear();
        window.location.replace('/assess/users/auth/');
    });

    document.getElementById('home-btn')?.addEventListener('click', () => {
        window.location.replace('/assess/main/');
    });

    // Initialize button handlers
    // Button 5
    $('#btn_5').click(function(evt) {
        mark_fn('5', current_fid);
        if (evt) evt.preventDefault();
        return false;
    });

    // Button 0
    $('#btn_0').click(function(evt) {
        mark_fn('0', current_fid);
        if (evt) evt.preventDefault();
        return false;
    });

    // Keep your existing keyboard handler
    $(window).on("keyup", function(evt) {
        if (isLoading) return;
        const key = evt.key;
        if (key >= '0' && key <= '5') {
            mark_fn(key, current_fid);
        }
    });

    // Initial load
    get_next_fn();
});