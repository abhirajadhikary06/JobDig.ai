// Global variables
let currentChatSession = null;
let currentScrapeType = 'content';

// Initialize when DOM is ready
$(document).ready(function() {
    initChatInterface();
    initSidebarToggle();
    initMessageInput();
});

// Sidebar toggle functionality
function initSidebarToggle() {
    const sidebar = $('#chat-sidebar');
    const sidebarToggle = $('#sidebar-toggle');
    const hiddenToggle = $('#sidebar-toggle-hidden');
    const mobileSidebarToggle = $('#mobile-sidebar-toggle');
    const overlay = $('#sidebar-overlay');
    
    // Desktop sidebar toggle
    sidebarToggle.on('click', function() {
        const isCollapsed = sidebar.hasClass('collapsed');
        
        if (isCollapsed) {
            sidebar.removeClass('collapsed');
            hiddenToggle.removeClass('show');
            $(this).find('i').removeClass('fa-chevron-right').addClass('fa-chevron-left');
        } else {
            sidebar.addClass('collapsed');
            hiddenToggle.addClass('show');
            $(this).find('i').removeClass('fa-chevron-left').addClass('fa-chevron-right');
        }
    });
    
    // Hidden toggle button
    hiddenToggle.on('click', function() {
        sidebar.removeClass('collapsed');
        $(this).removeClass('show');
        sidebarToggle.find('i').removeClass('fa-chevron-right').addClass('fa-chevron-left');
    });
    
    // Mobile sidebar toggle
    mobileSidebarToggle.on('click', function() {
        sidebar.addClass('show');
        overlay.addClass('show');
    });
    
    // Close mobile sidebar
    overlay.on('click', function() {
        sidebar.removeClass('show');
        $(this).removeClass('show');
    });
}

// Message input functionality
function initMessageInput() {
    const messageInput = $('#message-input');
    
    // Auto-resize textarea
    messageInput.on('input', function() {
        autoResizeTextarea(this);
    });
    
    // Handle Enter key
    messageInput.on('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            $('#send-message-form').submit();
        }
    });
}

// Auto-resize textarea function
function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

// Authentication functionality
function initAuthToggle() {
    $('.auth-toggle .btn').on('click', function() {
        const type = $(this).data('type');
        $('.auth-toggle .btn').removeClass('active');
        $(this).addClass('active');
        
        $('.auth-form').hide();
        $(`#${type}-form`).show();
    });
}

// Chat interface functionality
function initChatInterface() {
    // Scrape type toggle
    $('.scrape-type-btn').on('click', function() {
        $('.scrape-type-btn').removeClass('active');
        $(this).addClass('active');
        currentScrapeType = $(this).data('type');
    });
    
    // Start chat form
    $('#start-chat-form').on('submit', function(e) {
        e.preventDefault();
        startChatSession();
    });
    
    // Send message form
    $('#send-message-form').on('submit', function(e) {
        e.preventDefault();
        sendMessage();
    });
    
    // Chat session selection
    $('.chat-session-item').on('click', function() {
        const sessionId = $(this).data('session-id');
        $('.chat-session-item').removeClass('active');
        $(this).addClass('active');
        loadChatSession(sessionId);
    });
    
    // Query suggestions
    $('.query-btn').on('click', function() {
        const query = $(this).data('query');
        $('#message-input').val(query).focus();
        autoResizeTextarea($('#message-input')[0]);
    });
}

function startChatSession() {
    const websiteUrl = $('#website-url').val().trim();
    
    if (!websiteUrl) {
        showAlert('Please enter a website URL', 'error');
        return;
    }
    
    const startButton = $('#start-chat-btn');
    const originalHtml = startButton.html();
    
    startButton.html('<span class="loading-spinner"></span>').prop('disabled', true);
    
    $.ajax({
        url: '/start_chat',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            website_url: websiteUrl,
            scrape_type: currentScrapeType
        }),
        success: function(response) {
            if (response.success) {
                currentChatSession = response.session_id;
                showAlert(response.message, 'success');
                $('#chat-interface').show();
                $('#start-chat-section').hide();
                $('#chat-session-url').text(websiteUrl);
                loadChatSession(response.session_id);
            } else {
                showAlert(response.error || 'Failed to start chat session', 'error');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'An error occurred';
            showAlert(error, 'error');
        },
        complete: function() {
            startButton.html(originalHtml).prop('disabled', false);
        }
    });
}

