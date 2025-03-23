// Main JavaScript file for Medical AI Assistant

// Function to format markdown-like content in chat messages
function formatMessageContent() {
    document.querySelectorAll('.assistant-message .message-content').forEach(content => {
        // Replace markdown-style headers
        content.innerHTML = content.innerHTML.replace(/\n## (.*?)(\n|$)/g, '<h5>$1</h5>');
        content.innerHTML = content.innerHTML.replace(/\n### (.*?)(\n|$)/g, '<h6>$1</h6>');
        
        // Replace bullet points
        content.innerHTML = content.innerHTML.replace(/\n\s*\* (.*?)(\n|$)/g, '<ul><li>$1</li></ul>');
        content.innerHTML = content.innerHTML.replace(/\n\s*- (.*?)(\n|$)/g, '<ul><li>$1</li></ul>');
        
        // Merge adjacent ul elements
        content.innerHTML = content.innerHTML.replace(/<\/ul>\s*<ul>/g, '');
        
        // Replace double line breaks with paragraphs
        content.innerHTML = content.innerHTML.replace(/\n\n/g, '</p><p>');
        
        // Handle special sections
        if (content.innerHTML.includes('Disclaimer:')) {
            const parts = content.innerHTML.split('Disclaimer:');
            content.innerHTML = parts[0] + '<div class="disclaimer"><strong>Disclaimer:</strong> ' + parts[1] + '</div>';
        }
    });
}

// Add event listener to format content when new messages are added
const observer = new MutationObserver(mutations => {
    mutations.forEach(mutation => {
        if (mutation.addedNodes.length) {
            formatMessageContent();
        }
    });
});

// Start observing the chat container when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    if (chatContainer) {
        observer.observe(chatContainer, { childList: true, subtree: true });
        formatMessageContent(); // Format initial content
    }
});