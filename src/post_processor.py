import re
import language_tool_python
from medical_term_processor import MedicalTermChecker  # Assuming you have this

class ResponsePostProcessor:
    def __init__(self):
        self.grammar_tool = language_tool_python.LanguageTool('en-US')
        self.medical_checker = MedicalTermChecker()
        
        # Context-specific correction rules
        self.context_rules = [
            (r"\bloving\b", "looking"),
            (r"\bacesible\b", "accessible"),
            (r"\bWhats’s\b", "What's")
        ]

    def correct_response(self, text):
        # Step 1: Context-aware replacements
        for pattern, replacement in self.context_rules:
            text = re.sub(pattern, replacement, text)
            
        # Step 2: Grammar check (ignore medical terms)
        matches = self.grammar_tool.check(text)
        medical_terms = self.medical_checker.get_medical_terms()
        
        # Filter out matches that are medical terms
        filtered_matches = [
            match for match in matches
            if match.ruleId not in {'ENGLISH_WORD_REPEAT_RULE'}  # Example filter
            and not any(term in text for term in medical_terms)
        ]
        
        return language_tool_python.utils.correct(text, filtered_matches)