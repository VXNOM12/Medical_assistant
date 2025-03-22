# src/response_templates.py
"""
This module provides response enhancement functionality for the medical chatbot.
It improves formatting, structure, and readability of model-generated responses.
"""

from src.fix_templates import MedicalResponseTemplates
import re
from datetime import datetime
from typing import Dict, List, Optional


class ResponseEnhancer:
    """
    Enhances model responses with better structure, formatting, and medical context.
    """
    
    def __init__(self):
        """
        Initialize ResponseEnhancer with medical response templates.
        """
        self.templates = MedicalResponseTemplates()

    def structure_response(self, base_response: str, query_type: str, condition: Optional[str] = None) -> str:
        """
        Enhance and structure the response with medical best practices.
        
        Args:
            base_response: Initial generated response
            query_type: Type of medical query
            condition: Optional specific medical condition
            
        Returns:
            Structured and formatted medical response
        """
        # Clean the response first
        cleaned_response = self._clean_response(base_response)
        
        # Get appropriate template and section headers
        if condition is None:
            condition = "this condition"
        
        # Select appropriate template
        template = self.templates.get_template(query_type, condition)
        section_headers = self.templates.get_section_headers(query_type)
        
        # Structure base response into sections
        structured_response = self._create_sectioned_response(
            cleaned_response, 
            list(section_headers.values()),
            section_headers
        )
        
        # Apply formatting enhancements
        formatted_response = self.templates.format_bullets(structured_response)
        
        # Add timestamp and disclaimer
        timestamp = datetime.now().strftime("%Y-%m-%d")
        formatted_response = f"{formatted_response}\n\nLast Updated: {timestamp}"
        
        # Add disclaimer
        final_response = formatted_response + self.templates.disclaimer
        
        return final_response

    def _clean_response(self, response: str) -> str:
        """
        Clean a response by removing redundancies and irrelevant content.
        
        Args:
            response: Raw response text
            
        Returns:
            Cleaned response text
        """
        if not response:
            return ""
            
        # Remove any XML or HTML-like tags
        cleaned = re.sub(r'</?[^>]+>', '', response)
        
        # Remove repeated sentences
        sentences = cleaned.split('. ')
        unique_sentences = []
        seen = set()
        
        for sentence in sentences:
            normalized = sentence.lower().strip()
            if normalized and normalized not in seen:
                unique_sentences.append(sentence)
                seen.add(normalized)
        
        cleaned = '. '.join(unique_sentences)
        
        # Ensure proper spacing
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned

    def _create_sectioned_response(
        self, 
        text: str, 
        section_names: List[str], 
        headers: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create a sectioned response from the base text.
        
        Args:
            text: Input response text
            section_names: List of section names to create
            headers: Optional dictionary of headers with emojis
            
        Returns:
            Sectioned response text
        """
        # Split text into sentences
        sentences = [s.strip() for s in re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text) if s.strip()]
        
        # Initialize sections
        sections = {name: [] for name in section_names}
        current_section = section_names[0]  # Default to first section
        
        # Categorize sentences into sections
        for sentence in sentences:
            # Determine appropriate section based on content
            section_match = self._determine_section(sentence, current_section, sections)
            if section_match:
                current_section = section_match
            
            # Add sentence to current section
            sections[current_section].append(sentence)
        
        # Construct formatted response
        formatted_sections = []
        for section_name, section_sentences in sections.items():
            if section_sentences:
                # Use custom header if provided, otherwise use section name
                header = headers.get(section_name, section_name) if headers else section_name
                section_text = f"{header}:\n" + " ".join(section_sentences)
                formatted_sections.append(section_text)
        
        return "\n\n".join(formatted_sections)

    def _determine_section(
        self, 
        sentence: str, 
        current_section: str, 
        sections: Dict[str, List[str]]
    ) -> Optional[str]:
        """
        Determine the most appropriate section for a sentence.
        
        Args:
            sentence: Input sentence
            current_section: Current active section
            sections: Available sections
            
        Returns:
            Most appropriate section name or None
        """
        # Lowercase for easier matching
        sentence_lower = sentence.lower()
        
        # Define section matching rules
        section_rules = {
            '📝 Overview': ['define', 'overview', 'introduction', 'what is', 'condition'],
            '🔔 Key Symptoms': ['symptom', 'sign', 'feeling', 'experiencing', 'pain'],
            '🔍 Diagnostic Criteria': ['diagnose', 'test', 'identify', 'criteria', 'exam'],
            '💊 Treatment Options': ['treat', 'medication', 'therapy', 'cure', 'manage'],
            '⚠️ Potential Complications': ['risk', 'serious', 'complication', 'consequence', 'danger'],
            '🎯 Expected Outcomes': ['outcome', 'result', 'expect', 'prognosis', 'recovery'],
            '🏥 When to Seek Medical Help': ['doctor', 'emergency', 'hospital', 'seek', 'urgent']
        }
        
        # Check for section match
        for section, keywords in section_rules.items():
            if any(keyword in sentence_lower for keyword in keywords):
                if section in sections:
                    return section
        
        return current_section