import re
import logging
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import random
from src.fallback_content import MedicalFallbackContent
from src.safety_filters import *

class ResponseFormatter:
    """
    Enhanced response formatter for structuring medical responses with proper sections,
    content formatting, and fallback mechanisms to ensure high-quality information.
    """
    
    def __init__(self, logger=None):
        """Initialize with response templates and section definitions."""
        # Set up logging
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize section templates with emojis for visual organization
        self.section_templates = {
            'overview': "📋 Overview:\n{content}\n\n",
            'definition': "📝 Definition and Overview:\n{content}\n\n",
            'symptoms': "🔍 Key Symptoms and Signs:\n{content}\n\n",
            'causes': "⚠️ Causes and Risk Factors:\n{content}\n\n",
            'diagnosis': "🔬 Diagnosis and Testing:\n{content}\n\n",
            'treatment': "💊 Treatment Options:\n{content}\n\n",
            'prevention': "🛡️ Prevention and Self-Care:\n{content}\n\n",
            'recommendations': "✅ Recommendations:\n{content}\n\n",
            'guidelines': "📊 General Guidelines:\n{content}\n\n",
            'considerations': "⚖️ Important Considerations:\n{content}\n\n",
            'warnings': "⚡ Warning Signs:\n{content}\n\n",
            'when_to_seek': "🏥 When to Seek Medical Attention:\n{content}\n\n",
            'resources': "📚 Additional Resources:\n{content}\n\n",
            'note': "ℹ️ Note:\n{content}\n\n"
        }
        
        # Define query type patterns to detect specific health topics
        self.query_patterns = {
            'water_intake': r'water\s+intake|hydration|drink\s+water|daily\s+water',
            'blood_pressure': r'blood\s+pressure|hypertension|BP\s+reading|pressure\s+range',
            'cholesterol': r'cholesterol|lipids?|HDL|LDL|triglyceride',
            'seasonal_allergies': r'allerg(y|ies)|seasonal|hay\s+fever|pollen|rhinitis',
            'headache': r'headache|migraine|head\s+pain',
            'back_pain': r'back\s+pain|spine|lumbar|sciatica',
            'sleep': r'sleep|insomnia|rest|bedtime',
            'nutrition': r'nutrition|diet|food|eating|meal',
            'exercise': r'exercise|workout|fitness|physical\s+activity'
        }
        
        # Initialize fallback content database
        self._initialize_fallback_content()
        
    def _initialize_fallback_content(self):
        """Initialize comprehensive fallback content for common medical topics."""
        self.fallback_content = {
            'water_intake': {
                'overview': "The recommended daily water intake is approximately 3.7 liters (15.5 cups) for men and 2.7 liters (11.5 cups) for women, according to the U.S. National Academies of Sciences, Engineering, and Medicine. This includes water from all beverages and foods.",
                'guidelines': "• Drink water throughout the day rather than all at once\n• Use thirst as an initial guide, but don't rely solely on it\n• Urine color should be pale yellow to clear when properly hydrated\n• About 20% of daily water intake typically comes from food\n• The remaining 80% comes from beverages, including water",
                'considerations': "• Higher intake may be needed during exercise, hot weather, illness, or pregnancy\n• Certain medical conditions may require different hydration levels\n• Older adults should monitor hydration carefully as thirst sensation decreases with age\n• Individual needs vary based on activity level, climate, and health status"
            },
            
            'blood_pressure': {
                'overview': "Normal blood pressure is considered to be below 120/80 mmHg. The top number (systolic) represents the pressure when the heart beats, while the bottom number (diastolic) represents the pressure when the heart rests between beats.",
                'guidelines': "• Normal: Less than 120/80 mmHg\n• Elevated: 120-129/less than 80 mmHg\n• Hypertension Stage 1: 130-139/80-89 mmHg\n• Hypertension Stage 2: 140+/90+ mmHg\n• Hypertensive Crisis: Higher than 180/120 mmHg (requires immediate medical attention)",
                'considerations': "• Blood pressure can fluctuate throughout the day\n• Multiple readings over time provide more accurate assessment\n• Various factors like stress, caffeine, and activity can temporarily affect readings\n• Regular blood pressure checks are recommended for all adults\n• More frequent monitoring for those with elevated readings or risk factors"
            },
            
            'cholesterol': {
                'overview': "Cholesterol can be managed naturally through lifestyle modifications including dietary changes, regular exercise, and weight management. These approaches can significantly impact your cholesterol levels.",
                'guidelines': "• Increase soluble fiber intake (oats, beans, fruits)\n• Consume heart-healthy fats (olive oil, nuts, avocados)\n• Limit saturated and trans fats\n• Add plant sterols and stanols to your diet\n• Consider omega-3 fatty acids from fish or supplements\n• Engage in regular physical activity (150+ minutes/week)\n• Maintain a healthy weight or lose weight if needed\n• Limit alcohol consumption\n• Quit smoking\n• Manage stress effectively",
                'considerations': "• Results typically require 3-6 months of consistent changes\n• Individual responses to dietary changes vary\n• Some people may still need medication despite lifestyle changes\n• Regular monitoring is important to track progress\n• Consult healthcare providers before making significant changes"
            },
            
            'seasonal_allergies': {
                'overview': "Seasonal allergies, also known as allergic rhinitis or hay fever, are immune reactions to specific airborne substances that appear during certain times of the year, typically when plants pollinate.",
                'symptoms': "• Nasal congestion and runny nose with clear discharge\n• Sneezing and postnasal drip\n• Itchy, watery, or red eyes\n• Itchy throat, ears, or face\n• Temporary loss of smell or taste\n• Fatigue and irritability\n• Headaches and potential sinus pressure",
                'causes': "• Tree pollen (typically in spring)\n• Grass pollen (typically in late spring and summer)\n• Weed pollen (typically in fall, especially ragweed)\n• Mold spores (can occur in any season, especially in damp weather)",
                'treatment': "• Monitoring pollen counts and limiting outdoor exposure when high\n• Keeping windows closed during high pollen seasons\n• Showering and changing clothes after outdoor activities\n• Using air purifiers with HEPA filters\n• Over-the-counter antihistamines, nasal sprays, or eye drops\n• Prescription medications for severe symptoms\n• Immunotherapy (allergy shots) for long-term treatment"
            },
            
            'general': {
                'overview': "This health topic involves several important factors that affect overall well-being and may require lifestyle adjustments or medical intervention depending on severity.",
                'guidelines': "• Consult healthcare professionals for personalized advice\n• Follow established medical recommendations\n• Make gradual, sustainable lifestyle changes\n• Regular monitoring may be necessary\n• Multiple approaches often work better than single interventions",
                'considerations': "• Individual responses vary based on personal health factors\n• Evidence-based approaches are recommended for management\n• Prevention is often more effective than treatment\n• Consistency is key for long-term management"
            }
        }
    
    def structure_response(self, raw_text: str, query: str = "", query_type: str = "general") -> str:
        """
        Structure raw text into a well-formatted medical response with appropriate
        sections, formatting, and content.
        
        Args:
            raw_text: Raw text from the model
            query: Original user query 
            query_type: Type of medical query (optional)
            
        Returns:
            Structured response with proper formatting
        """
        try:
            # Detect query type if not provided
            if not query_type or query_type == "general":
                detected_type = self._detect_query_type(query)
                if detected_type:
                    query_type = detected_type
            
            # Clean the raw text
            cleaned_text = self._clean_text(raw_text)
            
            # Check if we have enough content
            if not cleaned_text or len(cleaned_text.strip()) < 30:
                # Use fallback content for this query type
                return self._generate_fallback_response(query_type, query)
            
            # Extract sections from the text
            sections = self._extract_sections(cleaned_text)
            
            # If extraction failed or insufficient sections were found, use pattern-based extraction
            if not sections or len(sections) < 2:
                sections = self._extract_sections_by_patterns(cleaned_text)
            
            # If still insufficient, use fallback content
            if not sections or len(sections) < 2:
                return self._generate_fallback_response(query_type, query)
            
            # Format the sections
            formatted_response = self._format_sections(sections, query_type)
            
            # Add additional sections if needed
            if 'when_to_seek' not in sections and query_type in ['seasonal_allergies', 'headache', 'pain']:
                formatted_response += self._generate_when_to_seek_section(query_type)
            
            # Add timestamp
            formatted_response += f"Information Last Updated: {datetime.now().strftime('%Y-%m-%d')}"
            
            return formatted_response
            
        except Exception as e:
            self.logger.error(f"Error in structure_response: {str(e)}")
            # Return fallback response on error
            return self._generate_fallback_response(query_type, query)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize raw text."""
        if not text:
            return ""
        
        # Remove redundant occurrences of "Medical Information on..." 
        text = re.sub(r'Medical Information on [\'"].*?[\'"]:', '', text)
        
        # Remove repeated phrases
        text = re.sub(r'(\b\w+\b)\s+\1', r'\1', text)
        
        # Remove unnecessary quotation marks
        text = text.replace('"', '').replace("'", "")
        
        # Fix spacing
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s*\n\s*', '\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _detect_query_type(self, query: str) -> str:
        """Detect the type of query to use appropriate response format."""
        if not query:
            return "general"
            
        query_lower = query.lower()
        
        # Check against patterns for each query type
        for qtype, pattern in self.query_patterns.items():
            if re.search(pattern, query_lower):
                return qtype
        
        # Special handling for common questions
        if "recommend" in query_lower and "water" in query_lower:
            return "water_intake"
        if "normal" in query_lower and "blood pressure" in query_lower:
            return "blood_pressure"
        if "reduc" in query_lower and "cholesterol" in query_lower:
            return "cholesterol"
        if "symptom" in query_lower and "allerg" in query_lower:
            return "seasonal_allergies"
            
        return "general"
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract sections from the text using common section headers."""
        sections = {}
        
        # Common section markers
        section_markers = {
            'overview': r'(?:Overview|Definition|Introduction|About):',
            'symptoms': r'(?:Symptoms|Signs|Clinical presentation):',
            'causes': r'(?:Causes|Etiology|Risk factors):',
            'diagnosis': r'(?:Diagnosis|Testing|Assessment|Evaluation):',
            'treatment': r'(?:Treatment|Management|Therapy|Intervention):',
            'prevention': r'(?:Prevention|Prophylaxis|Avoidance):',
            'considerations': r'(?:Considerations|Important|Precautions|Notes):',
            'guidelines': r'(?:Guidelines|Recommendations|Best practices):',
            'when_to_seek': r'(?:When to seek|Medical attention|Emergency|Warning signs):'
        }
        
        # Find all potential section starts
        section_matches = []
        for section_type, pattern in section_markers.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                section_matches.append((match.start(), section_type, match.group()))
        
        # Sort by position in text
        section_matches.sort()
        
        # Extract content between sections
        for i, (pos, section_type, marker) in enumerate(section_matches):
            # Find start position (after the marker)
            start_pos = pos + len(marker)
            
            # Find end position (start of next section or end of text)
            if i < len(section_matches) - 1:
                end_pos = section_matches[i+1][0]
            else:
                end_pos = len(text)
                
            # Extract and clean content
            content = text[start_pos:end_pos].strip()
            sections[section_type] = content
        
        return sections
    
    def _extract_sections_by_patterns(self, text: str) -> Dict[str, str]:
        """Extract sections using common patterns when headers aren't clearly defined."""
        sections = {}
        
        # Try to identify an overview/introduction (usually starts the text)
        intro_match = re.match(r'^(.+?)(?=\n\n|\n[A-Z])', text, re.DOTALL)
        if intro_match:
            sections['overview'] = intro_match.group(1).strip()
        
        # Look for bullet point lists (recommendations, symptoms, etc.)
        bullet_lists = re.findall(r'(?:^|\n)(?:(?:\d+\.|\*|\-)\s+.+\n)+', text, re.MULTILINE)
        if bullet_lists:
            # First bullet list is often symptoms or recommendations
            if 'symptoms' not in sections and any(symptom_word in text.lower() for symptom_word in ['symptom', 'sign', 'feel', 'experience']):
                sections['symptoms'] = bullet_lists[0].strip()
            else:
                sections['guidelines'] = bullet_lists[0].strip()
            
            # Second bullet list might be treatments or considerations
            if len(bullet_lists) > 1:
                if 'treatment' not in sections and any(treatment_word in text.lower() for treatment_word in ['treat', 'manage', 'therapy']):
                    sections['treatment'] = bullet_lists[1].strip()
                else:
                    sections['considerations'] = bullet_lists[1].strip()
        
        # Try to find content about seeking medical attention
        seek_medical_match = re.search(r'(?:seek\s+medical|doctor|healthcare\s+provider|emergency).{3,200}', text, re.IGNORECASE | re.DOTALL)
        if seek_medical_match:
            sections['when_to_seek'] = seek_medical_match.group(0).strip()
        
        return sections
    
    def _format_sections(self, sections: Dict[str, str], query_type: str) -> str:
        """Format extracted sections into a cohesive response."""
        formatted_response = ""
        
        # Define preferred section order based on query type
        section_order = {
            'general': ['overview', 'symptoms', 'causes', 'treatment', 'prevention', 'guidelines', 'considerations', 'when_to_seek'],
            'water_intake': ['overview', 'guidelines', 'considerations'],
            'blood_pressure': ['overview', 'guidelines', 'considerations', 'when_to_seek'],
            'cholesterol': ['overview', 'guidelines', 'treatment', 'considerations'],
            'seasonal_allergies': ['overview', 'symptoms', 'causes', 'treatment', 'prevention', 'when_to_seek'],
        }
        
        # Get preferred order for this query type or use general
        preferred_order = section_order.get(query_type, section_order['general'])
        
        # Iterate through preferred order, adding sections if they exist
        for section_type in preferred_order:
            if section_type in sections and sections[section_type]:
                # Format the content
                content = self._format_section_content(sections[section_type], section_type)
                # Add to response using template
                formatted_response += self.section_templates.get(section_type, "{content}\n\n").format(content=content)
        
        # Add any remaining sections not in the preferred order
        for section_type, content in sections.items():
            if section_type not in preferred_order and content:
                formatted_content = self._format_section_content(content, section_type)
                formatted_response += self.section_templates.get(section_type, "{content}\n\n").format(content=formatted_content)
        
        return formatted_response
    
    def _format_section_content(self, content: str, section_type: str) -> str:
        """Format the content of a section for better readability."""
        # Turn sentences into bullet points for certain section types
        bullet_point_sections = ['symptoms', 'causes', 'treatment', 'prevention', 'guidelines', 'considerations']
        
        if section_type in bullet_point_sections and not any(line.strip().startswith(('•', '-', '*', '1.')) for line in content.split('\n')):
            # Split content into sentences
            sentences = re.split(r'(?<=[.!?])\s+', content)
            
            # Convert sentences to bullet points
            bullet_points = []
            for sentence in sentences:
                if sentence.strip():
                    bullet_points.append(f"• {sentence.strip()}")
            
            content = "\n".join(bullet_points)
        
        # If content already has bullet points but with different markers, standardize them
        if any(line.strip().startswith(('-', '*', '1.')) for line in content.split('\n')):
            lines = content.split('\n')
            standardized_lines = []
            
            for line in lines:
                stripped = line.strip()
                if stripped.startswith(('-', '*')):
                    standardized_lines.append(f"• {stripped[1:].strip()}")
                elif re.match(r'^\d+\.', stripped):
                    standardized_lines.append("• " + re.sub(r'^\d+\.\s*', '', stripped))
                else:
                    standardized_lines.append(line)
                    
            content = "\n".join(standardized_lines)
        
        return content
    
    def _generate_fallback_response(self, query_type: str, query: str) -> str:
        """Generate a fallback response when extraction fails."""
        # First try to use topic-specific fallback content
        if query_type in self.fallback_content:
            topic_content = self.fallback_content[query_type]
            
            formatted_response = ""
            
            # Add all available sections for this topic
            for section_type, content in topic_content.items():
                formatted_response += self.section_templates.get(section_type, "{content}\n\n").format(content=content)
                
            # Add medical information title
            if query:
                title = f"Medical Information on '{query}':\n\n"
                formatted_response = title + formatted_response
                
            # Add standard disclaimer
            disclaimer = ("\nDisclaimer: This information is for educational purposes only and provides general medical guidance. "
                        "It should not be considered a substitute for professional medical advice, diagnosis, or treatment. "
                        "Always consider individual health variations and consult healthcare providers for personalized medical "
                        "recommendations tailored to your specific health needs and individual medical history.\n\n")
                
            # Add timestamp
            timestamp = f"Information Last Updated: {datetime.now().strftime('%Y-%m-%d')}"
            
            return formatted_response + disclaimer + timestamp
            
        # If no specific fallback content, use general format
        else:
            # Use general fallback content
            return self._generate_fallback_response("general", query)
            
    def _generate_when_to_seek_section(self, query_type: str) -> str:
        """Generate a 'When to Seek Medical Attention' section based on query type."""
        seek_medical_content = {
            'seasonal_allergies': "• If symptoms are severe or significantly affect quality of life\n• If over-the-counter medications aren't providing relief\n• If allergies trigger or worsen asthma symptoms\n• If you develop signs of infection like fever or yellow/green nasal discharge\n• If symptoms persist for more than two weeks despite treatment",
            'headache': "• If headache is sudden and severe (thunderclap headache)\n• If headache follows a head injury\n• If headache is accompanied by fever, stiff neck, confusion, seizures, double vision, weakness, numbness, or difficulty speaking\n• If headache gets progressively worse over days\n• If headache changes pattern or is different from previous headaches",
            'pain': "• If pain is severe or prevents normal activities\n• If pain is accompanied by unexplained weight loss or fever\n• If pain follows an injury\n• If pain is accompanied by loss of bowel or bladder control\n• If pain is accompanied by weakness, numbness, or tingling",
            'general': "• If symptoms are severe or rapidly worsening\n• If symptoms persist despite home treatment\n• If symptoms significantly interfere with daily activities\n• If symptoms are accompanied by warning signs like high fever, difficulty breathing, or changes in consciousness\n• If you have underlying health conditions that may complicate the situation"
        }
        
        content = seek_medical_content.get(query_type, seek_medical_content['general'])
        return self.section_templates['when_to_seek'].format(content=content)