import pandas as pd
import numpy as np
from pathlib import Path
import logging
import yaml
import json
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime
from collections import defaultdict

class DataHandler:
    """
    Handles data operations for the medical chatbot including loading, processing,
    and managing medical knowledge bases and configuration data.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the data handler with project root path and logging configuration.
        
        Args:
            project_root: Optional path to project root directory
        """
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Set project root
        self.project_root = project_root or Path(__file__).parent.parent
        
        # Initialize data structures
        self.medical_terms = {}
        self.medical_abbreviations = {}
        self.symptom_descriptions = {}
        self.clinical_guidelines = {}
        self.drug_interactions = {}
        
        # Load configurations and resources
        self._load_configs()
        self._load_medical_resources()
        
    def _load_configs(self) -> None:
        """Load all configuration files."""
        try:
            # Load inference config
            inference_config_path = self.project_root / "config" / "inference_config.yaml"
            with open(inference_config_path) as f:
                self.inference_config = yaml.safe_load(f)
                
            # Load safety config
            safety_config_path = self.project_root / "config" / "safety_config.yaml"
            with open(safety_config_path) as f:
                self.safety_config = yaml.safe_load(f)
                
            # Load data config
            data_config_path = self.project_root / "config" / "data_config.yaml"
            with open(data_config_path) as f:
                self.data_config = yaml.safe_load(f)
                
            self.logger.info("Successfully loaded all configuration files")
            
        except Exception as e:
            self.logger.error(f"Error loading configurations: {str(e)}")
            raise
            
    def _load_medical_resources(self) -> None:
        """Load medical knowledge resources."""
        try:
            resources_path = self.project_root / "data" / "resources"
            resources = [
                ("medical_terms.json", "medical_terms"),
                ("medical_abbreviations.json", "medical_abbreviations"),
                ("symptom_descriptions.json", "symptom_descriptions"),
                ("clinical_guidelines.json", "clinical_guidelines"),
                ("drug_interactions.json", "drug_interactions")
            ]
            
            for filename, attr_name in resources:
                file_path = resources_path / filename
                if file_path.exists():
                    with open(file_path) as f:
                        setattr(self, attr_name, json.load(f))
                        self.logger.info(f"Loaded {filename}")
                else:
                    self.logger.warning(f"Resource file not found: {filename}")
                    setattr(self, attr_name, {})
                    
        except Exception as e:
            self.logger.error(f"Error loading medical resources: {str(e)}")
            
    def process_query(self, query: str) -> Tuple[str, Dict[str, any]]:
        """
        Process and enhance a user query with relevant medical context.
        
        Args:
            query: User input query string
            
        Returns:
            Tuple containing processed query and context dictionary
        """
        # Clean and normalize query
        processed_query = self._clean_text(query)
        
        # Extract medical terms
        medical_terms = self._extract_medical_terms(processed_query)
        
        # Get relevant context
        context = self._get_medical_context(processed_query, medical_terms)
        
        return processed_query, context
        
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not isinstance(text, str):
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Expand medical abbreviations
        for abbr, expansion in self.medical_abbreviations.items():
            text = text.replace(f" {abbr} ", f" {expansion} ")
            
        # Remove special characters but keep medical symbols
        text = ''.join(c for c in text if c.isalnum() or c in ' -+°%/')
        
        # Normalize whitespace
        return ' '.join(text.split())
        
    def _extract_medical_terms(self, text: str) -> List[str]:
        """Extract medical terms from text."""
        words = text.split()
        return [word for word in words if word in self.medical_terms]
        
    def _get_medical_context(self, query: str, medical_terms: List[str]) -> Dict[str, any]:
        """Get relevant medical context for the query."""
        context = {
            'terms': {},
            'guidelines': [],
            'warnings': [],
            'interactions': []
        }
        
        # Add medical term definitions
        for term in medical_terms:
            if term in self.medical_terms:
                context['terms'][term] = self.medical_terms[term]
                
        # Check clinical guidelines
        for guideline in self.clinical_guidelines.values():
            if any(term in guideline['text'].lower() for term in medical_terms):
                context['guidelines'].append(guideline)
                
        # Check drug interactions
        for term in medical_terms:
            if term in self.drug_interactions:
                context['interactions'].extend(self.drug_interactions[term])
                
        return context
        
    def get_response_template(self, query_type: str) -> str:
        """Get appropriate response template based on query type."""
        templates = {
            'symptoms': (
                "Common symptoms include:\n"
                "{symptoms_list}\n\n"
                "Important considerations:\n"
                "{considerations}\n\n"
                "When to seek medical attention:\n"
                "{warnings}"
            ),
            'treatment': (
                "General treatment approaches:\n"
                "{treatments}\n\n"
                "Important guidelines:\n"
                "{guidelines}\n\n"
                "Safety considerations:\n"
                "{safety}"
            ),
            'general': (
                "Medical Information:\n"
                "{information}\n\n"
                "Key points:\n"
                "{key_points}\n\n"
                "Additional considerations:\n"
                "{considerations}"
            )
        }
        
        return templates.get(query_type, templates['general'])
        
    def save_interaction(self, query: str, response: str, metadata: Dict[str, any]) -> None:
        """
        Save interaction data for analysis and improvement.
        
        Args:
            query: User query
            response: Generated response
            metadata: Additional interaction metadata
        """
        try:
            # Create interaction record
            interaction = {
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'response': response,
                'metadata': metadata
            }
            
            # Save to interaction log
            log_path = self.project_root / "data" / "interaction_logs.jsonl"
            with open(log_path, 'a') as f:
                json.dump(interaction, f)
                f.write('\n')
                
        except Exception as e:
            self.logger.error(f"Error saving interaction: {str(e)}")
            
    def get_safety_response(self, safety_issue: str) -> str:
        """Get appropriate safety response for identified issues."""
        return self.safety_config.get('responses', {}).get(
            safety_issue,
            self.safety_config.get('default_response', 
                "Please consult a healthcare professional for medical advice.")
        )
        
    def check_query_safety(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Check if query contains any safety concerns.
        
        Args:
            query: User query string
            
        Returns:
            Tuple of (is_safe, warning_message)
        """
        query_lower = query.lower()
        
        # Check emergency patterns
        for pattern in self.safety_config.get('emergency_patterns', []):
            if pattern in query_lower:
                return False, self.get_safety_response('emergency')
                
        # Check restricted topics
        for topic in self.safety_config.get('restricted_topics', []):
            if topic in query_lower:
                return False, self.get_safety_response('restricted')
                
        return True, None
        
    def update_medical_knowledge(self, new_data: Dict[str, any], data_type: str) -> None:
        """
        Update medical knowledge base with new data.
        
        Args:
            new_data: Dictionary containing new medical data
            data_type: Type of medical data being updated
        """
        try:
            if data_type == 'terms':
                self.medical_terms.update(new_data)
            elif data_type == 'abbreviations':
                self.medical_abbreviations.update(new_data)
            elif data_type == 'guidelines':
                self.clinical_guidelines.update(new_data)
            elif data_type == 'interactions':
                self.drug_interactions.update(new_data)
            else:
                raise ValueError(f"Unknown data type: {data_type}")
                
            # Save updated data
            self._save_medical_resources()
            
        except Exception as e:
            self.logger.error(f"Error updating medical knowledge: {str(e)}")
            
    def _save_medical_resources(self) -> None:
        """Save medical resources to disk."""
        try:
            resources_path = self.project_root / "data" / "resources"
            resources_path.mkdir(parents=True, exist_ok=True)
            
            # Save each resource type
            resources = {
                'medical_terms.json': self.medical_terms,
                'medical_abbreviations.json': self.medical_abbreviations,
                'symptom_descriptions.json': self.symptom_descriptions,
                'clinical_guidelines.json': self.clinical_guidelines,
                'drug_interactions.json': self.drug_interactions
            }
            
            for filename, data in resources.items():
                with open(resources_path / filename, 'w') as f:
                    json.dump(data, f, indent=2)
                    
            self.logger.info("Successfully saved medical resources")
            
        except Exception as e:
            self.logger.error(f"Error saving medical resources: {str(e)}")