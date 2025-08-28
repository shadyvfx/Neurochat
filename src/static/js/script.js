// Modal popup functions for login/signup
function openPopup(page) {
    const modal = document.getElementById("modalOverlay");
    const iframe = document.getElementById("modalIframe");

    iframe.src = page; // Load login.html or signup.html
    modal.classList.add("show");

    // Prevent scrolling background
    document.body.style.overflow = 'hidden';
}

function closePopup() {
    const modal = document.getElementById("modalOverlay");
    const iframe = document.getElementById("modalIframe");

    modal.classList.remove("show");
    iframe.src = ""; // Clear iframe to stop any running code

    // Re-enable scrolling
    document.body.style.overflow = '';
}

// Listen for messages from iframe (login success)
window.addEventListener('message', function(event) {
    if (event.data && event.data.action === 'redirect') {
        closePopup(); // Close the popup first
        window.location.replace(event.data.url); // Then redirect main window
    }
});

// Chat functionality for index page
let currentMode = null;
let awaitingModeSelection = true;
let chatInitialized = false;
let isAuthenticated = false;

// Get CSRF token function
function getCSRFToken() {
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    return csrfMeta ? csrfMeta.getAttribute('content') : null;
}

// Check authentication status
async function checkAuthStatus() {
    try {
        const response = await fetch('/guest/status');
        const data = await response.json();
        
        if (data.authenticated) {
            isAuthenticated = true;
            // User is authenticated, redirect to dashboard
            window.location.href = '/dashboard';
            return;
        }
        
        // User is not authenticated, continue with guest mode
        isAuthenticated = false;
    } catch (error) {
        console.error('Error checking auth status:', error);
        isAuthenticated = false;
    }
}

// Initialize chat when page loads (only on index page)
window.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the index page (has chatWindow element)
    if (document.getElementById('chatWindow')) {
        // Check authentication status first
        checkAuthStatus().then(() => {
            if (!isAuthenticated) {
                setTimeout(() => {
                    showWelcomeMessage();
                }, 1000); // Small delay for natural feel
            }
        });
    }
});

function showWelcomeMessage() {
    showTypingIndicator();
    
    setTimeout(() => {
        hideTypingIndicator();
        addMessage('ai', "Hi, I'm Neurochat — your friendly AI companion here to listen or talk whenever you need. Would you prefer me to mainly listen and provide gentle support, or would you like me to actively respond and engage in conversation with you?\n\nSimply type 'listen' or 'talk' to get started.");
        
        // Enable input for mode selection
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.disabled = false;
            messageInput.placeholder = "Type 'listen' or 'talk' to continue...";
            messageInput.focus();
        }
    }, 2000); // 2 second typing delay
}

async function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    if (!messageInput) return;
    
    const message = messageInput.value.trim().toLowerCase();
    
    if (!message) return;
    
    // Add user message to chat
    addMessage('user', messageInput.value.trim());
    messageInput.value = '';
    
    if (awaitingModeSelection) {
        handleModeSelection(message);
    } else if (chatInitialized && currentMode) {
        handleChatMessage(message);
    }
}

async function handleModeSelection(message) {
    if (message.includes('listen') || message === 'l') {
        await setMode('listen');
    } else if (message.includes('talk') || message.includes('respond') || message === 't') {
        await setMode('talk');
    } else {
        // Invalid response
        showTypingIndicator();
        setTimeout(() => {
            hideTypingIndicator();
            addMessage('ai', "I didn't quite understand that. Please type 'listen' if you'd like me to mainly listen and provide gentle support, or 'talk' if you'd like me to actively engage in conversation with you.");
        }, 1000);
    }
}

async function setMode(mode) {
    try {
        showTypingIndicator();
        
        const headers = { 'Content-Type': 'application/json' };
        const csrfToken = getCSRFToken();
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
        
        const response = await fetch('/auth/chat/mode', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ mode: mode })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentMode = mode;
            awaitingModeSelection = false;
            chatInitialized = true;
            
            setTimeout(() => {
                hideTypingIndicator();
                addMessage('ai', data.message);
                
                // Update placeholder for normal chat
                const messageInput = document.getElementById('messageInput');
                if (messageInput) {
                    messageInput.placeholder = "Share what's on your mind...";
                    messageInput.focus();
                }
            }, 1500);
        } else {
            throw new Error(data.error || 'Failed to set mode');
        }
    } catch (error) {
        console.error('Error setting mode:', error);
        hideTypingIndicator();
        addMessage('ai', "I'm having trouble setting up our conversation. Please try typing 'listen' or 'talk' again.");
    }
}

