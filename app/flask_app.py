# flask_app.py
import os
import sys
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify

# Print debugging information
print("=" * 50)
print("DEBUGGING INFORMATION")
print("Python version:", sys.version)
print("Working directory:", os.getcwd())
print("Directory contents:", os.listdir('.'))
print("=" * 50)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)

# Example questions for the interface
example_questions = [
    "What are common symptoms of seasonal allergies?",
    "How can I reduce cholesterol naturally?",
    "What's the recommended daily water intake?",
    "What causes frequent headaches?",
    "How do I manage lower back pain?",
    "What are normal blood pressure ranges?"
]

# Create a fallback chatbot that works even if the main one fails
class FallbackChatBot:
    def generate_response(self, query):
        return ("I'm currently experiencing technical difficulties with my medical knowledge base. "
                "Please try again later or ask a different health-related question. "
                "Remember that this service is for educational purposes only and is not a substitute "
                "for professional medical advice.")

# Try to initialize the real chatbot with robust error handling
try:
    from src.inference import MedicalChatBot
    try:
        chatbot = MedicalChatBot()
        logger.info("Medical chatbot initialized successfully")
        CHATBOT_AVAILABLE = True
    except Exception as e:
        logger.error(f"Error initializing MedicalChatBot: {e}")
        chatbot = FallbackChatBot()
        CHATBOT_AVAILABLE = False
except Exception as e:
    logger.error(f"Error importing MedicalChatBot: {e}")
    chatbot = FallbackChatBot()
    CHATBOT_AVAILABLE = False

# Routes
@app.route('/')
def home():
    """Render the main chat interface."""
    return render_template('index.html', examples=example_questions, 
                          chatbot_status="active" if CHATBOT_AVAILABLE else "limited")

@app.route('/about')
def about():
    """Render the about page with project information."""
    return render_template('about.html')

@app.route('/health')
def health():
    """Health check endpoint for monitoring."""
    return jsonify({
        "status": "healthy",
        "chatbot_available": CHATBOT_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process chat messages and return responses."""
    try:
        data = request.json
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'status': 'error', 'message': 'No message provided'})
        
        # Log the received message
        logger.info(f"Received message: {message}")
        
        # Generate response from chatbot (works with both real and fallback)
        response = chatbot.generate_response(message)
        
        # Return the response
        return jsonify({
            'status': 'success',
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while processing your request. Please try again.'
        }), 500

# For direct execution during development
if __name__ == "__main__":
    print("Flask app is named:", app)
    print("App is located at:", __file__)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)