function sendMessage() {
    const message = $('#message-input').val().trim();
    
    if (!message || !currentChatSession) {
        return;
    }
    
    const sendButton = $('#send-message-btn');
    const originalHtml = sendButton.html();
    
    // Add user message to chat
    addMessageToChat('user', message);
    $('#message-input').val('');
    autoResizeTextarea($('#message-input')[0]);
    
    sendButton.html('<span class="loading-spinner"></span>').prop('disabled', true);
    
    $.ajax({
        url: '/send_message',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            session_id: currentChatSession,
            message: message
        }),
        success: function(response) {
            if (response.success) {
                addMessageToChat('assistant', response.response);
            } else {
                showAlert(response.error || 'Failed to send message', 'error');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'An error occurred';
            showAlert(error, 'error');
        },
        complete: function() {
            // Fix: Restore the original HTML content instead of text
            sendButton.html(originalHtml).prop('disabled', false);
        }
    });
}

function loadChatSession(sessionId) {
    $.ajax({
        url: `/get_chat_history/${sessionId}`,
        type: 'GET',
        success: function(response) {
            currentChatSession = sessionId;
            $('#chat-messages').empty();
            
            response.messages.forEach(function(message) {
                addMessageToChat(message.message_type, message.content);
            });
            
            $('#chat-interface').show();
            $('#start-chat-section').hide();
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to load chat session';
            showAlert(error, 'error');
        }
    });
}

function addMessageToChat(type, content) {
    const timestamp = new Date().toLocaleTimeString();
    const messageHtml = `
        <div class="message ${type}">
            <div class="message-content">${content}</div>
            <div class="message-time">${timestamp}</div>
        </div>
    `;
    
    $('#chat-messages').append(messageHtml);
    scrollToBottom();
}

function scrollToBottom() {
    const chatMessages = $('#chat-messages');
    chatMessages.scrollTop(chatMessages[0].scrollHeight);
}

// Show alert function (implement based on your alert system)
function showAlert(message, type) {
    // You can implement your preferred alert/notification system here
    console.log(`${type.toUpperCase()}: ${message}`);
    
    // Simple alert for now - replace with your notification system
    if (type === 'error') {
        alert('Error: ' + message);
    } else {
        console.log('Success: ' + message);
    }
}

// Profile functionality
function initProfileFunctionality() {
    // Resume upload
    $('#resume-upload').on('change', function() {
        const file = this.files[0];
        if (file) {
            $('#resume-filename').text(file.name);
            $('#upload-resume-btn').prop('disabled', false);
        }
    });
    
    // Add skill form
    $('#add-skill-form').on('submit', function(e) {
        e.preventDefault();
        addSkill();
    });
    
    // Delete skill buttons
    $(document).on('click', '.skill-delete', function() {
        const skillId = $(this).data('skill-id');
        deleteSkill(skillId);
    });
}

function addSkill() {
    const skillName = $('#skill-name').val().trim();
    const skillLevel = $('#skill-level').val();
    
    if (!skillName) {
        showAlert('Please enter a skill name', 'error');
        return;
    }
    
    $.ajax({
        url: '/add_skill',
        type: 'POST',
        data: {
            skill_name: skillName,
            skill_level: skillLevel
        },
        success: function() {
            location.reload();
        },
        error: function() {
            showAlert('Failed to add skill', 'error');
        }
    });
}

function deleteSkill(skillId) {
    if (confirm('Are you sure you want to delete this skill?')) {
        $.ajax({
            url: `/delete_skill/${skillId}`,
            type: 'POST',
            success: function() {
                location.reload();
            },
            error: function() {
                showAlert('Failed to delete skill', 'error');
            }
        });
    }
}

