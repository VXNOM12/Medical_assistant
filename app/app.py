from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime
import logging

# Import your medical chatbot
from src.inference import MedicalChatBot as EnhancedMedicalChatbot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize the chatbot
try:
    chatbot = EnhancedMedicalChatbot()
    logger.info("Medical chatbot initialized successfully")
except Exception as e:
    logger.error(f"Error initializing chatbot: {e}")
    chatbot = None

# Example questions for the interface
example_questions = [
    "What are common symptoms of seasonal allergies?",
    "How can I reduce cholesterol naturally?",
    "What's the recommended daily water intake?",
    "What causes frequent headaches?",
    "How do I manage lower back pain?",
    "What are normal blood pressure ranges?"
]

@app.route('/')
def home():
    """Render the main chat interface."""
    return render_template('index.html', examples=example_questions)

@app.route('/about')
def about():
    """Render the about page with project information."""
    return render_template('about.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process chat messages and return responses."""
    try:
        data = request.json
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'status': 'error', 'message': 'No message provided'})
        
        if not chatbot:
            return jsonify({
                'status': 'error', 
                'message': 'Chatbot initialization failed. Please check server logs.'
            })
        
        # Log the received message
        logger.info(f"Received message: {message}")
        
        # Generate response from your chatbot
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

if __name__ == '__main__':
    # Get port from environment variable or use 5000 as default
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)