async function handleChatMessage(message) {
    try {
        console.log('handleChatMessage called with:', message);
        
        // Check if user is authenticated
        if (isAuthenticated) {
            // User is authenticated, proceed with chat
            await sendAuthenticatedMessage(message);
            return;
        }
        
        // Show typing indicator immediately
        console.log('About to show typing indicator...');
        showTypingIndicator();
        
        const headers = { 'Content-Type': 'application/json' };
        const csrfToken = getCSRFToken();
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
        
        console.log('Sending message to backend...');
        const response = await fetch('/auth/chat/message', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        console.log('Backend response:', data);
        
        if (response.ok) {
            // Hide typing indicator first
            console.log('Hiding typing indicator...');
            hideTypingIndicator();
            
            // Add AI response with a small delay for natural feel
            setTimeout(() => {
                addMessage('ai', data.message);
            }, 500); // 0.5 second delay after typing stops
        } else {
            // Check if it's a guest time expiration error
            if (response.status === 403 && data.expired) {
                hideTypingIndicator();
                addMessage('ai', data.message);
                // Show the expired message overlay
                if (typeof showGuestExpired === 'function') {
                    showGuestExpired();
                }
            } else {
                throw new Error(data.error || 'Failed to send message');
            }
        }
    } catch (error) {
        console.error('Error sending message:', error);
        hideTypingIndicator();
        addMessage('ai', "I apologize, but I'm having trouble responding right now. Please try again.");
    }
}

// Function to send messages for authenticated users
async function sendAuthenticatedMessage(message) {
    try {
        showTypingIndicator();
        
        const headers = { 'Content-Type': 'application/json' };
        const csrfToken = getCSRFToken();
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
        
        const response = await fetch('/auth/chat/message', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            hideTypingIndicator();
            setTimeout(() => {
                addMessage('ai', data.message);
            }, 500);
        } else {
            throw new Error(data.error || 'Failed to send message');
        }
    } catch (error) {
        console.error('Error sending authenticated message:', error);
        hideTypingIndicator();
        addMessage('ai', "I apologize, but I'm having trouble responding right now. Please try again.");
    }
}

function addMessage(sender, message) {
    const chatWindow = document.getElementById('chatWindow');
    if (!chatWindow) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender} message-animated`;
    
    const chatDiv = document.createElement('div');
    chatDiv.className = 'chat';
    chatDiv.textContent = message;
    
    messageDiv.appendChild(chatDiv);
    chatWindow.appendChild(messageDiv);
    
    // Scroll to bottom smoothly
    setTimeout(() => {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }, 10); // Small delay to ensure DOM is updated
    
    // Remove animation class after animation completes
    setTimeout(() => {
        messageDiv.classList.remove('message-animated');
    }, 300);
}

function showTypingIndicator() {
    console.log('showTypingIndicator called');
    const chatWindow = document.getElementById('chatWindow');
    if (!chatWindow) {
        console.error('chatWindow not found');
        return;
    }
    
    console.log('chatWindow found, showing typing indicator');
    
    // Remove any existing typing indicator
    const existingTyping = chatWindow.querySelector('.typing-indicator');
    if (existingTyping) {
        existingTyping.remove();
    }
    
    // Create typing indicator element with the correct structure
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.innerHTML = `
        <span></span>
        <span></span>
        <span></span>
    `;
    
    // Add to chat window
    chatWindow.appendChild(typingDiv);
    console.log('Typing indicator added to chat window');
    
    // Scroll to bottom to show typing indicator
    setTimeout(() => {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }, 10);
}

function hideTypingIndicator() {
    console.log('hideTypingIndicator called');
    const chatWindow = document.getElementById('chatWindow');
    if (!chatWindow) {
        console.error('chatWindow not found in hideTypingIndicator');
        return;
    }
    
    // Remove typing indicator from chat window
    const typingIndicator = chatWindow.querySelector('.typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
        console.log('Typing indicator removed');
    } else {
        console.log('No typing indicator found to remove');
    }
}

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Handle Enter key in textarea (only if messageInput exists)
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        // Multiple event listeners for cross-browser compatibility
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Safari mobile compatibility - keypress event
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Additional mobile compatibility - keyup event
        messageInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Touch events for mobile devices
        messageInput.addEventListener('touchend', function(e) {
            // Focus the textarea when touched (helps with mobile keyboard)
            this.focus();
        });

        // Handle textarea auto-resize
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });

        // Ensure textarea is focused and ready for mobile input
        messageInput.addEventListener('focus', function() {
            // Scroll to bottom to ensure textarea is visible on mobile
            setTimeout(() => {
                this.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 100);
        });
    }
});

function logout() {
    // Redirect to index.html
    window.location.href = 'index.html';
}

// Theme toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('themeToggle');
    const switchLabel = document.querySelector('.switch-label');
    
    // Check for saved theme preference or default to dark
    const currentTheme = localStorage.getItem('theme') || 'dark';
    document.body.className = currentTheme;
    
    // Set toggle state based on current theme
    if (currentTheme === 'light') {
        themeToggle.checked = true;
        switchLabel.textContent = 'Light Mode';
    } else {
        themeToggle.checked = false;
        switchLabel.textContent = 'Dark Mode';
    }
    
    // Theme toggle event listener
    themeToggle.addEventListener('change', function() {
        if (this.checked) {
            document.body.className = 'light';
            localStorage.setItem('theme', 'light');
            switchLabel.textContent = 'Light Mode';
        } else {
            document.body.className = 'dark';
            localStorage.setItem('theme', 'dark');
            switchLabel.textContent = 'Dark Mode';
        }
    });
});