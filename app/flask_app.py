from flask import Flask, jsonify, render_template, request
import os
import logging
import sys

# Print Python version for verification
print(f"Python version: {sys.version}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Example questions
example_questions = [
    "What are common symptoms of seasonal allergies?",
    "How can I reduce cholesterol naturally?",
    "What's the recommended daily water intake?"
]

# Simple fallback chatbot
class SimpleChatbot:
    def generate_response(self, query):
        return f"You asked: {query}. This is a placeholder response until the full model is loaded."

# Initialize a simple chatbot first
chatbot = SimpleChatbot()

@app.route('/')
def home():
    try:
        return render_template('index.html', examples=example_questions)
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        return f"Medical Chatbot is starting up! Flask app is working with Python {sys.version}."

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "python_version": sys.version,
        "chatbot_type": chatbot.__class__.__name__
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'status': 'error', 'message': 'No message provided'})
        
        # Use whatever chatbot is available
        response = chatbot.generate_response(message)
        
        return jsonify({
            'status': 'success',
            'response': response
        })
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error: {str(e)}'
        }), 500

# Try to load the full chatbot in the background
try:
    from src.inference import MedicalChatBot
    full_chatbot = MedicalChatBot()
    chatbot = full_chatbot  # Replace simple chatbot with full version
    logger.info("Successfully loaded full Medical Chatbot")
except Exception as e:
    logger.error(f"Error loading full chatbot: {e}")
    # Keep using the simple chatbot

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)