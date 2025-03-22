import re
import json
import logging
from pathlib import Path
import spacy
from typing import Dict, List, Optional

class MedicalTermChecker:
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the Medical Term Checker.
        
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
        
        # Load medical resources
        self.medical_ontology = self.load_medical_ontology()
        
        # Load SpaCy model
        try:
            self.nlp = spacy.load("en_core_sci_md")
            self.logger.info("Loaded medical SpaCy model")
        except Exception as e:
            self.logger.warning(f"Could not load medical SpaCy model: {e}")
            self.nlp = spacy.load("en_core_web_sm")
            self.logger.info("Loaded standard SpaCy model as fallback")
    
    def load_medical_ontology(self) -> Dict:
        """
        Load medical ontology from JSON file.
        
        Returns:
            Dictionary of medical terms and their metadata
        """
        try:
            ontology_path = self.project_root / "data" / "resources" / "medical_terms.json"
            
            if not ontology_path.exists():
                self.logger.warning("Medical ontology file not found. Creating empty ontology.")
                return {}
            
            with open(ontology_path, 'r') as f:
                medical_ontology = json.load(f)
            
            self.logger.info(f"Loaded medical ontology with {len(medical_ontology)} terms")
            return medical_ontology
        
        except Exception as e:
            self.logger.error(f"Error loading medical ontology: {e}")
            return {}
    
    def identify_medical_entities(self, text: str) -> List[str]:
        """
        Use NER to extract medical entities from text.
        
        Args:
            text: Input text to process
            
        Returns:
            List of identified medical entities
        """
        # Process text with SpaCy
        doc = self.nlp(text)
        
        # Extract medical entities
        medical_entities = []
        for ent in doc.ents:
            if ent.label_ in ['DISEASE', 'SYMPTOM', 'TREATMENT', 'MEDICATION']:
                medical_entities.append(ent.text)
        
        return medical_entities
    
    def extract_medical_entities(self, text: str) -> Dict[str, Dict]:
        """
        Extract and enrich medical entities from text.
        
        Args:
            text: Input text to process
            
        Returns:
            Dictionary of enriched medical entities
        """
        # Identify medical entities
        entities = self.identify_medical_entities(text)
        
        # Enrich entities
        return self.enrich_entities(entities)
    
    def enrich_entities(self, entities: List[str]) -> Dict[str, Dict]:
        """
        Add additional context to medical entities.
        
        Args:
            entities: List of medical entities
            
        Returns:
            Dictionary of enriched medical entities
        """
        enriched_entities = {}
        
        for entity in entities:
            enriched_entities[entity] = {
                'definition': self.get_definition(entity),
                'related_conditions': self.find_related_conditions(entity),
                'category': self.get_entity_category(entity)
            }
        
        return enriched_entities
    
    def get_definition(self, entity: str) -> Optional[str]:
        """
        Get definition for a medical entity.
        
        Args:
            entity: Medical term to look up
            
        Returns:
            Definition of the entity or None
        """
        # First check the medical ontology
        if entity in self.medical_ontology:
            return self.medical_ontology[entity].get('definition')
        
        return None
    
    def find_related_conditions(self, entity: str) -> List[str]:
        """
        Find conditions related to a medical entity.
        
        Args:
            entity: Medical term to find related conditions for
            
        Returns:
            List of related conditions
        """
        # Check medical ontology for related conditions
        if entity in self.medical_ontology:
            return self.medical_ontology[entity].get('related_conditions', [])
        
        return []
    
    def get_entity_category(self, entity: str) -> str:
        """
        Determine the category of a medical entity.
        
        Args:
            entity: Medical term to categorize
            
        Returns:
            Category of the entity
        """
        # Process with SpaCy to get entity type
        doc = self.nlp(entity)
        
        for ent in doc.ents:
            return ent.label_
        
        # Fallback: check medical ontology
        if entity in self.medical_ontology:
            return self.medical_ontology[entity].get('category', 'UNKNOWN')
        
        return 'UNKNOWN'
    
    def get_medical_terms(self) -> List[str]:
        """
        Get list of all medical terms in the ontology.
        
        Returns:
            List of medical terms
        """
        return list(self.medical_ontology.keys())
    
    def update_ontology(self, new_terms: Dict):
        """
        Update the medical ontology with new terms.
        
        Args:
            new_terms: Dictionary of new medical terms to add
        """
        try:
            # Merge new terms
            self.medical_ontology.update(new_terms)
            
            # Save updated ontology
            ontology_path = self.project_root / "data" / "resources" / "medical_terms.json"
            with open(ontology_path, 'w') as f:
                json.dump(self.medical_ontology, f, indent=2)
            
            self.logger.info(f"Added {len(new_terms)} new terms to medical ontology")
        
        except Exception as e:
            self.logger.error(f"Error updating medical ontology: {e}")

def main():
    """
    Demonstrate usage of MedicalTermChecker.
    """
    # Initialize the term checker
    term_checker = MedicalTermChecker()
    
    # Example medical text
    text = "Patient diagnosed with type 2 diabetes and hypertension. Prescribed metformin."
    
    # Extract and enrich medical entities
    entities = term_checker.extract_medical_entities(text)
    
    # Print enriched entities
    for entity, info in entities.items():
        print(f"Entity: {entity}")
        print(f"  - Definition: {info['definition']}")
        print(f"  - Related Conditions: {info['related_conditions']}")
        print(f"  - Category: {info['category']}\n")

if __name__ == "__main__":
    main()