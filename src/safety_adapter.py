# src/safety_adapter.py
"""
Adapter for safety filtering in the medical chatbot.
Ensures compatibility between safety filter implementations.
"""

import logging
from typing import Tuple, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_safety_compatibility():
    """
    Ensure compatibility between SafetyFilter implementations.
    This adds missing methods to the SafetyFilter class if they don't exist.
    """
    try:
        # Import the SafetyFilter class
        from src.safety_filters import SafetyFilter
        
        # Check if the check_input_safety method exists
        if not hasattr(SafetyFilter, 'check_input_safety'):
            # Add the check_input_safety method
            def check_input_safety(self, text: str) -> Tuple[bool, Optional[str]]:
                """
                Check if input text contains safety concerns.
                
                Args:
                    text: Input text to check
                    
                Returns:
                    Tuple of (is_safe, message_if_not_safe)
                """
                try:
                    # Try using check_input if it exists
                    if hasattr(self, 'check_input'):
                        return self.check_input(text)
                    
                    # Basic validation
                    if not text or not isinstance(text, str):
                        return False, "Invalid input received."
                    
                    # Define emergency patterns
                    emergency_patterns = getattr(self, 'emergency_patterns', [
                        "heart attack", "stroke", "suicide", "emergency",
                        "bleeding", "unconscious", "not breathing", "overdose"
                    ])
                    
                    # Define emergency response
                    emergency_response = getattr(self, 'emergency_response', 
                        "This appears to be a medical emergency. Please call emergency services."
                    )
                    
                    # Define deny words
                    deny_words = getattr(self, 'deny_words', [
                        "prescribe", "diagnosis", "illegal drugs",
                        "treatment plan", "medical advice"
                    ])
                    
                    # Define denial response
                    denial_response = getattr(self, 'denial_response',
                        "I cannot provide specific medical advice, diagnoses, or prescriptions."
                    )
                    
                    # Check for emergency situations
                    text_lower = text.lower()
                    for pattern in emergency_patterns:
                        if pattern in text_lower:
                            logger.warning(f"Emergency content detected: {pattern}")
                            return False, emergency_response
                    
                    # Check for restricted content
                    for word in deny_words:
                        if word in text_lower:
                            logger.warning(f"Restricted content detected: {word}")
                            return False, denial_response
                    
                    # All checks passed
                    return True, None
                    
                except Exception as e:
                    logger.error(f"Error in safety check: {e}")
                    # Default to allowing the query but log the error
                    return True, None
            
            # Add the method to the class
            logger.info("Adding check_input_safety method to SafetyFilter")
            SafetyFilter.check_input_safety = check_input_safety
            print("Added check_input_safety method to SafetyFilter")
        
        # Check if validate_response exists
        if not hasattr(SafetyFilter, 'validate_response'):
            # Add the validate_response method
            def validate_response(self, text: str) -> str:
                """
                Validate and sanitize a response.
                
                Args:
                    text: Response text to validate
                    
                Returns:
                    Sanitized response text
                """
                import re
                
                # Basic validation
                if not text or not isinstance(text, str):
                    return "Error generating response."
                
                # Remove any potential HTML/script tags
                text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL)
                text = re.sub(r'<.*?>', '', text)
                
                # Add disclaimer if not present
                disclaimer = (
                    "\n\nDisclaimer: This information is for educational purposes only. "
                    "Please consult a healthcare professional for medical advice."
                )
                
                if "disclaimer" not in text.lower() and "educational purposes" not in text.lower():
                    text += disclaimer
                
                return text
            
            # Add the method to the class
            logger.info("Adding validate_response method to SafetyFilter")
            SafetyFilter.validate_response = validate_response
            print("Added validate_response method to SafetyFilter")
            
        logger.info("Safety compatibility check completed successfully")
        
    except ImportError as e:
        logger.error(f"Could not import SafetyFilter: {e}")
        print(f"Safety adapter error: {e}")
    except Exception as e:
        logger.error(f"Error in safety compatibility: {e}")
        print(f"Unexpected error in safety adapter: {e}")

# Run the compatibility check when this module is imported
ensure_safety_compatibility()