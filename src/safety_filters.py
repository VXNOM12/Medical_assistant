import re
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class SafetyFilter:
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the safety filter with comprehensive safety checks.
        
        Args:
            project_root: Optional path to project root directory
        """
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Set project root
        self.project_root = project_root or Path(__file__).parent.parent
        
        # Define default patterns and responses FIRST - before loading config
        # This avoids the "attribute not defined" error
        self.emergency_patterns = [
            "heart attack", "stroke", "suicide", "emergency",
            "bleeding", "unconscious", "not breathing", "overdose"
        ]
        
        self.restricted_phrases = [
            "prescribe", "diagnosis", "treatment plan", 
            "medical advice", "illegal drugs"
        ]
        
        self.emergency_response = (
            "🚨 EMERGENCY: This appears to be a medical emergency. "
            "Please call emergency services (911 in the US) immediately "
            "or go to the nearest emergency room."
        )
        
        self.denial_response = (
            "I cannot provide specific medical advice, diagnoses, or prescriptions. "
            "Please consult a qualified healthcare professional for personalized "
            "medical guidance."
        )
        
        # Define default medical disclaimers
        self.medical_disclaimers = {
            'default': (
                "Disclaimer: This information is for educational purposes only. "
                "Please consult a healthcare professional for medical advice."
            )
        }
        
        # NOW load the configurations - after defaults are defined
        self._load_safety_config()
        self._load_medical_resources()

    def _load_safety_config(self):
        """Load safety configuration with default fallback."""
        try:
            config_path = self.project_root / "config" / "safety_config.yaml"
            
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self.safety_config = yaml.safe_load(f)
                    
                self.logger.info("Safety configuration loaded successfully")
                
                # Update patterns from config if available (and if config is not None)
                if self.safety_config:
                    # Use get() with our already-defined defaults
                    self.emergency_patterns = self.safety_config.get('emergency_patterns', self.emergency_patterns)
                    self.restricted_phrases = self.safety_config.get('deny_words', self.restricted_phrases)
                    self.emergency_response = self.safety_config.get('emergency_response', self.emergency_response)
                    self.denial_response = self.safety_config.get('denial_response', self.denial_response)
            else:
                self.safety_config = self._get_default_config()
                
        except Exception as e:
            self.logger.error(f"Error loading safety config: {e}")
            self.safety_config = self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Provide default safety configuration."""
        return {
            'emergency_patterns': self.emergency_patterns,
            'deny_words': self.restricted_phrases,
            'emergency_response': self.emergency_response,
            'denial_response': self.denial_response,
            'personal_info_patterns': [
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone numbers
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Emails
                r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',  # SSN
            ]
        }

    def _load_medical_resources(self):
        """Load medical resources for enhanced safety checking."""
        try:
            resources_path = self.project_root / "data" / "resources"
            
            # Create resources directory if it doesn't exist
            if not resources_path.exists():
                resources_path.mkdir(parents=True, exist_ok=True)
            
            # Load medical disclaimers
            disclaimer_path = resources_path / "medical_disclaimers.json"
            if disclaimer_path.exists():
                with open(disclaimer_path, 'r') as f:
                    self.medical_disclaimers = json.load(f)
            # No else needed - we already initialized medical_disclaimers with defaults
                
        except Exception as e:
            self.logger.warning(f"Error loading medical resources: {e}")
            # No need to set self.medical_disclaimers as we already initialized it

    # The necessary methods that EnhancedMedicalChatbot needs
    def check_input_safety(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Check if input text contains safety concerns.
        
        Args:
            text: Input text to check
            
        Returns:
            Tuple of (is_safe, message_if_not_safe)
        """
        try:
            # Basic input validation
            if not text or not isinstance(text, str):
                return False, "Invalid input received."
            
            text_lower = text.lower()
            
            # Check for emergency situations first (highest priority)
            for pattern in self.emergency_patterns:
                if pattern in text_lower:
                    self.logger.warning(f"Emergency content detected: {pattern}")
                    return False, self.emergency_response
            
            # Check for restricted medical advice
            for phrase in self.restricted_phrases:
                if phrase in text_lower:
                    self.logger.warning(f"Restricted content detected: {phrase}")
                    return False, self.denial_response
            
            # Check for personal information
            if self._contains_personal_info(text):
                return False, (
                    "For privacy and security reasons, please don't share personal "
                    "identifying information such as phone numbers, emails, or ID numbers."
                )
            
            # If all checks pass, the input is safe
            return True, None
            
        except Exception as e:
            self.logger.error(f"Error in safety check: {str(e)}")
            # Default to allowing the query but log the error
            return True, None

    def _contains_personal_info(self, text: str) -> bool:
        """
        Check if text contains personally identifiable information.
        
        Args:
            text: Text to check
            
        Returns:
            True if PII is detected, False otherwise
        """
        patterns = self.safety_config.get('personal_info_patterns', [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone numbers
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',  # SSN pattern
        ])
        
        for pattern in patterns:
            if re.search(pattern, text):
                self.logger.warning(f"PII detected in input")
                return True
                
        return False

    def validate_response(self, response: str) -> str:
        """
        Comprehensive multi-level safety validation for responses.
        
        Args:
            response: Generated response text
            
        Returns:
            Sanitized and safety-checked response
        """
        try:
            # Validate input type
            if not isinstance(response, str):
                return "Invalid response generated."
            
            # Sequence of safety checks
            safety_checks = [
                self.remove_personal_identifiers,
                self.remove_restricted_medical_advice,
                self.sanitize_medical_terminology,
                self.add_medical_disclaimer
            ]
            
            # Apply each safety check
            for check in safety_checks:
                response = check(response)
                
            return response
        
        except Exception as e:
            self.logger.error(f"Safety validation error: {e}")
            return self.medical_disclaimers.get('default', 
                "This information is for educational purposes only. "
                "Please consult a healthcare professional for medical advice."
            )

    def remove_personal_identifiers(self, text: str) -> str:
        """
        Remove potential personal identifying information.
        
        Args:
            text: Input text
            
        Returns:
            Text with personal identifiers removed
        """
        patterns = self.safety_config.get('personal_info_patterns', [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone numbers
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',  # SSN pattern
        ])
        
        for pattern in patterns:
            text = re.sub(pattern, '[REDACTED]', text, flags=re.IGNORECASE)
        
        return text

    def remove_restricted_medical_advice(self, text: str) -> str:
        """
        Remove potentially harmful medical advice.
        
        Args:
            text: Input text
            
        Returns:
            Text with restricted phrases removed
        """
        for phrase in self.restricted_phrases:
            text = re.sub(
                rf'\b{re.escape(phrase)}\b', 
                '[MEDICAL ADVICE REMOVED]', 
                text, 
                flags=re.IGNORECASE
            )
        
        return text

    def sanitize_medical_terminology(self, text: str) -> str:
        """
        Sanitize medical terminology to ensure clarity and safety.
        
        Args:
            text: Input text
            
        Returns:
            Sanitized text
        """
        # Remove potential HTML/script tags
        text = re.sub(r'<[^>]*>', '', text)
        
        # Normalize medical terminology
        text = text.replace('doctor', 'healthcare professional')
        text = text.replace('prescription', 'medical recommendation')
        
        return text

    def add_medical_disclaimer(self, text: str) -> str:
        """
        Add appropriate medical disclaimer based on text content.
        
        Args:
            text: Input text
            
        Returns:
            Text with appropriate disclaimer
        """
        # Don't add disclaimer if one is already present
        if "disclaimer" in text.lower() or "educational purposes" in text.lower():
            return text
            
        # Select disclaimer based on content
        if re.search(r'\b(symptom|condition|disease)\b', text, re.IGNORECASE):
            disclaimer = self.medical_disclaimers.get('symptoms', 
                self.medical_disclaimers['default'])
        elif re.search(r'\b(medication|drug|medicine)\b', text, re.IGNORECASE):
            disclaimer = self.medical_disclaimers.get('medications', 
                self.medical_disclaimers['default'])
        else:
            disclaimer = self.medical_disclaimers.get('default')
        
        return f"{text}\n\n{disclaimer}"

    # For backward compatibility
    def check_input(self, text: str) -> Tuple[bool, Optional[str]]:
        """Alias for check_input_safety for backward compatibility."""
        return self.check_input_safety(text)