from transformers import (
    AutoTokenizer, 
    AutoModelForSeq2SeqLM,  # This is the correct class name
    AutoModelForCausalLM,
    pipeline
)
import torch
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
import numpy as np
from datetime import datetime
import json
import yaml
import gc

class MedicalModel:
    """
    Core medical language model implementation.
    Handles model loading, inference, and response generation.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the medical model.
        
        Args:
            model_path: Optional path to a fine-tuned model
        """
        # Setup logging
        self._setup_logging()
        
        # Set project root and paths
        self.project_root = Path(__file__).parent.parent.parent
        
        # Load configurations
        self.config = self._load_config()
        
        # Setup device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger.info(f"Using device: {self.device}")
        
        # Initialize model components
        self._initialize_model(model_path)
        
        # Load medical knowledge
        self._load_medical_knowledge()

    def _setup_logging(self):
        """Configure logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _load_config(self) -> Dict:
        """Load model configuration."""
        try:
            config_path = self.project_root / "config" / "inference_config.yaml"
            with open(config_path) as f:
                config = yaml.safe_load(f)
                
            self.logger.info("Successfully loaded model configuration")
            return config
            
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            raise

    def _initialize_model(self, model_path: Optional[str]):
        """
        Initialize model and tokenizer.
        
        Args:
            model_path: Optional path to fine-tuned model
        """
        try:
            # Use provided model path or default from config
            model_name = model_path or self.config['model_params']['primary_model']
            self.logger.info(f"Initializing model: {model_name}")
            
            # Determine model type
            is_causal = any(name in model_name.lower() for name in ['gpt', 'llama', 'bloom'])
            
            # Initialize tokenizer with appropriate settings
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                model_max_length=self.config.get('max_length', 512),
                padding_side='left' if is_causal else 'right',
                truncation_side='left' if is_causal else 'right'
            )
            
            # Set padding token if needed
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Initialize model based on type
            if is_causal:
                model_class = AutoModelForCausalLM
                task = "text-generation"
            else:
                model_class = AutoModelForSeq2SeqLM
                task = "text2text-generation"
                
            # Load model with optimizations
            self.model = model_class.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map='auto' if torch.cuda.is_available() else None,
                low_cpu_mem_usage=True
            )
            
            # Create pipeline
            self.pipeline = pipeline(
                task,
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1,
                max_length=self.config.get('max_length', 512),
                temperature=self.config.get('temperature', 0.7),
                top_p=self.config.get('top_p', 0.95),
                repetition_penalty=self.config.get('repetition_penalty', 1.2),
                num_return_sequences=1
            )
            
            self.logger.info("Successfully initialized model and tokenizer")
            
        except Exception as e:
            self.logger.error(f"Error initializing model: {str(e)}")
            raise

    def _load_medical_knowledge(self):
        """Load medical knowledge bases."""
        try:
            resources_path = self.project_root / "data" / "resources"
            
            # Load medical terms
            with open(resources_path / "medical_terms.json") as f:
                self.medical_terms = json.load(f)
                
            # Load clinical guidelines
            with open(resources_path / "clinical_guidelines.json") as f:
                self.clinical_guidelines = json.load(f)
                
            self.logger.info("Successfully loaded medical knowledge")
            
        except Exception as e:
            self.logger.warning(f"Error loading medical knowledge: {str(e)}")
            self.medical_terms = {}
            self.clinical_guidelines = {}

    def generate_response(
        self, 
        query: str,
        context: Optional[Dict] = None,
        max_length: Optional[int] = None
    ) -> str:
        """
        Generate a medical response.
        
        Args:
            query: Input query string
            context: Optional context dictionary
            max_length: Optional maximum response length
            
        Returns:
            Generated response string
        """
        try:
            # Prepare input with context
            input_text = self._prepare_input(query, context)
            
            # Set generation parameters
            gen_kwargs = {
                'max_length': max_length or self.config.get('max_length', 512),
                'num_return_sequences': 1,
                'temperature': self.config.get('temperature', 0.7),
                'top_p': self.config.get('top_p', 0.95),
                'repetition_penalty': self.config.get('repetition_penalty', 1.2),
                'do_sample': True
            }
            
            # Generate response
            response = self.pipeline(
                input_text,
                **gen_kwargs
            )
            
            # Extract and clean response text
            response_text = self._extract_response_text(response)
            
            # Format response
            formatted_response = self._format_response(response_text)
            
            return formatted_response
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I'm having trouble generating a response. Please try again."

    def _prepare_input(self, query: str, context: Optional[Dict] = None) -> str:
        """
        Prepare model input with context.
        
        Args:
            query: Input query
            context: Optional context dictionary
            
        Returns:
            Prepared input string
        """
        # Start with the query
        input_text = query.strip()
        
        # Add context if provided
        if context:
            context_str = ""
            
            # Add medical terms
            if 'terms' in context:
                terms_str = ", ".join(f"{term}: {info.get('definition', '')}" 
                                    for term, info in context['terms'].items())
                if terms_str:
                    context_str += f"\nRelevant medical terms:\n{terms_str}"
            
            # Add guidelines
            if 'guidelines' in context and context['guidelines']:
                guidelines_str = "\n".join(f"- {g['text']}" 
                                         for g in context['guidelines'])
                context_str += f"\nClinical guidelines:\n{guidelines_str}"
            
            # Add warnings
            if 'warnings' in context and context['warnings']:
                warnings_str = "\n".join(f"- {w}" for w in context['warnings'])
                context_str += f"\nImportant considerations:\n{warnings_str}"
                
            # Add context to input
            if context_str:
                input_text = f"{context_str}\n\nQuery: {input_text}"
        
        return input_text

    def _extract_response_text(self, response) -> str:
        """
        Extract text from model response.
        
        Args:
            response: Model response object
            
        Returns:
            Extracted text string
        """
        if isinstance(response, list):
            if response and isinstance(response[0], dict):
                return response[0].get('generated_text', '')
            return response[0] if response else ''
        elif isinstance(response, dict):
            return response.get('generated_text', '')
        elif isinstance(response, str):
            return response
        else:
            self.logger.warning(f"Unexpected response type: {type(response)}")
            return str(response)

    def _format_response(self, text: str) -> str:
        """
        Format response text.
        
        Args:
            text: Response text to format
            
        Returns:
            Formatted response string
        """
        # Clean the text
        text = text.strip()
        
        # Add line breaks between sections
        text = text.replace(". ", ".\n")
        
        # Add medical disclaimer
        disclaimer = ("\n\nPlease note: This information is for educational purposes only. "
                     "Consult a healthcare professional for medical advice.")
        
        return f"{text}{disclaimer}"

    def batch_generate(
        self,
        queries: List[str],
        batch_size: int = 8
    ) -> List[str]:
        """
        Generate responses for multiple queries.
        
        Args:
            queries: List of input queries
            batch_size: Batch size for generation
            
        Returns:
            List of generated responses
        """
        responses = []
        
        for i in range(0, len(queries), batch_size):
            batch = queries[i:i + batch_size]
            
            try:
                # Generate responses for batch
                batch_responses = self.pipeline(
                    batch,
                    max_length=self.config.get('max_length', 512),
                    num_return_sequences=1,
                    batch_size=batch_size
                )
                
                # Extract and clean responses
                batch_texts = [
                    self._extract_response_text(resp)
                    for resp in batch_responses
                ]
                
                # Format responses
                batch_texts = [
                    self._format_response(text)
                    for text in batch_texts
                ]
                
                responses.extend(batch_texts)
                
            except Exception as e:
                self.logger.error(f"Error in batch generation: {str(e)}")
                # Add error responses for failed batch
                responses.extend(["Error generating response."] * len(batch))
                
        return responses

    def get_model_info(self) -> Dict[str, any]:
        """
        Get model information and configuration.
        
        Returns:
            Dictionary containing model information
        """
        return {
            'model_name': self.config['model_params']['primary_model'],
            'device': str(self.device),
            'max_length': self.config.get('max_length', 512),
            'temperature': self.config.get('temperature', 0.7),
            'top_p': self.config.get('top_p', 0.95),
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def cleanup(self):
        """Clean up model resources."""
        try:
            del self.pipeline
            del self.model
            del self.tokenizer
            torch.cuda.empty_cache()
            gc.collect()
            self.logger.info("Successfully cleaned up model resources")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

def main():
    """Main function for testing."""
    try:
        # Initialize model
        model = MedicalModel()
        
        # Test queries
        queries = [
            "What are the common symptoms of diabetes?",
            "How can I maintain a healthy blood pressure?"
        ]
        
        # Generate responses
        for query in queries:
            response = model.generate_response(query)
            print(f"\nQuery: {query}")
            print(f"Response: {response}")
            
        # Clean up
        model.cleanup()
        
    except Exception as e:
        logging.error(f"Error in main: {str(e)}")
        raise

if __name__ == "__main__":
    main()