import re
import json
from pathlib import Path
import logging as logger
import yaml
import nltk
from nltk.stem import WordNetLemmatizer
import spacy

class MedicalDataProcessor:
    def __init__(self, config_path=None):
        """
        Initialize the medical data processor.
        
        Args:
            config_path: Optional path to configuration file
        """
        # Setup logging
        self._setup_logging()
        
        # Set project root and load config
        self.project_root = Path(__file__).parent.parent
        self.config = self._load_config(config_path)
        
        # Initialize NLP tools
        self._initialize_nlp_tools()
        
        # Load medical resources
        self._load_medical_resources()

    def _setup_logging(self):
        """Configure logging settings."""
        logger.basicConfig(
            level=logger.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logger.getLogger(__name__)

    def _load_config(self, config_path=None):
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Dictionary containing configuration parameters
        """
        try:
            if config_path is None:
                config_path = self.project_root / "config" / "data_config.yaml"
                
            with open(config_path) as f:
                config = yaml.safe_load(f)
                
            self.logger.info("Successfully loaded data configuration")
            return config
            
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            return {}

    def _initialize_nlp_tools(self):
        """Initialize NLP tools and models."""
        # Download NLTK resources
        try:
            nltk.download('punkt')
            nltk.download('wordnet')
        except Exception as e:
            self.logger.warning(f"Error downloading NLTK resources: {e}")
        
        # Initialize lemmatizer
        self.lemmatizer = WordNetLemmatizer()
        
        # Load SpaCy model
        try:
            self.nlp = spacy.load("en_core_sci_md")  # Medical-specific SpaCy model
            logger.info("Loaded medical SpaCy model")
        except Exception as e:
            logger.warning(f"Could not load medical SpaCy model: {e}")
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("Loaded standard SpaCy model as fallback")
            except Exception as e:
                logger.error(f"Could not load fallback SpaCy model: {e}")
                # Add this fallback to prevent crashing
                from spacy.blank import blank
                self.nlp = blank("en")
                logger.warning("Using blank SpaCy model - NLP capabilities will be limited")

    def _load_medical_resources(self):
        """Load medical terminology and other domain-specific resources."""
        try:
            resources_path = self.project_root / "data" / "resources"
            
            # Make sure the resources directory exists
            if not resources_path.exists():
                os.makedirs(resources_path, exist_ok=True)
                self.logger.warning(f"Resources directory not found, created it: {resources_path}")
                self.medical_abbreviations = {}
                self.medical_terms = {}
                return
            
            # Load medical abbreviations
            abbreviations_path = resources_path / "medical_abbreviations.json"
            if abbreviations_path.exists():
                with open(abbreviations_path) as f:
                    self.medical_abbreviations = json.load(f)
                self.logger.info("Successfully loaded medical abbreviations")
            else:
                self.logger.warning(f"Medical abbreviations file not found: {abbreviations_path}")
                self.medical_abbreviations = {}
            
            # Load medical terms
            terms_path = resources_path / "medical_terms.json"
            if terms_path.exists():
                with open(terms_path) as f:
                    self.medical_terms = json.load(f)
                self.logger.info("Successfully loaded medical terms")
            else:
                self.logger.warning(f"Medical terms file not found: {terms_path}")
                self.medical_terms = {}
                
        except Exception as e:
            self.logger.warning(f"Error loading medical resources: {str(e)}")
            self.medical_abbreviations = {}
            self.medical_terms = {}

            
    def preprocess_text(self, text):
        """
        Preprocess text with multiple cleaning steps.
        
        Args:
            text: Input text string
            
        Returns:
            Preprocessed text
        """
        try:
            # Remove special characters
            text = self.remove_special_characters(text)
            
            # Expand medical abbreviations
            text = self.expand_medical_abbreviations(text)
            
            # Lemmatize text
            text = self.lemmatize_text(text)
            
            # Lowercase
            text = text.lower()
            
            # Remove extra whitespace
            text = ' '.join(text.split())
            
            return text
        
        except Exception as e:
            self.logger.error(f"Error preprocessing text: {e}")
            return text

    def remove_special_characters(self, text):
        """
        Remove special characters while preserving medical symbols.
        
        Args:
            text: Input text string
            
        Returns:
            Text with special characters removed
        """
        # Remove URLs
        text = re.sub(r'http\S+|www.\S+', '', text)
        
        # Remove special characters but keep medical symbols
        text = re.sub(r'[^a-zA-Z0-9\s\-\+°%/]', ' ', text)
        
        return text

    def expand_medical_abbreviations(self, text):
        """
        Replace medical abbreviations with full terms.
        
        Args:
            text: Input text string
            
        Returns:
            Text with expanded abbreviations
        """
        for abbr, full_term in self.medical_abbreviations.items():
            # Use word boundary to ensure exact match
            text = re.sub(rf'\b{abbr}\b', full_term, text, flags=re.IGNORECASE)
        
        return text

    def lemmatize_text(self, text):
        """
        Lemmatize text while preserving medical terms.
        
        Args:
            text: Input text string
            
        Returns:
            Lemmatized text
        """
        # Tokenize the text
        doc = self.nlp(text)
        
        # Process tokens
        processed_tokens = []
        for token in doc:
            # Keep medical terms as is
            if token.text.lower() in self.medical_terms:
                processed_tokens.append(token.text)
            # Lemmatize other tokens
            elif not token.is_stop:
                processed_tokens.append(self.lemmatizer.lemmatize(token.text))
        
        return ' '.join(processed_tokens)

    def extract_medical_entities(self, text):
        """
        Extract medical entities from text.
        
        Args:
            text: Input text string
            
        Returns:
            Dictionary of extracted medical entities
        """
        doc = self.nlp(text)
        
        entities = {
            'diseases': [],
            'symptoms': [],
            'treatments': [],
            'medications': []
        }
        
        for ent in doc.ents:
            if ent.label_ == 'DISEASE':
                entities['diseases'].append(ent.text)
            elif ent.label_ == 'SYMPTOM':
                entities['symptoms'].append(ent.text)
            elif ent.label_ == 'TREATMENT':
                entities['treatments'].append(ent.text)
            elif ent.label_ == 'MEDICATION':
                entities['medications'].append(ent.text)
        
        return entities

    def augment_text(self, text):
        """
        Perform text augmentation for medical data.
        
        Args:
            text: Input text string
            
        Returns:
            List of augmented text variants
        """
        augmented_texts = [text]
        
        # Get medical entities
        doc = self.nlp(text)
        
        # Synonym replacement
        for token in doc.ents:
            if token.text.lower() in self.medical_terms:
                synonyms = self.medical_terms.get(token.text.lower(), {}).get('synonyms', [])
                
                for synonym in synonyms:
                    augmented_text = text.replace(token.text, synonym)
                    augmented_texts.append(augmented_text)
        
        return augmented_texts

def main():
    """
    Example usage of MedicalDataProcessor.
    """
    processor = MedicalDataProcessor()
    
    # Example medical text
    text = "Patient with HTN experiencing chest pain"
    
    # Preprocess text
    processed_text = processor.preprocess_text(text)
    print("Processed Text:", processed_text)
    
    # Extract medical entities
    entities = processor.extract_medical_entities(text)
    print("Extracted Entities:", entities)
    
    # Augment text
    augmented_texts = processor.augment_text(text)
    print("Augmented Texts:", augmented_texts)

if __name__ == "__main__":
    main()