// Jobs functionality
function initJobsFunctionality() {
    // Job compatibility analysis
    $(document).on('click', '.analyze-compatibility', function() {
        const jobUrl = $(this).data('job-url');
        analyzeJobCompatibility(jobUrl);
    });
    
    // Job application tracking
    $(document).on('click', '.apply-job', function() {
        const jobUrl = $(this).data('job-url');
        window.open(jobUrl, '_blank');
    });
}

function analyzeJobCompatibility(jobUrl) {
    const button = $(`.analyze-compatibility[data-job-url="${jobUrl}"]`);
    const originalText = button.text();
    
    button.html('<span class="loading-spinner"></span> Analyzing...').prop('disabled', true);
    
    $.ajax({
        url: '/analyze_job_compatibility',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            job_url: jobUrl
        }),
        success: function(response) {
            if (response.success) {
                displayCompatibilityAnalysis(response.analysis);
            } else {
                showAlert(response.error || 'Failed to analyze job compatibility', 'error');
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'An error occurred';
            showAlert(error, 'error');
        },
        complete: function() {
            button.text(originalText).prop('disabled', false);
        }
    });
}

function displayCompatibilityAnalysis(analysis) {
    const modalHtml = `
        <div class="modal fade" id="compatibilityModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content bg-card">
                    <div class="modal-header">
                        <h5 class="modal-title">Job Compatibility Analysis</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h6>Compatibility Score</h6>
                                <div class="progress mb-3">
                                    <div class="progress-bar" style="width: ${analysis.compatibility_percentage}%">
                                        ${analysis.compatibility_percentage}%
                                    </div>
                                </div>
                                
                                <h6>Matching Skills</h6>
                                <div class="skills-container mb-3">
                                    ${analysis.matching_skills.map(skill => 
                                        `<span class="skill-tag matched">${skill}</span>`
                                    ).join('')}
                                </div>
                                
                                <h6>Missing Skills</h6>
                                <div class="skills-container mb-3">
                                    ${analysis.missing_skills.map(skill => 
                                        `<span class="skill-tag">${skill}</span>`
                                    ).join('')}
                                </div>
                            </div>
                            
                            <div class="col-md-6">
                                <h6>Preparation Suggestions</h6>
                                <ul class="list-unstyled">
                                    ${analysis.preparation_suggestions.map(suggestion => 
                                        `<li class="mb-2"><i class="fas fa-check-circle text-primary me-2"></i>${suggestion}</li>`
                                    ).join('')}
                                </ul>
                                
                                <h6>Your Strengths</h6>
                                <ul class="list-unstyled">
                                    ${analysis.strengths.map(strength => 
                                        `<li class="mb-2"><i class="fas fa-star text-warning me-2"></i>${strength}</li>`
                                    ).join('')}
                                </ul>
                            </div>
                        </div>
                        
                        <div class="mt-4">
                            <h6>Recommendations</h6>
                            <p class="text-secondary">${analysis.recommendations}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal
    $('#compatibilityModal').remove();
    
    // Add and show new modal
    $('body').append(modalHtml);
    $('#compatibilityModal').modal('show');
}

// Utility functions
function showAlert(message, type) {
    const alertClass = type === 'error' ? 'alert-danger' : `alert-${type}`;
    const alertHtml = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    $('#alert-container').html(alertHtml);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        $('.alert').alert('close');
    }, 2000);
}

function formatSkillsForDisplay(skills) {
    if (!skills || skills.length === 0) {
        return '<span class="text-muted">No skills found</span>';
    }
    
    return skills.map(skill => 
        `<span class="skill-tag">${skill}</span>`
    ).join('');
}

function calculateCompatibilityColor(percentage) {
    if (percentage >= 80) return 'success';
    if (percentage >= 60) return 'warning';
    if (percentage >= 40) return 'info';
    return 'danger';
}

// Keyboard shortcuts
$(document).on('keydown', function(e) {
    // Enter to send message in chat
    if (e.key === 'Enter' && !e.shiftKey && $('#message-input').is(':focus')) {
        e.preventDefault();
        sendMessage();
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        $('.modal').modal('hide');
    }
});

// Auto-resize textarea
$(document).on('input', 'textarea', function() {
    this.style.height = 'auto';
    this.style.height = this.scrollHeight + 'px';
});
