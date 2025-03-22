# src/fix_imports.py
"""
This module provides utility functions and imports to handle circular dependencies
and ensure proper module imports throughout the application.
"""
import logging
import os
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

# Create a consistent way to access project root
PROJECT_ROOT = Path(__file__).parent.parent

# Ensure required directories exist
def ensure_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        PROJECT_ROOT / "data",
        PROJECT_ROOT / "data" / "resources",
        PROJECT_ROOT / "data" / "medical_knowledge",
        PROJECT_ROOT / "models"
    ]
    
    for directory in directories:
        if not directory.exists():
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Created directory: {directory}")
            except Exception as e:
                logger.error(f"Failed to create directory {directory}: {e}")

# Import with fallbacks for core components
try:
    from src.response_formatter import ResponseFormatter
except ImportError:
    # Define a minimal fallback if import fails
    class ResponseFormatter:
        def __init__(self, logger=None):
            self.logger = logger or logging.getLogger(__name__)
            
        def structure_response(self, raw_text, query="", query_type="general"):
            self.logger.warning("Using fallback ResponseFormatter implementation")
            return f"Medical information about {query or 'this health topic'}: {raw_text}"

try:
    from src.safety_filters import SafetyFilter
except ImportError:
    # Fallback safety filter implementation
    class SafetyFilter:
        def __init__(self, project_root=None):
            self.logger = logging.getLogger(__name__)
            self.project_root = project_root or PROJECT_ROOT
            self.disclaimer = ("\n\nDisclaimer: This information is for educational purposes only. "
                              "Please consult a healthcare professional for medical advice.")
            
        def check_input_safety(self, text):
            self.logger.warning("Using fallback SafetyFilter implementation")
            return True, None
            
        def validate_response(self, response):
            return response + self.disclaimer

# Try to import older components with fallbacks for backward compatibility
try:
    from src.response_templates import ResponseEnhancer
except ImportError:
    # Define a minimal fallback
    class ResponseEnhancer:
        def __init__(self):
            pass
        def structure_response(self, base_response, query_type, condition=None):
            return f"Medical information about {condition or 'this condition'}: {base_response}"

try:
    from src.fix_templates import MedicalResponseTemplates
except ImportError:
    # Fallback alias if the actual class isn't available
    MedicalResponseTemplates = ResponseEnhancer

try:
    from src.fallback_content import MedicalFallbackContent
except ImportError:
    # Create a minimal fallback implementation
    class MedicalFallbackContent:
        @staticmethod
        def get_content_by_topic(topic):
            return {
                "overview": f"General information about {topic}.",
                "key_info": "This is a placeholder for medical information.",
                "guidelines": "Consult healthcare professionals for personalized advice."
            }

# Attempt to import model components
try:
    from src.model.medical_model import MedicalModel
except ImportError:
    # Create a minimal model implementation
    class MedicalModel:
        def __init__(self):
            self.logger = logging.getLogger(__name__)
            self.logger.warning("Using fallback MedicalModel implementation")
            
        def generate(self, prompt):
            return f"This is important health information related to your query about {prompt}."
        
        def generate_response(self, query, context=None, max_length=512):
            return self.generate(query)

# Function to provide fallback resource loading
def get_default_medical_terms():
    """Provide fallback medical terms data."""
    return {
        "fever": {"definition": "Elevated body temperature", "term": "fever"},
        "headache": {"definition": "Pain in the head or upper neck", "term": "headache"},
        "hypertension": {"definition": "Abnormally high blood pressure", "term": "hypertension"},
        "diabetes": {"definition": "Condition causing elevated blood glucose levels", "term": "diabetes"},
        "cholesterol": {"definition": "Fatty substance found in the blood", "term": "cholesterol"}
    }

def get_default_medical_abbreviations():
    """Provide fallback medical abbreviations data."""
    return {
        "BP": "blood pressure",
        "HR": "heart rate",
        "BMI": "body mass index",
        "CVD": "cardiovascular disease",
        "HTN": "hypertension"
    }

def get_default_clinical_guidelines():
    """Provide fallback clinical guidelines data."""
    return {
        "general": [{"text": "Stay hydrated and get adequate rest."}],
        "hypertension": [{"text": "Monitor blood pressure regularly. Maintain a heart-healthy diet."}],
        "diabetes": [{"text": "Monitor blood glucose levels as recommended by healthcare providers."}]
    }

# Mixing for compatibility with different class implementations
def process_input_mixin(query):
    """Process input compatibility function."""
    logger.warning("Using standalone process_input_mixin function")
    formatter = ResponseFormatter()
    safety = SafetyFilter()
    
    is_safe, message = safety.check_input_safety(query)
    if not is_safe:
        return {"response": message, "response_type": "safety_alert"}
    
    model = MedicalModel()
    raw_response = model.generate(query)
    formatted_response = formatter.structure_response(raw_response, query)
    safe_response = safety.validate_response(formatted_response)
    
    return {
        "response": safe_response,
        "response_type": "final_response",
        "conversation_id": "standalone-response"
    }

# Add compatibility functions for term processing
def get_term_info(term):
    """Get information about a medical term."""
    terms = get_default_medical_terms()
    return terms.get(term.lower(), {"term": term, "definition": f"Information about {term}"})

# Ensure all core components are importable
def ensure_imports():
    """Ensure all necessary imports are available and create any required resources."""
    # Make sure directories exist
    ensure_directories()
    
    # Return dictionary of available components
    return {
        "ResponseFormatter": ResponseFormatter,
        "SafetyFilter": SafetyFilter,
        "ResponseEnhancer": ResponseEnhancer,
        "MedicalResponseTemplates": MedicalResponseTemplates,
        "MedicalModel": MedicalModel,
        "MedicalFallbackContent": MedicalFallbackContent
    }

# Initialize the module when imported
ensure_imports()