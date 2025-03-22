# src/inference_adapter.py
"""
This module provides adapter methods for the EnhancedMedicalChatbot class.
It bridges the gap between the GUI expectations and the chatbot functionality.
"""

import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DummyChatbot:
    """Fallback implementation when real chatbot is unavailable."""
    
    def __init__(self):
        """Initialize the dummy chatbot."""
        self._conversation_id = str(uuid.uuid4())
        self._conversation_history = []
        logger.warning("Using DummyChatbot - limited functionality available")
        
    def process_input(self, message: str) -> Dict[str, Any]:
        """Process input and return a basic response."""
        return {
            'response': f"I understand your question about: {message}. However, I'm currently in a limited functionality mode.",
            'response_type': 'final_response',
            'conversation_id': self._conversation_id,
            'conversation_complete': True,
            'timestamp': datetime.now().isoformat()
        }
        
    def generate_comprehensive_response(self, query: str) -> str:
        """Generate a basic response."""
        return f"I understand your question about: {query}. However, I'm currently in a limited functionality mode."

class ProcessInputMixin:
    """
    A mixin that adds the process_input method expected by the GUI to the EnhancedMedicalChatbot class.
    """
    
    def process_input(self, message: str) -> Dict[str, Any]:
        """
        Process an input message and return a response in the format expected by the GUI.
        
        Args:
            message: User's input message
            
        Returns:
            Response dictionary with fields expected by the GUI
        """
        try:
            # Create or retrieve conversation ID
            if not hasattr(self, '_conversation_id') or not self._conversation_id:
                self._conversation_id = str(uuid.uuid4())
            
            # Store conversation state if not already present
            if not hasattr(self, '_conversation_history'):
                self._conversation_history = []
                
            # Add message to conversation history
            self._conversation_history.append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.now().isoformat()
            })
            
            # Generate response using existing methods
            if hasattr(self, 'generate_comprehensive_response'):
                # Use the comprehensive response method if available
                response_text = self.generate_comprehensive_response(message)
            elif hasattr(self, 'generate_response'):
                # Fallback to simpler method if available
                response_text = self.generate_response(message)
            else:
                # Create a basic response using the message content
                response_text = f"I received your question about: {message}. I'll provide more detailed information in future updates."
                
            # Determine response type
            response_type = 'final_response'
            
            # Check if this is a follow-up question
            is_follow_up = self._detect_follow_up_question(response_text)
            if is_follow_up:
                response_type = 'follow_up_question'
            
            # Check if conversation is complete
            conversation_complete = not is_follow_up
            
            # Add response to conversation history
            self._conversation_history.append({
                'role': 'assistant',
                'content': response_text,
                'timestamp': datetime.now().isoformat()
            })
            
            # Prepare the result in the expected format
            result = {
                'response': response_text,
                'response_type': response_type,
                'conversation_id': self._conversation_id,
                'conversation_complete': conversation_complete,
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            # Log error and return error response
            logger.error(f"Error processing message: {str(e)}")
            
            return {
                'response': f"Error processing your request: {str(e)}\n\nPlease try asking your question in a different way.",
                'response_type': 'error',
                'conversation_id': getattr(self, '_conversation_id', str(uuid.uuid4())),
                'conversation_complete': True,
                'timestamp': datetime.now().isoformat()
            }
    
    def _detect_follow_up_question(self, text: str) -> bool:
        """
        Detect if a response contains a follow-up question.
        
        Args:
            text: Response text to analyze
            
        Returns:
            True if the response contains a follow-up question, False otherwise
        """
        # Check for question marks
        if '?' in text:
            # Check for question words
            question_indicators = [
                'what', 'how', 'when', 'where', 'why', 'which', 'would you', 'could you',
                'can you', 'do you', 'are you', 'did you'
            ]
            text_lower = text.lower()
            
            # Check if any question indicator is in the text
            for indicator in question_indicators:
                if indicator in text_lower:
                    return True
        
        return False
        
# Apply the mixin to the EnhancedMedicalChatbot class
def apply_process_input_mixin():
    """
    Apply the ProcessInputMixin to the EnhancedMedicalChatbot class.
    If EnhancedMedicalChatbot doesn't exist, creates a dummy implementation.
    """
    try:
        # Try to import the EnhancedMedicalChatbot class
        try:
            from src.inference import EnhancedMedicalChatbot
            chatbot_exists = True
        except ImportError:
            # Create a dummy implementation
            chatbot_exists = False
            logger.warning("EnhancedMedicalChatbot not found - using dummy implementation")
            
            # Create a global alias for the dummy implementation
            import sys
            import types
            
            # Create a module
            module = types.ModuleType("src.inference")
            module.EnhancedMedicalChatbot = DummyChatbot
            sys.modules["src.inference"] = module
            
            # Now we can import it
            from src.inference import EnhancedMedicalChatbot
        
        # Only apply if process_input is not already present
        if not hasattr(EnhancedMedicalChatbot, 'process_input'):
            # Add the process_input method to the class
            EnhancedMedicalChatbot.process_input = ProcessInputMixin.process_input
            EnhancedMedicalChatbot._detect_follow_up_question = ProcessInputMixin._detect_follow_up_question
            
            # Add necessary attributes
            original_init = EnhancedMedicalChatbot.__init__
            
            def enhanced_init(self, *args, **kwargs):
                original_init(self, *args, **kwargs)
                self._conversation_id = str(uuid.uuid4())
                self._conversation_history = []
                
            EnhancedMedicalChatbot.__init__ = enhanced_init
            
            print("Successfully added process_input method to EnhancedMedicalChatbot")
        else:
            print("EnhancedMedicalChatbot already has process_input method")
            
    except Exception as e:
        print(f"Error applying ProcessInputMixin: {str(e)}")

# Automatically apply the mixin when this module is imported
apply_process_input_mixin()