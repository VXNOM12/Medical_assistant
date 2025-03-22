# src/inference.py
from typing import Dict, Any, Optional, List
import logging
import random
import uuid
import re
from pathlib import Path
from datetime import datetime

# Try to import components with fallback options
try:
    from src.data_processing import MedicalDataProcessor as DataProcessor
except ImportError:
    # Create fallback DataProcessor
    class DataProcessor:
        def __init__(self):
            self.logger = logging.getLogger(__name__)
            self.logger.warning("Using fallback DataProcessor")
            
        def preprocess_text(self, text):
            return text.strip()

try:
    from src.question_analyzer import QuestionAnalyzer
except ImportError:
    # Create fallback QuestionAnalyzer
    class QuestionAnalyzer:
        def __init__(self):
            self.logger = logging.getLogger(__name__)
            self.logger.warning("Using fallback QuestionAnalyzer")
            
        def analyze_query(self, query):
            return {'category': 'general', 'needs_clarification': False}
            
        def categorize_query(self, query):
            return 'general'

try:
    from src.medical_term_processor import MedicalTermChecker
except ImportError:
    # Create fallback MedicalTermChecker
    class MedicalTermChecker:
        def __init__(self):
            self.logger = logging.getLogger(__name__)
            self.logger.warning("Using fallback MedicalTermChecker")
            
        def extract_medical_entities(self, text):
            return {'terms': {}}
            
        def get_term_info(self, query):
            return {'term': None}

try:
    from src.model.medical_model import MedicalModel
except ImportError:
    # Create fallback MedicalModel
    class MedicalModel:
        def __init__(self):
            self.logger = logging.getLogger(__name__)
            self.logger.warning("Using fallback MedicalModel")
            
        def generate_response(self, query, context=None, max_length=512):
            return f"Information about {query}."
            
        def generate(self, prompt):
            return f"Information about {prompt}."

try:
    from src.response_templates import ResponseEnhancer
except ImportError:
    # Create fallback ResponseEnhancer
    class ResponseEnhancer:
        def __init__(self):
            self.logger = logging.getLogger(__name__)
            self.logger.warning("Using fallback ResponseEnhancer")
            
        def structure_response(self, base_response, query_type, condition=None):
            condition_text = f" about {condition}" if condition else ""
            return f"Medical information{condition_text}: {base_response}"

try:
    from src.data_retriever import MedicalDataRetriever
except ImportError:
    # Create fallback MedicalDataRetriever
    class MedicalDataRetriever:
        def __init__(self):
            self.logger = logging.getLogger(__name__)
            self.logger.warning("Using fallback MedicalDataRetriever")
            
        def get_enhanced_query(self, query):
            return f"Provide detailed medical information about {query}"

# Import formatter and safety filter - these are critical
from src.response_formatter import ResponseFormatter
from src.safety_filters import SafetyFilter

# Import utility functions
from src.fix_imports import ensure_imports, get_default_medical_terms

