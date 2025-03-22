# src/fix_templates.py
"""
This module provides medical response templates for the chatbot.
It's imported by ResponseEnhancer and other modules to structure medical responses.
"""

import logging

# Set up logging
logger = logging.getLogger(__name__)

class MedicalResponseTemplates:
    """
    Provides structured templates for different types of medical responses.
    Used by ResponseEnhancer to format and structure responses.
    Compatible with the new ResponseFormatter class.
    """
    
    def __init__(self):
        """Initialize the medical response templates."""
        # General response templates
        self.general_templates = {
            "prefix": "Medical Information:",
            "body": "{content}",
            "suffix": "Key Points to Remember:"
        }
        
        # Templates for specific medical query types
        self.specialized_templates = {
            "symptoms": {
                "prefix": "📋 Symptoms and Signs",
                "body": "{content}",
                "suffix": "When to Seek Medical Attention"
            },
            "treatment": {
                "prefix": "💊 Treatment Options",
                "body": "{content}",
                "suffix": "Important Considerations"
            },
            "diagnostic": {
                "prefix": "🔍 Diagnostic Information",
                "body": "{content}",
                "suffix": "Follow-up Recommendations"
            },
            "prevention": {
                "prefix": "🛡️ Preventive Measures",
                "body": "{content}",
                "suffix": "Additional Recommendations"
            },
            "medication": {
                "prefix": "💊 Medication Information",
                "body": "{content}",
                "suffix": "Potential Side Effects"
            }
        }
        
        # Section headers with emojis
        self.section_headers = {
            "Overview": "📝 Overview",
            "Key Symptoms": "🔔 Key Symptoms",
            "Diagnostic Criteria": "🔍 Diagnostic Criteria",
            "Treatment Options": "💊 Treatment Options",
            "Potential Complications": "⚠️ Potential Complications",
            "Expected Outcomes": "🎯 Expected Outcomes",
            "Prevention": "🛡️ Prevention",
            "When to Seek Help": "🏥 When to Seek Medical Help"
        }
        
        # Emergency response templates
        self.emergency_templates = {
            "immediate": (
                "🚨 EMERGENCY: This appears to be a medical emergency. "
                "Please call emergency services (911 in the US) immediately "
                "or go to the nearest emergency room."
            ),
            "urgent": (
                "⚠️ URGENT: These symptoms require prompt medical attention. "
                "Please seek immediate care at an urgent care facility or emergency room."
            ),
            "concerning": (
                "❗ ATTENTION: These symptoms require medical evaluation. "
                "Please schedule an appointment with your healthcare provider soon."
            )
        }
        
        # Disclaimer templates
        self.disclaimer = (
            "\n\nDisclaimer: This information is for educational purposes only. "
            "Please consult a healthcare professional for personalized medical advice."
        )
    
    def get_template(self, query_type, condition=None):
        """
        Get the appropriate template for a query type.
        
        Args:
            query_type: Type of medical query
            condition: Optional medical condition name
            
        Returns:
            Template dictionary
        """
        template = self.specialized_templates.get(query_type, self.general_templates)
        
        # Customize template with condition if provided
        if condition and template:
            # Create a copy to avoid modifying the original
            template_copy = template.copy()
            if 'prefix' in template_copy:
                template_copy['prefix'] = f"{template_copy['prefix']} for {condition.title()}"
            return template_copy
            
        return template
    
    def get_section_headers(self, query_type):
        """
        Get appropriate section headers based on query type.
        
        Args:
            query_type: Type of medical query
            
        Returns:
            Dictionary of section headers
        """
        # Default headers that apply to most queries
        default_headers = {
            "Overview": self.section_headers["Overview"],
            "Key Symptoms": self.section_headers["Key Symptoms"],
            "Treatment Options": self.section_headers["Treatment Options"]
        }
        
        # Add specialized headers based on query type
        if query_type == "diagnostic":
            default_headers["Diagnostic Criteria"] = self.section_headers["Diagnostic Criteria"]
            default_headers["Expected Outcomes"] = self.section_headers["Expected Outcomes"]
            
        elif query_type == "treatment":
            default_headers["Potential Complications"] = self.section_headers["Potential Complications"]
            
        elif query_type == "prevention":
            default_headers["Prevention"] = self.section_headers["Prevention"]
            
        # Always include when to seek help
        default_headers["When to Seek Help"] = self.section_headers["When to Seek Help"]
        
        return default_headers
    
    def format_bullets(self, text):
        """
        Format text with bullet points for readability.
        
        Args:
            text: Input text
            
        Returns:
            Formatted text with bullet points
        """
        lines = text.split('\n')
        formatted_lines = []
        
        in_bullet_section = False
        for i, line in enumerate(lines):
            # Check if this is a section header
            if ':' in line and len(line.split(':')[0].split()) <= 5:
                # This is a section header - reset bullet section flag
                in_bullet_section = True
                formatted_lines.append(line)
            elif in_bullet_section and line.strip() and not line.startswith('•') and i > 0:
                # This is content in a bullet section
                # Check if it's a short sentence that should be bulleted
                if len(line) < 100 and not line.endswith(':'):
                    formatted_lines.append(f"• {line}")
                else:
                    # Long paragraph - keep as is
                    formatted_lines.append(line)
            else:
                # Keep as is
                formatted_lines.append(line)
                
        return '\n'.join(formatted_lines)
        
    def format_response(self, content, query_type="general"):
        """
        Format a response using the appropriate template.
        
        Args:
            content: Response content
            query_type: Type of medical query
            
        Returns:
            Formatted response string
        """
        template = self.get_template(query_type)
        
        formatted_response = (
            f"{template['prefix']}:\n\n"
            f"{template['body'].format(content=content)}\n\n"
            f"{template['suffix']}:"
        )
        
        return formatted_response + self.disclaimer
    
    def get_emergency_response(self, severity="urgent"):
        """
        Get an emergency response based on severity.
        
        Args:
            severity: Emergency severity level
            
        Returns:
            Emergency response string
        """
        response = self.emergency_templates.get(severity, self.emergency_templates["urgent"])
        return response + self.disclaimer
        
    def structure_response(self, raw_text, query="", query_type="general"):
        """
        Bridge method to make MedicalResponseTemplates compatible with ResponseFormatter.
        
        Args:
            raw_text: Raw response text
            query: Original query
            query_type: Type of query
            
        Returns:
            Formatted response
        """
        logger.info("Using MedicalResponseTemplates as a fallback for ResponseFormatter")
        
        if query_type not in self.specialized_templates:
            query_type = "general"
            
        template = self.get_template(query_type)
        
        # Add bullet formatting
        content = self.format_bullets(raw_text)
        
        # Format with template
        formatted = (
            f"{template['prefix']}:\n\n"
            f"{content}\n\n"
            f"{template['suffix']}:"
        )
        
        # Add disclaimer
        return formatted + self.disclaimer