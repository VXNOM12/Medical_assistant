// static/js/script.js
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const chatDisplay = document.getElementById('chat-display');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const newConversationButton = document.getElementById('new-conversation-button');
    const clearButton = document.getElementById('clear-button');
    const statusIndicator = document.getElementById('status-indicator');
    const conversationIdDisplay = document.getElementById('conversation-id');
    const connectionStatus = document.getElementById('connection-status');
    const timeDisplay = document.getElementById('time-display');
    const exampleButtons = document.querySelectorAll('.example-button');
    
    // Global variables
    let isAwaitingFollowUp = false;
    let conversationId = '';
    let typingTimeout = null;
    
    // Initialize
    loadChatHistory();
    updateTime();
    setInterval(updateTime, 1000);
    
    // Event listeners
    messageInput.addEventListener('focus', handleInputFocus);
    messageInput.addEventListener('blur', handleInputBlur);
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    sendButton.addEventListener('click', sendMessage);
    newConversationButton.addEventListener('click', startNewConversation);
    clearButton.addEventListener('click', clearChat);
    
    exampleButtons.forEach(button => {
        button.addEventListener('click', function() {
            messageInput.value = this.textContent;
            messageInput.focus();
            sendMessage();
        });
    });
    
    function updateTime() {
        const now = new Date();
        timeDisplay.textContent = now.toLocaleTimeString();
    }
    
    function handleInputFocus() {
        if (messageInput.value === 'Type your health question here...') {
            messageInput.value = '';
            messageInput.style.color = '#2C3E50';
        }
    }
    
    function handleInputBlur() {
        if (messageInput.value === '') {
            messageInput.value = 'Type your health question here...';
            messageInput.style.color = '#95A5A6';
        }
    }
    
    function sendMessage() {
        const message = messageInput.value.trim();
        if (message === '' || message === 'Type your health question here...') {
            return;
        }
        
        messageInput.value = '';
        messageInput.focus();
        addMessageToChat('You', message, 'user');
        statusIndicator.textContent = 'Assistant is thinking...';
        
        fetch('/send_message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'error') {
                addMessageToChat('System', data.response, 'error');
                statusIndicator.textContent = '';
                return;
            }
            typeMessage('Assistant', data.response, data.response_type);
            conversationId = data.conversation_id;
            isAwaitingFollowUp = data.awaiting_follow_up;
            conversationIdDisplay.textContent = `Conversation: ${conversationId.slice(0, 8)}...`;
            statusIndicator.textContent = isAwaitingFollowUp ? 'Waiting for your response...' : '';
        })
        .catch(error => {
            console.error('Error:', error);
            addMessageToChat('System', 'Error connecting to the server.', 'error');
            statusIndicator.textContent = '';
        });
    }
    
    function startNewConversation() {
        fetch('/new_conversation', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                chatDisplay.innerHTML = '';
                addMessageToChat('System', 'New conversation started.', 'system');
                conversationId = data.conversation_id;
                isAwaitingFollowUp = false;
                conversationIdDisplay.textContent = `Conversation: ${conversationId.slice(0, 8)}...`;
                statusIndicator.textContent = 'New conversation started';
                setTimeout(() => statusIndicator.textContent = '', 3000);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            addMessageToChat('System', 'Error starting new conversation.', 'error');
        });
    }
    
    function clearChat() {
        fetch('/clear_chat', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                chatDisplay.innerHTML = '';
                statusIndicator.textContent = '';
                isAwaitingFollowUp = false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            addMessageToChat('System', 'Error clearing chat.', 'error');
        });
    }
    
    function loadChatHistory() {
        fetch('/get_chat_history')
        .then(response => response.json())
        .then(data => {
            chatDisplay.innerHTML = '';
            data.chat_history.forEach(item => {
                addMessageToChat(item.sender, item.message, item.message_type);
            });
            conversationId = data.conversation_id;
            isAwaitingFollowUp = data.awaiting_follow_up;
            conversationIdDisplay.textContent = `Conversation: ${conversationId.slice(0, 8)}...`;
            statusIndicator.textContent = isAwaitingFollowUp ? 'Waiting for your response...' : '';
        })
        .catch(error => {
            console.error('Error loading chat history:', error);
            addMessageToChat('System', 'Welcome to the Medical AI Assistant. How can I help you today?', 'system');
        });
    }
});