class EnhancedMedicalChatbot:
    def __init__(self):
        """Initialize the enhanced medical chatbot with all necessary components."""
        try:
            # Setup logging
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(__name__)
            
            # Set project root
            self.project_root = Path(__file__).parent.parent
            
            # Initialize core components
            self.logger.info("Initializing data processor...")
            self.data_processor = DataProcessor()
            
            self.logger.info("Initializing question analyzer...")
            self.question_analyzer = QuestionAnalyzer()
            
            self.logger.info("Initializing medical term processor...")
            self.medical_term_processor = MedicalTermChecker()
            
            self.logger.info("Initializing language model...")
            self.language_model = MedicalModel()
            
            self.logger.info("Initializing data retriever...")
            self.data_retriever = MedicalDataRetriever()
            
            # Initialize response enhancement components
            print("About to initialize response enhancer")
            self.response_enhancer = ResponseEnhancer()
            print("Response enhancer initialized successfully")
            
            self.logger.info("Initializing response formatter...")
            self.response_formatter = ResponseFormatter(logger=self.logger)
            
            self.logger.info("Initializing safety filter...")
            self.safety_filter = SafetyFilter(project_root=self.project_root)
            
            # Initialize conversation tracking
            self._conversation_id = str(uuid.uuid4())
            self._conversation_history = []
            
            # Cache of medical terms for efficient lookups
            self._medical_terms_cache = get_default_medical_terms()
            
            self.logger.info("Enhanced Medical ChatBot initialized successfully")
            
        except Exception as e:
            # Enhanced error reporting
            import traceback
            print(f"Detailed initialization error: {e}")
            print(f"Error occurred in: {traceback.format_exc()}")
            raise

    def generate_comprehensive_response(self, query: str) -> str:
        """
        Generate a comprehensive medical response with integrated components.
        
        Args:
            query: User's medical query
            
        Returns:
            Comprehensive medical response
        """
        try:
            # Input validation
            if not query or not isinstance(query, str):
                return "Please provide a valid medical query."
            
            # Safety check first
            safety_check, safety_message = self.safety_filter.check_input_safety(query)
            if not safety_check and safety_message:
                return safety_message
            
            # Preprocess and analyze query
            processed_query = self.data_processor.preprocess_text(query)
            query_analysis = self.question_analyzer.analyze_query(processed_query)
            query_type = query_analysis.get('category', 'general')
            
            # Extract medical entities and context
            entities = self.medical_term_processor.extract_medical_entities(processed_query)
            
            # Determine if clarification is needed
            if query_analysis.get('needs_clarification', False):
                follow_up_questions = query_analysis.get('suggested_questions', [])
                if follow_up_questions:
                    return random.choice(follow_up_questions)
            
            # Generate base response
            base_response = self.language_model.generate_response(
                query=processed_query,
                context=entities,
                max_length=512
            )

            # Create enhanced query with dataset knowledge
            enhanced_query = self.data_retriever.get_enhanced_query(processed_query)

            # Generate base response with the enhanced query
            if enhanced_query != processed_query:
                try:
                    enhanced_response = self.language_model.generate_response(
                        query=enhanced_query,
                        context=entities,
                        max_length=512
                    )
                    # Use enhanced response if it's substantive
                    if len(enhanced_response) > len(base_response) * 0.8:
                        base_response = enhanced_response
                except Exception as e:
                    self.logger.warning(f"Error generating enhanced response: {e}")
            
            # Enhance response structure
            enhanced_response = self.response_enhancer.structure_response(
                base_response, 
                query_type, 
                condition=self.medical_term_processor.get_term_info(query).get('term')
            )
            
            # Apply safety filters
            final_response = self.safety_filter.validate_response(enhanced_response)
            
            return final_response
        
        except Exception as e:
            self.logger.error(f"Comprehensive response generation error: {e}")
            return (
                "I apologize, but I'm having trouble processing your query. "
                "Could you rephrase your question?"
            )
        
    def generate_response(self, query: str) -> str:
        """
        Generate a comprehensive medical information response with improved
        formatting and safety checks.
        """
        try:
            # Input validation
            if not isinstance(query, str) or not query.strip():
                return "Please provide a specific health-related question."
            
            query = query.strip()
            
            # Safety check first
            is_safe, safety_message = self.safety_filter.check_input_safety(query)
            if not is_safe and safety_message:
                return safety_message
            
            # Determine query type for appropriate response formatting
            query_type = self._determine_query_type(query)
            
            # Create enhanced prompt for better response generation
            prompt = self._prepare_medical_prompt(query)
            
            # Generate model response with error handling
            try:
                response = self._get_weighted_response(prompt)
            except Exception as model_error:
                self.logger.error(f"Model generation error: {str(model_error)}")
                # If model generation fails, use a fallback response
                response = f"I'm having trouble generating specific information about {query}. Let me provide some general information instead."
            
            # Format the response using the ResponseFormatter
            formatted_response = self.response_formatter.structure_response(
                raw_text=response,
                query=query,
                query_type=query_type
            )
            
            # Validate response with safety filter
            final_response = self.safety_filter.validate_response(formatted_response)
            
            return final_response
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return ("I apologize, but I encountered an error processing your request. "
                "Please try asking your question in a different way.") + "\n\nDisclaimer: This information is for educational purposes only. Please consult a healthcare professional for personalized medical guidance."

    def _determine_query_type(self, query: str) -> str:
        """
        Determine the type of medical query.
        
        Args:
            query: User's medical query
            
        Returns:
            Query type category
        """
        query_lower = query.lower()
        
        # Define keywords for different query types
        keywords = {
            "symptoms": ["symptom", "feel", "experiencing", "signs", "notice"],
            "treatment": ["treat", "cure", "therapy", "manage", "handle", "deal with"],
            "prevention": ["prevent", "avoid", "reduce risk", "protect", "stop"],
            "water_intake": ["water intake", "hydration", "drink water", "daily water"],
            "blood_pressure": ["blood pressure", "hypertension", "bp reading"],
            "cholesterol": ["cholesterol", "lipids", "hdl", "ldl", "triglyceride"],
            "seasonal_allergies": ["allergy", "allergies", "seasonal", "hay fever", "pollen"]
        }
        
        # Check query against keywords
        for qtype, words in keywords.items():
            if any(word in query_lower for word in words):
                return qtype
                
        return "general"
    
    def _prepare_medical_prompt(self, query: str) -> str:
        """
        Prepare a specialized medical prompt for the model.
        
        Args:
            query: User's medical query
            
        Returns:
            Enhanced prompt for the model
        """
        # Query type-specific prompts
        templates = {
            "general": (
                f"Provide comprehensive, educational information about {query}.\n\n"
                f"Include the following sections:\n"
                f"- Overview\n"
                f"- Key Information\n"
                f"- Guidelines\n"
                f"- Important Considerations\n\n"
                f"Focus on factual medical information. Use clear, simple language."
            ),
            "symptoms": (
                f"Provide educational information about symptoms related to {query}.\n\n"
                f"Include the following sections:\n"
                f"- Common Symptoms\n"
                f"- Potential Causes\n"
                f"- When to Seek Medical Care\n"
                f"- Self-Care Measures\n\n"
                f"Focus on general patterns rather than specific diagnoses."
            ),
            "treatment": (
                f"Describe general treatment approaches for {query}.\n\n"
                f"Include the following sections:\n"
                f"- Overview of Management\n"
                f"- Common Treatment Options\n"
                f"- Lifestyle Considerations\n"
                f"- Important Precautions\n\n"
                f"Focus on educational information rather than specific medical advice."
            ),
            "prevention": (
                f"Provide information about preventing or reducing risk related to {query}.\n\n"
                f"Include the following sections:\n"
                f"- Preventive Strategies\n"
                f"- Risk Factors\n"
                f"- Lifestyle Recommendations\n"
                f"- Monitoring Guidelines\n\n"
                f"Focus on evidence-based preventive measures."
            )
        }
        
        # Determine query type
        query_type = self._determine_query_type(query)
        
        # Use appropriate template or default to general
        return templates.get(query_type, templates["general"])
    
    def _get_weighted_response(self, prompt: str) -> str:
        """
        Get response from the language model.
        
        Args:
            prompt: Enhanced prompt for the model
            
        Returns:
            Generated response text
        """
        try:
            # Use the language model to generate a response
            if hasattr(self.language_model, 'generate'):
                return self.language_model.generate(prompt)
            elif hasattr(self.language_model, 'generate_response'):
                return self.language_model.generate_response(query=prompt, max_length=512)
            else:
                self.logger.warning("No suitable generation method found in language model")
                return f"Information about {prompt.split()[-1]}."
        except Exception as e:
            self.logger.error(f"Error getting model response: {e}")
            return f"General information about {prompt.split()[-1]}."

    def handle_conversation(self, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Manage multi-turn medical conversations.
        
        Args:
            conversation_history: Optional list of previous conversation messages
            
        Returns:
            Conversation response dictionary
        """
        try:
            # If no conversation history, start a new conversation
            if not conversation_history:
                return {
                    'response_type': 'initial',
                    'response': "How can I help you with your medical query today?",
                    'conversation_id': str(uuid.uuid4())
                }
            
            # Get the latest message
            latest_message = conversation_history[-1]
            
            # Process the message
            response = self.generate_comprehensive_response(latest_message.get('content', ''))
            
            return {
                'response_type': 'follow_up',
                'response': response,
                'conversation_id': latest_message.get('conversation_id', str(uuid.uuid4())),
                'metadata': {
                    'entities': self.medical_term_processor.extract_medical_entities(latest_message.get('content', '')),
                    'query_type': self.question_analyzer.categorize_query(latest_message.get('content', ''))
                }
            }
        
        except Exception as e:
            self.logger.error(f"Conversation handling error: {e}")
            return {
                'response_type': 'error',
                'response': "I'm experiencing technical difficulties. Please try again.",
                'conversation_id': None
            }
    
    def process_input(self, message: str) -> Dict[str, Any]:
        """
        Process an input message and return a response in the format expected by the GUI.
        This method is called by the GUI.
        
        Args:
            message: User's input message
            
        Returns:
            Response dictionary with fields expected by the GUI
        """
        try:
            # Add message to conversation history
            self._conversation_history.append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.now().isoformat()
            })
            
            # Generate response using existing methods
            response_text = self.generate_response(message)
            
            # Determine if this is a follow-up question
            is_follow_up = '?' in response_text and any(
                indicator in response_text.lower() 
                for indicator in ['what', 'how', 'when', 'where', 'why', 'which']
            )
            
            response_type = 'follow_up_question' if is_follow_up else 'final_response'
            
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
                'conversation_complete': not is_follow_up,
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            
            return {
                'response': f"Error processing your request: {str(e)}\n\nPlease try asking your question in a different way.",
                'response_type': 'error',
                'conversation_id': self._conversation_id,
                'conversation_complete': True,
                'timestamp': datetime.now().isoformat()
            }

def main():
    """
    Demonstrate the enhanced medical chatbot functionality.
    """
    chatbot = EnhancedMedicalChatbot()
    
    # Example interactions
    test_queries = [
        "What are the symptoms of diabetes?",
        "How can I prevent heart disease?",
        "I've been feeling tired lately. What could be causing this?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        response = chatbot.generate_comprehensive_response(query)
        print("Response:", response)

if __name__ == "__main__":
    main()