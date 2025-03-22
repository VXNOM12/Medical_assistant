# src/conversation_manager.py

from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import logging
import re
import random  # Added import for random.choice
import uuid    # Added for better conversation IDs

class ConversationManager:
    """
    Manages the state and flow of medical conversations, including follow-up questions.
    
    This class tracks conversation history, analyzes queries for ambiguity,
    generates appropriate follow-up questions, and determines when the conversation
    is ready for a final response.
    """
    
    def __init__(self, logger=None):
        """Initialize the conversation manager with empty state."""
        # Configure logging
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize conversation state
        self.reset_conversation()
        
        # Initialize tracking for answered questions
        self.answered_questions = set()
        
        # Define follow-up question templates for different medical contexts
        self._initialize_question_templates()
        
        # Define ambiguity detection patterns
        self._initialize_ambiguity_patterns()
        
        # Key medical information categories that may need clarification
        self.information_categories = {
            'duration': {
                'keywords': ['how long', 'duration', 'time', 'days', 'weeks', 'months', 'years'],
                'importance': 0.9,
                'questions': [
                    "How long have you been experiencing symptoms of {condition}?",
                    "When did these symptoms first appear?",
                    "Do your symptoms occur year-round or only during certain seasons?"
                ]
            },
            'severity': {
                'keywords': ['severe', 'mild', 'moderate', 'intensity', 'bad', 'serious', 'pain level'],
                'importance': 0.8,
                'questions': [
                    "How would you describe the severity of your {condition} symptoms?",
                    "On a scale of 1-10, how would you rate the intensity of your symptoms?",
                    "Are your symptoms mild, moderate, or severe?",
                    "How much do these symptoms affect your daily activities?"
                ]
            },
            'frequency': {
                'keywords': ['often', 'frequency', 'how many times', 'daily', 'weekly', 'occasionally', 'regularly'],
                'importance': 0.7,
                'questions': [
                    "How often do you experience symptoms of {condition}?",
                    "Do your symptoms occur regularly or intermittently?",
                    "Are there specific times when your symptoms get worse?"
                ]
            },
            'location': {
                'keywords': ['where', 'location', 'area', 'spot', 'part of body', 'left', 'right', 'upper', 'lower'],
                'importance': 0.8,
                'questions': [
                    "Where do you typically experience these symptoms?",
                    "Do the symptoms affect specific areas of your body?",
                    "Is there a particular location where symptoms are most noticeable?"
                ]
            },
            'associated_symptoms': {
                'keywords': ['other symptoms', 'also have', 'alongside', 'accompanied by', 'together with'],
                'importance': 0.7,
                'questions': [
                    "Are there any other symptoms that accompany your {condition}?",
                    "Have you noticed any other changes when experiencing these symptoms?",
                    "Do you have any additional symptoms alongside {condition}?"
                ]
            },
            'medical_history': {
                'keywords': ['history', 'condition', 'diagnosed', 'previous', 'existing', 'chronic'],
                'importance': 0.6,
                'questions': [
                    "Do you have any underlying medical conditions?",
                    "Have you had {condition} or similar issues before?",
                    "Is there a family history of {condition} or related conditions?"
                ]
            },
            'triggers': {
                'keywords': ['trigger', 'cause', 'makes it worse', 'worsens', 'improves', 'alleviates', 'helps'],
                'importance': 0.7,
                'questions': [
                    "Have you identified any triggers for your {condition}?",
                    "Does anything seem to make your symptoms worse?",
                    "Have you noticed any patterns related to when symptoms appear?"
                ]
            },
            'tried_remedies': {
                'keywords': ['tried', 'treatment', 'medication', 'remedy', 'relief', 'helps', 'taken'],
                'importance': 0.5,
                'questions': [
                    "What treatments have you tried for {condition} so far?",
                    "Have any remedies or medications helped with your symptoms?",
                    "What approaches have you found effective in managing {condition}?"
                ]
            },
            # Added specialized allergies category
            'allergies': {
                'keywords': ['allergy', 'allergies', 'allergic', 'allergen', 'seasonal'],
                'importance': 0.9,
                'questions': [
                    "During which seasons do you typically experience your allergy symptoms?",
                    "Which symptoms are most bothersome for you? (e.g., runny nose, itchy eyes, sneezing)",
                    "Have you noticed any specific triggers for your allergies?",
                    "Have you tried any treatments for your allergic symptoms?"
                ]
            }
        }
        
    def reset_conversation(self):
        """Reset the conversation state to initial values."""
        self.conversation_id = str(uuid.uuid4())[:12]  # Better unique ID
        self.conversation_history = []
        self.follow_up_questions_asked = 0
        self.max_follow_up_questions = 3  # Limit follow-up questions to avoid loops
        self.current_query_type = None
        self.original_query = None
        self.current_topic = None
        self.missing_information = {}
        self.collected_information = {}
        self.conversation_complete = False
        # Reset answered questions tracking
        self.answered_questions = set()
        
    def _initialize_question_templates(self):
        """Initialize templates for follow-up questions by medical context."""
        self.question_templates = {
            # Symptom-related follow-up questions
            'symptoms': [
                "How long have you been experiencing {symptom}?",
                "On a scale of 1-10, how would you rate the severity of {symptom}?",
                "How often do you experience {symptom}?",
                "Is {symptom} constant or does it come and go?",
                "Have you noticed anything that triggers or worsens {symptom}?",
                "Are there any other symptoms occurring alongside {symptom}?",
                "Where exactly do you experience {symptom} (which part of the body)?",
                "Have you tried anything that helps relieve {symptom}?"
            ],
            
            # Treatment-related follow-up questions
            'treatment': [
                "What treatments or remedies have you already tried for {condition}?",
                "Do you have any allergies or reactions to medications?",
                "Are you currently taking any medications?",
                "Do you have any underlying health conditions?",
                "What specific aspects of {condition} treatment are you interested in?",
                "Are you looking for information on medication, lifestyle changes, or other approaches?"
            ],
            
            # Prevention-related follow-up questions
            'prevention': [
                "Do you have any risk factors for {condition}?",
                "Is there a family history of {condition}?",
                "What prevention methods have you already implemented?",
                "Are you looking for primary prevention or ways to prevent complications?",
                "Are you interested in lifestyle changes, screening recommendations, or other preventive measures?"
            ],
            
            # Duration-specific follow-up questions
            'duration': [
                "How long have you been experiencing these symptoms?",
                "When did you first notice these symptoms?",
                "Is this a recent development or a long-term issue?",
                "Have the symptoms been constant or intermittent over this period?"
            ],
            
            # Severity-specific follow-up questions
            'severity': [
                "How would you describe the severity of your symptoms?",
                "On a scale of 1-10, how would you rate the intensity?",
                "Are the symptoms mild, moderate, or severe?",
                "Is this affecting your daily activities or sleep?"
            ],
            
            # Allergy-specific follow-up questions
            'allergies': [
                "During which seasons do you typically experience allergy symptoms?",
                "Which allergy symptoms bother you the most?",
                "Have you identified any specific triggers for your allergies?",
                "Do your symptoms improve when you're indoors with air conditioning?",
                "Have you tried any over-the-counter allergy medications?"
            ],
            
            # General follow-up questions
            'general': [
                "Could you provide more details about your question regarding {topic}?",
                "What specific aspect of {topic} are you most interested in learning about?",
                "Is there a particular reason you're asking about {topic}?",
                "Are you asking for yourself or someone else?",
                "Is there any additional context that might help me provide better information?"
            ]
        }
    
    def _initialize_ambiguity_patterns(self):
        """Initialize patterns for detecting ambiguity in medical queries."""
        self.ambiguity_patterns = {
            # Patterns for vague symptoms
            'vague_symptoms': [
                r'(?i)feel(?:ing)?\s+(?:unwell|bad|off|weird|strange|sick)',
                r'(?i)something\s+(?:wrong|off|weird|strange)',
                r'(?i)not\s+(?:feeling|seeming)\s+right',
                r'(?i)general(?:ly)?\s+(?:unwell|ill)',
                r'(?i)under\s+the\s+weather'
            ],
            
            # Patterns for missing context
            'missing_context': [
                r'(?i)(?:is|are)\s+(?:this|these|it|that)\s+(?:normal|serious|concerning|bad)',
                r'(?i)(?:should|do)\s+(?:i|one|you)\s+(?:worry|be\s+concerned)',
                r'(?i)what\s+(?:does|could|might|is)\s+(?:this|it|that)',
                r'(?i)why\s+(?:do|does|am|is|are)',
                r'(?i)(?:how|what)\s+(?:to|about)\s+(?:my|this)'
            ],
            
            # Patterns for multiple conditions
            'multiple_conditions': [
                r'(?i)(?:and|or)\s+(?:also|additionally|too)',
                r'(?i)(?:plus|along\s+with|together\s+with|as\s+well\s+as)',
                r'(?i)(?:both|multiple|several|various)\s+(?:issues|problems|symptoms|conditions)'
            ],
            
            # Patterns indicating need for follow-up on duration
            'needs_duration': [
                r'(?i)(?:pain|ache|discomfort|symptom|issue|problem)',
                r'(?i)(?:feeling|experiencing|having)',
                r'(?i)(?:cough|headache|fever|rash)'
            ],
            
            # Patterns indicating need for follow-up on severity
            'needs_severity': [
                r'(?i)(?:pain|ache|discomfort|hurt)',
                r'(?i)(?:bad|serious|severe|mild)',
                r'(?i)(?:symptom|issue|problem)'
            ]
        }
    
    def add_user_message(self, message: str) -> None:
        """
        Add a user message to the conversation history.
        
        Args:
            message: The user's message text
        """
        # Store the original query if this is the first message
        if not self.conversation_history:
            self.original_query = message
            
        # Add message to history with timestamp
        self.conversation_history.append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Analyze the message
        self._analyze_user_message(message)
    
    def add_system_message(self, message: str, is_follow_up: bool = False) -> None:
        """
        Add a system (chatbot) message to the conversation history.
        
        Args:
            message: The system's message text
            is_follow_up: Whether this message is a follow-up question
        """
        message_type = 'follow_up_question' if is_follow_up else 'response'
        
        # Add message to history with timestamp
        self.conversation_history.append({
            'role': 'system',
            'content': message,
            'type': message_type,
            'timestamp': datetime.now().isoformat()
        })
        
        # If this was a follow-up question, increment the count
        if is_follow_up:
            self.follow_up_questions_asked += 1
    
    def _analyze_user_message(self, message: str) -> None:
        """
        Analyze a user message to determine query type and extract key information.
        
        Args:
            message: The user's message text
        """
        # Determine message type (if this is a follow-up response or initial query)
        if self.follow_up_questions_asked > 0:
            # This is a response to a follow-up question
            self._process_follow_up_response(message)
        else:
            # This is an initial query
            message_lower = message.lower()
            
            # Determine the query type 
            self.current_query_type = self._determine_query_type(message_lower)
            
            # Extract key topic
            self.current_topic = self._extract_main_topic(message_lower)
            
            # Check for missing information
            self.missing_information = self._identify_missing_information(message_lower)
            
            # If topic is about allergies, trigger specific allergy-related questions
            if self.current_topic and ('allerg' in self.current_topic.lower() or 'season' in self.current_topic.lower()):
                if 'allergies' not in self.missing_information:
                    self.missing_information['allergies'] = 0.95  # High priority
    
    def _determine_query_type(self, message: str) -> str:
        """
        Determine the type of medical query.
        
        Args:
            message: The user's message text (lowercase)
            
        Returns:
            Query type category (symptoms, treatment, etc.)
        """
        query_types = {
            'symptoms': ['symptom', 'feel', 'experiencing', 'having', 'notice', 'signs'],
            'treatment': ['treat', 'cure', 'therapy', 'remedy', 'medication', 'manage'],
            'prevention': ['prevent', 'avoid', 'reduce risk', 'protect', 'stop'],
            'cause': ['cause', 'reason', 'why', 'what causes', 'from', 'due to'],
            'diagnosis': ['diagnose', 'test', 'confirm', 'identify', 'check']
        }
        
        scores = {category: 0 for category in query_types}
        
        for category, keywords in query_types.items():
            for keyword in keywords:
                if keyword in message:
                    scores[category] += 1
        
        # Special handling for allergies
        if 'allerg' in message or 'seasonal' in message:
            scores['symptoms'] += 2  # Boost symptoms score for allergy questions
        
        max_score = max(scores.values())
        
        if max_score > 0:
            for category, score in scores.items():
                if score == max_score:
                    return category
        
        return 'general'
    
    def _extract_main_topic(self, message: str) -> Optional[str]:
        """
        Extract the main medical topic from the user's message.
        
        Args:
            message: The user's message text (lowercase)
            
        Returns:
            Main topic string or None if not found
        """
        # Handle common patterns first
        if "seasonal allergies" in message:
            return "seasonal allergies"
        if "allergies" in message and "seasonal" in message:
            return "seasonal allergies"
        if "allergies" in message:
            return "allergies"
        
        # Common patterns for topic extraction
        patterns = [
            # "What causes [topic]"
            r'(?i)what\s+(?:causes|is|are)\s+(?:the\s+)?(?:cause|reason|symptoms|treatment|cure)s?\s+(?:of|for)\s+([a-z\s\-]+)(?:\?|\.|\s|$)',
            
            # "How to treat [topic]"
            r'(?i)how\s+(?:to|do\s+i|can\s+i|should\s+i)\s+(?:treat|manage|handle|deal\s+with|cure|prevent)\s+([a-z\s\-]+)(?:\?|\.|\s|$)',
            
            # "[topic] symptoms"
            r'(?i)([a-z\s\-]+)\s+symptoms(?:\?|\.|\s|$)',
            
            # More generic "[topic]" extraction as fallback
            r'(?i)(?:about|regarding|concerning|for|with)\s+([a-z\s\-]+)(?:\?|\.|\s|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                topic = match.group(1).strip()
                # Filter out very short topics or stop words
                if len(topic.split()) >= 1 and len(topic) > 3:
                    # Check for allergies in the extracted topic
                    if "seasonal allergies" in topic.lower():
                        return "seasonal allergies"
                    if "allergies" in topic.lower() and "seasonal" in topic.lower():
                        return "seasonal allergies"
                    if "allergies" in topic.lower():
                        return "allergies"
                    return topic
        
        # Check for direct mentions of common medical conditions
        common_conditions = [
            'headache', 'migraine', 'cold', 'flu', 'fever', 'cough', 'asthma',
            'diabetes', 'hypertension', 'arthritis', 'allergy', 'depression',
            'anxiety', 'insomnia', 'heartburn', 'eczema', 'acne', 'rash'
        ]
        
        for condition in common_conditions:
            if condition in message:
                return condition
        
        # Special handling for symptom questions with no clear topic
        if "symptoms" in message and "common" in message:
            return "common symptoms"
        
        return None
    
    def _identify_missing_information(self, message: str) -> Dict[str, float]:
        """
        Identify potentially missing information in the user query.
        
        Args:
            message: The user's message text (lowercase)
            
        Returns:
            Dictionary of missing information categories with confidence scores
        """
        missing_info = {}
        
        # Special handling for allergy-related queries
        if self.current_topic and ('allerg' in self.current_topic.lower() or 'season' in self.current_topic.lower()):
            # Check for missing allergy-specific information
            allergy_keywords = [
                'season', 'time of year', 'spring', 'summer', 'fall', 'winter',
                'pollen', 'dust', 'mold', 'pet', 'food', 'indoor', 'outdoor'
            ]
            
            if not any(keyword in message.lower() for keyword in allergy_keywords):
                missing_info['allergies'] = 0.95  # High priority
            
            # Also check for symptom severity and duration
            for category in ['severity', 'duration']:
                if not any(keyword in message for keyword in self.information_categories[category]['keywords']):
                    missing_info[category] = self.information_categories[category]['importance']
                    
            return missing_info
        
        # Skip if we couldn't determine a topic
        if not self.current_topic:
            return missing_info
        
        # Check for missing information based on query type
        if self.current_query_type == 'symptoms':
            # For symptom queries, check for missing duration, severity, and frequency
            for category in ['duration', 'severity', 'frequency']:
                if not any(keyword in message for keyword in self.information_categories[category]['keywords']):
                    missing_info[category] = self.information_categories[category]['importance']
                    
            # Check if location is missing for physical symptoms
            physical_symptoms = ['pain', 'ache', 'discomfort', 'rash', 'swelling', 'tingling', 'numbness']
            if any(symptom in self.current_topic for symptom in physical_symptoms):
                if not any(keyword in message for keyword in self.information_categories['location']['keywords']):
                    missing_info['location'] = self.information_categories['location']['importance']
        
        elif self.current_query_type == 'treatment':
            # For treatment queries, check for tried remedies and medical history
            for category in ['tried_remedies', 'medical_history']:
                if not any(keyword in message for keyword in self.information_categories[category]['keywords']):
                    missing_info[category] = self.information_categories[category]['importance']
        
        elif self.current_query_type == 'prevention':
            # For prevention queries, check for medical history and triggers
            for category in ['medical_history', 'triggers']:
                if not any(keyword in message for keyword in self.information_categories[category]['keywords']):
                    missing_info[category] = self.information_categories[category]['importance']
        
        # Check for general ambiguity in the query
        for ambiguity_type, patterns in self.ambiguity_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message):
                    if ambiguity_type == 'vague_symptoms':
                        missing_info['symptom_specification'] = 0.9
                    elif ambiguity_type == 'missing_context':
                        missing_info['context'] = 0.8
                    elif ambiguity_type == 'multiple_conditions':
                        missing_info['condition_clarification'] = 0.7
                    elif ambiguity_type == 'needs_duration' and 'duration' not in missing_info:
                        missing_info['duration'] = 0.8
                    elif ambiguity_type == 'needs_severity' and 'severity' not in missing_info:
                        missing_info['severity'] = 0.7
        
        return missing_info
    
    def _process_follow_up_response(self, message: str) -> None:
        """
        Process a user's response to a follow-up question.
        
        Args:
            message: The user's response to a follow-up question
        """
        # Get the last follow-up question that was asked
        last_question = None
        for entry in reversed(self.conversation_history):
            if entry['role'] == 'system' and entry.get('type') == 'follow_up_question':
                last_question = entry['content']
                break
        
        if not last_question:
            return
        
        # Track this question as answered to avoid repeating
        self.answered_questions.add(last_question)
        
        # Determine what information category this question was asking about
        info_category = self._determine_question_category(last_question)
        
        if info_category:
            # Extract and store the provided information
            self.collected_information[info_category] = message
            
            # Remove this category from missing information
            if info_category in self.missing_information:
                del self.missing_information[info_category]
        
        # Update conversation completion status
        self._update_conversation_status()
    
    def _determine_question_category(self, question: str) -> Optional[str]:
        """
        Determine which information category a follow-up question was asking about.
        
        Args:
            question: The follow-up question text
            
        Returns:
            Information category or None if not determined
        """
        question_lower = question.lower()
        
        # Special handling for allergy-specific questions
        if any(term in question_lower for term in ['season', 'allergen', 'allerg', 'trigger']):
            if 'seasonal allergies' in self.current_topic or 'allergies' in self.current_topic:
                return 'allergies'
        
        # Check against each information category's keywords
        for category, info in self.information_categories.items():
            if any(keyword in question_lower for keyword in info['keywords']):
                return category
        
        return None
    
    def _update_conversation_status(self) -> None:
        """Update the conversation completion status based on current state."""
        # Mark conversation as complete if:
        # 1. We've asked the maximum number of follow-up questions
        # 2. There's no more missing critical information
        # 3. We've received responses for all asked questions
        
        if self.follow_up_questions_asked >= self.max_follow_up_questions:
            self.conversation_complete = True
            return
        
        # Check if there's any critical missing information
        critical_missing = False
        for category, importance in self.missing_information.items():
            if importance >= 0.7:  # Importance threshold for critical information
                critical_missing = True
                break
        
        if not critical_missing:
            self.conversation_complete = True
    
    def get_next_follow_up_question(self) -> Optional[str]:
        """
        Get the next most appropriate follow-up question based on missing information.
        
        Returns:
            Follow-up question text or None if no more questions needed
        """
        # Don't ask more questions if conversation is complete or max questions reached
        if self.conversation_complete or self.follow_up_questions_asked >= self.max_follow_up_questions:
            return None
        
        # Sort missing information by importance
        if not self.missing_information:
            return None
            
        sorted_missing = sorted(
            self.missing_information.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Get the most important missing information category
        next_category, _ = sorted_missing[0]
        
        # Generate a question for this category
        question = self._generate_question_for_category(next_category)
        
        # Ensure we don't repeat questions
        attempts = 0
        while question in self.answered_questions and attempts < 5:
            # Try to generate a different question
            question = self._generate_question_for_category(next_category)
            attempts += 1
            
            # If we can't generate a unique question after 5 attempts, try the next category
            if attempts >= 5 and len(sorted_missing) > 1:
                next_category = sorted_missing[1][0]
                question = self._generate_question_for_category(next_category)
                
        return question
    
    def _generate_question_for_category(self, category: str) -> str:
        """
        Generate a follow-up question for a specific information category.
        
        Args:
            category: The information category
            
        Returns:
            Question text
        """
        # Use specialized handling for allergies
        if category == 'allergies' and ('allerg' in (self.current_topic or '') or 'season' in (self.current_topic or '')):
            # Use allergy-specific questions
            questions = self.question_templates.get('allergies', [
                "During which seasons do you typically experience allergy symptoms?",
                "Which allergy symptoms bother you the most?",
                "Have you identified any specific triggers for your allergies?"
            ])
            return random.choice(questions)
        
        # Get questions from information categories first, fall back to templates if not found
        if category in self.information_categories and 'questions' in self.information_categories[category]:
            questions = self.information_categories[category]['questions']
        elif category in self.question_templates:
            questions = self.question_templates[category]
        else:
            # Fall back to general questions if category not found
            questions = self.question_templates['general']
        
        # Select a question from available templates
        if not questions:  # Handle empty questions list
            return f"Could you tell me more about your {self.current_topic or 'symptoms'}?"
            
        question = random.choice(questions)
        
        # Prepare values for template substitution
        topic = self.current_topic or "this health topic"
        symptom = self.current_topic or "these symptoms"  
        condition = self.current_topic or "this condition"
        
        # Handle plurals properly
        if symptom.endswith('s') and '{symptom}' in question:
            # For plural symptoms, ensure proper grammar
            question = question.replace('the {symptom}', '{symptom}')
            question = question.replace('this {symptom}', 'these symptoms')
        
        # Replace template variables carefully
        question = question.replace('{topic}', topic)
        question = question.replace('{symptom}', symptom)
        question = question.replace('{condition}', condition)
        
        return question
    
    def is_conversation_complete(self) -> bool:
        """
        Check if the conversation has gathered enough information.
        
        Returns:
            True if conversation is complete, False otherwise
        """
        return self.conversation_complete
    
    def get_enhanced_prompt(self) -> str:
        """
        Generate an enhanced prompt with all collected information.
        
        Returns:
            Enhanced prompt text for final response generation
        """
        if not self.original_query:
            return ""
        
        # Start with the original query
        enhanced_prompt = f"Original question: {self.original_query}\n\n"
        
        # Add additional context from follow-up questions
        if self.collected_information:
            enhanced_prompt += "Additional information:\n"
            for category, information in self.collected_information.items():
                enhanced_prompt += f"- {category.replace('_', ' ').title()}: {information}\n"
        
        # Add query type and topic
        if self.current_query_type:
            enhanced_prompt += f"\nQuery type: {self.current_query_type}\n"
        if self.current_topic:
            enhanced_prompt += f"Topic: {self.current_topic}\n"
        
        # Add instruction for comprehensive response
        enhanced_prompt += "\nBased on ALL the information above, provide a comprehensive and "
        enhanced_prompt += "detailed response to the original question, incorporating the "
        enhanced_prompt += "additional context provided through follow-up questions."
        
        return enhanced_prompt
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current conversation state.
        
        Returns:
            Dictionary with conversation summary information
        """
        return {
            'conversation_id': self.conversation_id,
            'original_query': self.original_query,
            'query_type': self.current_query_type,
            'topic': self.current_topic,
            'follow_up_questions_asked': self.follow_up_questions_asked,
            'missing_information': self.missing_information,
            'collected_information': self.collected_information,
            'is_complete': self.conversation_complete,
            'message_count': len(self.conversation_history)
        }
    
    def get_formatted_conversation(self) -> str:
        """
        Get a formatted string representation of the conversation history.
        
        Returns:
            Formatted conversation history text
        """
        if not self.conversation_history:
            return "No conversation history."
        
        formatted = []
        for entry in self.conversation_history:
            role = "You" if entry['role'] == 'user' else "Assistant"
            formatted.append(f"{role}: {entry['content']}")
        
        return "\n\n".join(formatted)