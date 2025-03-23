# app.py
import sys
from pathlib import Path
import threading
import time
import json
import uuid
import waitress
from flask import Flask, render_template, request, jsonify, session

# Add project root to Python path - MUST BE BEFORE OTHER IMPORTS
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

# Import the fix and integration modules first
from src.fix_templates import MedicalResponseTemplates
from src.fix_imports import ensure_imports
from src.inference_adapter import apply_process_input_mixin
from src.safety_adapter import ensure_safety_compatibility
from src.medical_term_adapter import ensure_medical_term_compatibility
from src.integration import ensure_component_compatibility

# Now import remaining modules
from src.response_templates import ResponseEnhancer
from src.inference import EnhancedMedicalChatbot as MedicalChatBot
from src.model.medical_model import MedicalModel

app = Flask(__name__)
app.secret_key = str(uuid.uuid4())  # Generate a random secret key

# Initialize the medical chatbot
try:
    bot = MedicalChatBot()
    print("Successfully initialized MedicalChatBot")
except Exception as e:
    print(f"Error initializing MedicalChatBot: {e}")
    sys.exit(1)

# Example questions for the UI
EXAMPLE_QUESTIONS = [
    "What are common symptoms of seasonal allergies?",
    "How can I reduce cholesterol naturally?",
    "What's the recommended daily water intake?",
    "What causes frequent headaches?",
    "How do I manage lower back pain?",
    "What are normal blood pressure ranges?"
]

@app.route('/')
def index():
    """Render the main page of the application"""
    # Initialize a new session if needed
    if 'conversation_id' not in session:
        session['conversation_id'] = str(uuid.uuid4())
        session['awaiting_follow_up'] = False
        session['conversation_active'] = False
        session['chat_history'] = []
    
    return render_template('index.html', 
                          example_questions=EXAMPLE_QUESTIONS, 
                          conversation_id=session['conversation_id'])

@app.route('/send_message', methods=['POST'])
def send_message():
    """Process a user message and return the assistant's response"""
    data = request.json
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({"error": "Empty message"})
    
    # Add user message to chat history
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    session['chat_history'].append({
        'sender': 'You',
        'message': user_message,
        'message_type': 'user'
    })
    
    # Process the user message
    try:
        # Get response based on conversation state
        if session.get('awaiting_follow_up', False):
            # This is a response to a follow-up question
            response_data = bot.process_input(user_message)
        else:
            # This is a new query or continuation of conversation
            response_data = bot.process_input(user_message)
            
        # Update conversation tracking
        if 'conversation_id' in response_data and response_data['conversation_id']:
            session['conversation_id'] = response_data['conversation_id']
            session['conversation_active'] = True
        
        # Update awaiting_follow_up state
        session['awaiting_follow_up'] = (response_data.get('response_type') == 'follow_up_question')
        
        # Update conversation completion status
        if response_data.get('conversation_complete', False):
            session['awaiting_follow_up'] = False
                
        # Get the response text
        response = response_data.get('response', "Error processing your request.")
        
        # Determine message type based on response type
        response_type = response_data.get('response_type', 'final_response')
        
        # Add to chat history
        session['chat_history'].append({
            'sender': 'Assistant',
            'message': response,
            'message_type': response_type
        })
        
        # Save modified session data
        session.modified = True
        
        return jsonify({
            'status': 'success',
            'response': response,
            'response_type': response_type,
            'conversation_id': session['conversation_id'],
            'awaiting_follow_up': session['awaiting_follow_up']
        })
        
    except Exception as e:
        error_message = f"Error: {str(e)}\n\nPlease try asking your question in a different way."
        
        # Add error to chat history
        session['chat_history'].append({
            'sender': 'System',
            'message': error_message,
            'message_type': 'error'
        })
        
        # Reset conversation state
        session['awaiting_follow_up'] = False
        session.modified = True
        
        return jsonify({
            'status': 'error',
            'response': error_message,
            'response_type': 'error'
        })

@app.route('/new_conversation', methods=['POST'])
def new_conversation():
    """Start a new conversation and reset state"""
    # Reset conversation manager in the bot
    if hasattr(bot, 'conversation_manager'):
        bot.conversation_manager.reset_conversation()
        
    # Reset session tracking variables
    session['conversation_id'] = str(uuid.uuid4())
    session['awaiting_follow_up'] = False
    session['conversation_active'] = False
    session['chat_history'] = [{
        'sender': 'System',
        'message': 'New conversation started.',
        'message_type': 'system'
    }]
    session.modified = True
    
    return jsonify({
        'status': 'success',
        'message': 'New conversation started',
        'conversation_id': session['conversation_id']
    })

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    """Clear the chat history while maintaining the conversation state"""
    # Keep the conversation ID but clear the messages
    session['chat_history'] = []
    session.modified = True
    
    return jsonify({
        'status': 'success',
        'message': 'Chat cleared'
    })

@app.route('/get_chat_history', methods=['GET'])
def get_chat_history():
    """Return the current chat history"""
    if 'chat_history' not in session:
        session['chat_history'] = []
        
    return jsonify({
        'chat_history': session['chat_history'],
        'conversation_id': session.get('conversation_id', ''),
        'awaiting_follow_up': session.get('awaiting_follow_up', False)
    })

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
