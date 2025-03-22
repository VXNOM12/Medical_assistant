import re
import logging
from typing import Dict, Any, Optional, List

class QuestionAnalyzer:
    def __init__(self):
        """Initialize the question analyzer with comprehensive medical analysis capabilities."""
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize knowledge bases
        self._initialize_knowledge_bases()

    def _initialize_knowledge_bases(self):
        """Initialize knowledge bases for question analysis."""
        # Advanced categorization with more nuanced categories
        self.categories = {
            'diagnostic': {
                'keywords': [
                    'diagnose', 'symptoms', 'condition', 'what is', 
                    'identify', 'check for', 'test for', 'signs of'
                ],
                'weight': 2
            },
            'treatment': {
                'keywords': [
                    'cure', 'treat', 'medication', 'remedy', 
                    'therapy', 'heal', 'manage', 'control'
                ],
                'weight': 1.5
            },
            'prevention': {
                'keywords': [
                    'prevent', 'avoid', 'risk', 'reduce', 
                    'stop', 'protect', 'safeguard', 'mitigate'
                ],
                'weight': 1.3
            },
            'management': {
                'keywords': [
                    'handle', 'cope', 'live with', 'deal with', 
                    'manage', 'control', 'support', 'adapt'
                ],
                'weight': 1
            },
            'general': {
                'keywords': [
                    'information', 'learn', 'understand', 'about', 
                    'tell me', 'explain', 'what are'
                ],
                'weight': 0.5
            }
        }

        # Emergency and sensitive topic detection
        self.emergency_patterns = [
            r'(emergency|urgent|critical|severe)',
            r'(heart attack|stroke|seizure|overdose)',
            r'(bleeding|unconscious|not breathing)',
            r'(suicide|kill myself|want to die)'
        ]

        # Restricted medical advice topics
        self.restricted_topics = [
            'prescribe', 'diagnosis', 'treatment plan', 
            'medical advice', 'specific medication'
        ]

    def categorize_query(self, query: str) -> str:
        """
        Advanced query categorization with weighted scoring.
        
        Args:
            query: User's medical query
            
        Returns:
            Most likely query category
        """
        if not query or not isinstance(query, str):
            return 'general'

        query_lower = query.lower()
        category_scores = {}

        # Check emergency patterns first
        for pattern in self.emergency_patterns:
            if re.search(pattern, query_lower):
                return 'emergency'

        # Check for restricted topics
        if any(topic in query_lower for topic in self.restricted_topics):
            return 'restricted'

        # Calculate weighted scores for categories
        for category, config in self.categories.items():
            score = sum(
                config['weight'] if keyword in query_lower else 0 
                for keyword in config['keywords']
            )
            category_scores[category] = score

        # Return category with highest score
        return max(category_scores, key=category_scores.get)

    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Comprehensive query analysis.
        
        Args:
            query: User's medical query
            
        Returns:
            Detailed analysis of the query
        """
        analysis = {
            'original_query': query,
            'category': self.categorize_query(query),
            'needs_clarification': False,
            'suggested_questions': []
        }

        # Emergency detection
        if analysis['category'] == 'emergency':
            analysis.update({
                'needs_clarification': False,
                'emergency_message': (
                    "🚨 EMERGENCY ALERT: This appears to be a medical emergency. "
                    "Please call emergency services immediately."
                )
            })
            return analysis

        # Restricted topic handling
        if analysis['category'] == 'restricted':
            analysis.update({
                'needs_clarification': True,
                'suggested_questions': [
                    "Can I help you find general health information?",
                    "Would you like to rephrase your question?",
                    "I can provide educational health information."
                ]
            })
            return analysis

        # Complexity analysis
        complexity_indicators = [
            r'\b(how|why|what)\b',
            r'\b(might|could|possibly)\b',
            r'\b(symptoms|condition|disease)\b'
        ]

        analysis['complexity'] = any(
            re.search(pattern, query.lower()) 
            for pattern in complexity_indicators
        )

        # Vagueness detection
        vague_terms = [
            'something', 'not feeling well', 'weird', 
            'strange', 'issue', 'problem'
        ]
        analysis['is_vague'] = any(
            term in query.lower() 
            for term in vague_terms
        )

        # Suggest clarification if vague or complex
        if analysis['is_vague'] or analysis['complexity']:
            analysis['needs_clarification'] = True
            analysis['suggested_questions'] = [
                "Could you provide more specific details?",
                "Can you elaborate on what you're experiencing?",
                "What specific aspects are you most concerned about?"
            ]

        return analysis

    def extract_key_terms(self, query: str) -> List[str]:
        """
        Extract key medical terms from the query.
        
        Args:
            query: User's medical query
            
        Returns:
            List of identified key terms
        """
        # Basic medical term extraction logic
        medical_terms = [
            'diabetes', 'hypertension', 'cancer', 'heart disease', 
            'asthma', 'arthritis', 'migraine', 'depression', 'anxiety'
        ]

        return [
            term for term in medical_terms 
            if term.lower() in query.lower()
        ]

def main():
    """Demonstrate QuestionAnalyzer functionality."""
    analyzer = QuestionAnalyzer()
    
    test_queries = [
        "What are the symptoms of diabetes?",
        "I'm having chest pain, is this serious?",
        "How can I prevent heart disease?",
        "Something feels wrong, can you help?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        analysis = analyzer.analyze_query(query)
        print(f"Category: {analysis['category']}")
        
        if analysis.get('needs_clarification'):
            print("Suggested Follow-up Questions:")
            for q in analysis.get('suggested_questions', []):
                print(f"- {q}")

if __name__ == "__main__":
    main()