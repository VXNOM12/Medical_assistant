# src/followup_templates.py

from typing import Dict, List, Optional, Tuple
import random
import re

class FollowupQuestionTemplates:
    """
    Provides templates for follow-up questions based on medical context.
    
    This class generates appropriate follow-up questions based on the type
    of medical query, missing information categories, and conversation context.
    """
    
    @staticmethod
    def get_templates_by_category(category: str) -> List[str]:
        """
        Get follow-up question templates for a specific category.
        
        Args:
            category: The category of information needed
            
        Returns:
            List of question templates
        """
        templates = {
            # Duration-related follow-up questions
            'duration': [
                "How long have you been experiencing {symptom}?",
                "When did you first notice {symptom}?",
                "Has {symptom} been present continuously or does it come and go?",
                "How long has this been going on?",
                "Did {symptom} start suddenly or gradually develop over time?"
            ],
            
            # Severity-related follow-up questions
            'severity': [
                "On a scale of 1-10, how would you rate the severity of {symptom}?",
                "How severe is {symptom} - mild, moderate, or severe?",
                "How much does {symptom} affect your daily activities?",
                "Does {symptom} interfere with your sleep or work?",
                "Has {symptom} gotten better, worse, or stayed the same over time?"
            ],
            
            # Frequency-related follow-up questions
            'frequency': [
                "How often do you experience {symptom}?",
                "Does {symptom} occur at specific times of day or in certain situations?",
                "Is {symptom} constant or does it come and go?",
                "How many times per day/week do you typically experience {symptom}?",
                "Has the frequency of {symptom} changed over time?"
            ],
            
            # Location-related follow-up questions
            'location': [
                "Where exactly do you experience {symptom}?",
                "Does {symptom} affect one specific area or multiple areas?",
                "Does {symptom} spread or radiate to other parts of your body?",
                "Can you point to exactly where you feel {symptom}?",
                "Does the location of {symptom} change over time?"
            ],
            
            # Trigger-related follow-up questions
            'triggers': [
                "Have you noticed anything that triggers or worsens {symptom}?",
                "Does {symptom} occur after certain activities or foods?",
                "Are there any patterns you've noticed with when {symptom} occurs?",
                "What makes {symptom} better or worse?",
                "Are there environmental factors that seem to affect {symptom}?"
            ],
            
            # Associated symptoms follow-up questions
            'associated_symptoms': [
                "Are there any other symptoms that accompany {symptom}?",
                "Do you notice any other changes in your body when {symptom} occurs?",
                "Have you experienced any fever, fatigue, or other general symptoms alongside {symptom}?",
                "Are there any other symptoms that occur before, during, or after {symptom}?",
                "Have you noticed any unusual changes in your appetite, sleep, or energy level?"
            ],
            
            # Medical history follow-up questions
            'medical_history': [
                "Do you have any underlying medical conditions?",
                "Are you currently taking any medications?",
                "Have you had {condition} or similar issues in the past?",
                "Is there a family history of {condition} or related conditions?",
                "Have you recently had any medical procedures or treatments?"
            ],
            
            # Treatment follow-up questions
            'treatment': [
                "What treatments have you already tried for {condition}?",
                "Have any treatments helped with {symptom} so far?",
                "Are you currently taking any medications for {condition}?",
                "What has your healthcare provider recommended for {condition}?",
                "What specific aspects of treatment are you interested in learning about?"
            ],
            
            # Prevention follow-up questions
            'prevention': [
                "What preventive measures have you already implemented?",
                "Do you have specific risk factors for {condition} you're concerned about?",
                "Are you looking for information on lifestyle changes, medications, or other preventive approaches?",
                "Is there a family history of {condition} that concerns you?",
                "Are you interested in primary prevention or preventing complications of existing {condition}?"
            ],
            
            # General clarification questions
            'clarification': [
                "Could you provide more details about your question regarding {topic}?",
                "What specific aspects of {topic} are you most interested in learning about?",
                "Are you asking about {topic} for yourself or someone else?",
                "What's your main concern regarding {topic}?",
                "What information would be most helpful to you about {topic}?"
            ]
        }
        
        return templates.get(category, templates['clarification'])
    
    @staticmethod
    def generate_question(category: str, context: Dict) -> str:
        """
        Generate a specific follow-up question based on category and context.
        
        Args:
            category: The category of information needed
            context: Dictionary with context like symptoms, conditions, etc.
            
        Returns:
            Formatted question text
        """
        templates = FollowupQuestionTemplates.get_templates_by_category(category)
        
        # Select a template (could be random or based on context)
        template = random.choice(templates)
        
        # Fill in the template placeholders based on context
        symptom = context.get('symptom', 'symptoms')
        condition = context.get('condition', 'condition')
        topic = context.get('topic', symptom if 'symptom' in context else condition)
        
        filled_template = template
        if '{symptom}' in template:
            filled_template = template.replace('{symptom}', symptom)
        if '{condition}' in filled_template:
            filled_template = filled_template.replace('{condition}', condition)
        if '{topic}' in filled_template:
            filled_template = filled_template.replace('{topic}', topic)
            
        return filled_template
    
    @staticmethod
    def get_question_by_query_type(query_type: str, context: Dict) -> str:
        """
        Get a follow-up question based on the type of medical query.
        
        Args:
            query_type: Type of the medical query (symptoms, treatment, etc.)
            context: Dictionary with context information
            
        Returns:
            Formatted question text
        """
        query_templates = {
            'symptoms': [
                "How long have you been experiencing these symptoms?",
                "On a scale of 1-10, how would you rate the severity?",
                "Have you noticed any patterns or triggers for these symptoms?"
            ],
            
            'treatment': [
                "Have you tried any treatments for {condition} already?",
                "Are you looking for information on medications, lifestyle changes, or other approaches?",
                "Do you have any specific concerns about treatment options?"
            ],
            
            'prevention': [
                "Do you have specific risk factors for {condition} you're concerned about?",
                "Are you interested in preventive measures for yourself or someone else?",
                "What preventive approaches have you already considered?"
            ],
            
            'cause': [
                "When did you first notice {condition}?",
                "Have you identified any patterns or triggers associated with {condition}?",
                "Are you experiencing any other symptoms alongside {condition}?"
            ],
            
            'diagnosis': [
                "What symptoms are you experiencing that led to this question?",
                "How long have these symptoms been present?",
                "Have you consulted with a healthcare provider about these concerns?"
            ]
        }
        
        # Get templates for the query type or use general templates
        templates = query_templates.get(query_type, [
            "Could you provide more specific details about your question?",
            "What particular aspect of this health topic are you most interested in?",
            "Is there specific information you're hoping to learn?"
        ])
        
        # Select and fill template
        template = random.choice(templates)
        condition = context.get('condition', 'this condition')
        
        filled_template = template
        if '{condition}' in template:
            filled_template = template.replace('{condition}', condition)
            
        return filled_template
    
    @staticmethod
    def format_question(question: str) -> str:
        """
        Format the question text for better readability.
        
        Args:
            question: Raw question text
            
        Returns:
            Formatted question text
        """
        # Ensure the question ends with a question mark
        if not question.endswith('?'):
            question += '?'
            
        # Capitalize the first letter
        question = question[0].upper() + question[1:]
        
        # Add a friendly prefix occasionally
        prefixes = [
            "To help provide better information, ",
            "If you don't mind sharing, ",
            "To better address your question, ",
            "For more specific information, ",
            "To tailor my response, "
        ]
        
        # Only add a prefix 40% of the time to maintain variety
        if random.random() < 0.4:
            prefix = random.choice(prefixes)
            question = prefix + question[0].lower() + question[1:]
        
        return question
    
    @staticmethod
    def generate_question_for_missing_info(missing_info: Dict[str, float], context: Dict) -> str:
        """
        Generate the most appropriate follow-up question based on missing information.
        
        Args:
            missing_info: Dictionary of missing information categories with importance scores
            context: Dictionary with context information
            
        Returns:
            Formatted question text or None if no questions needed
        """
        if not missing_info:
            return None
            
        # Sort missing information by importance
        sorted_missing = sorted(
            missing_info.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Get the most important missing information category
        category, _ = sorted_missing[0]
        
        # Generate a question for this category
        question = FollowupQuestionTemplates.generate_question(category, context)
        
        # Format the question
        formatted_question = FollowupQuestionTemplates.format_question(question)
        
        return formatted_question