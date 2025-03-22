# src/medical_term_adapter.py
"""
Adapter for medical terminology processing in the medical chatbot.
Ensures compatibility between components that handle medical terms.
"""

import logging
from typing import Dict, Any, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DummyMedicalTermChecker:
    """Fallback implementation when real MedicalTermChecker is unavailable."""
    
    def __init__(self):
        """Initialize the dummy term checker."""
        logger.warning("Using DummyMedicalTermChecker - limited functionality available")
        
    def extract_medical_entities(self, text: str) -> Dict[str, Any]:
        """Extract medical entities from text using basic pattern matching."""
        entities = {"terms": {}}
        
        # Basic medical term detection
        common_terms = [
            "headache", "fever", "pain", "blood pressure", "diabetes", 
            "cholesterol", "heart", "allergy", "vitamin", "diet"
        ]
        
        text_lower = text.lower()
        for term in common_terms:
            if term in text_lower:
                entities["terms"][term] = {"definition": f"Information about {term}"}
                
        return entities
        
    def get_term_info(self, query: str) -> Dict[str, Any]:
        """Get information about medical terms in the query."""
        entities = self.extract_medical_entities(query)
        terms = list(entities.get("terms", {}).keys())
        
        if terms:
            return {"term": terms[0], "definition": f"Information about {terms[0]}"}
        return {"term": None}

def ensure_medical_term_compatibility():
    """
    Ensure compatibility between MedicalTermChecker implementations.
    Adds missing methods to the MedicalTermChecker class or creates a fallback.
    """
    try:
        # Import the MedicalTermChecker class
        try:
            from src.medical_term_processor import MedicalTermChecker
            term_checker_exists = True
        except ImportError:
            term_checker_exists = False
            logger.warning("MedicalTermChecker not found - using dummy implementation")
            # Create a global alias for the dummy implementation
            import sys
            import types
            
            # Create a module
            module = types.ModuleType("src.medical_term_processor")
            module.MedicalTermChecker = DummyMedicalTermChecker
            sys.modules["src.medical_term_processor"] = module
            
            # Now we can import it
            from src.medical_term_processor import MedicalTermChecker
        
        # Check if the get_term_info method exists (only needed for real implementation)
        if term_checker_exists and not hasattr(MedicalTermChecker, 'get_term_info'):
            # Add the get_term_info method
            def get_term_info(self, query: str) -> Dict[str, Any]:
                """
                Get information about medical terms in the query.
                
                Args:
                    query: Input query string
                    
                Returns:
                    Dictionary with term information
                """
                try:
                    # Extract medical terms from the query
                    entities = self.extract_medical_entities(query)
                    
                    # If no entities found, return default
                    if not entities or 'terms' not in entities:
                        return {'term': None}
                        
                    # Get the first term as the main term
                    terms = list(entities.get('terms', {}).keys())
                    if terms:
                        return {'term': terms[0]}
                        
                    return {'term': None}
                    
                except Exception as e:
                    logger.error(f"Error getting term info: {e}")
                    return {'term': None}
            
            # Add the method to the class
            MedicalTermChecker.get_term_info = get_term_info
            print("Added get_term_info method to MedicalTermChecker")
            
        logger.info("Medical term compatibility check completed successfully")
        
    except Exception as e:
        logger.error(f"Error in medical term compatibility: {e}")
        print(f"Unexpected error in medical term adapter: {e}")

# Run the compatibility check when this module is imported
ensure_medical_term_compatibility()