# fallback_content.py

class MedicalFallbackContent:
    """Provides fallback medical content when dataset knowledge is unavailable."""
    
    @staticmethod
    def get_water_intake():
        return {
            "overview": "The recommended daily water intake is approximately 3.7 liters (15.5 cups) for men and 2.7 liters (11.5 cups) for women, according to the U.S. National Academies of Sciences, Engineering, and Medicine. This includes water from all beverages and foods.",
            "key_info": "About 20% of daily water intake typically comes from food. The remaining 80% comes from beverages, including water. Individual needs vary based on activity level, climate, and health status.",
            "guidelines": "Drink water throughout the day rather than all at once. Use thirst as an initial guide, but don't rely solely on it. Urine color should be pale yellow to clear when properly hydrated.",
            "considerations": "Higher intake may be needed during exercise, hot weather, illness, or pregnancy. Certain medical conditions may require different hydration levels. Older adults should monitor hydration carefully as thirst sensation decreases with age."
        }
    
    @staticmethod
    def get_blood_pressure():
        return {
            "overview": "Normal blood pressure is considered to be below 120/80 mmHg. The top number (systolic) represents the pressure when the heart beats, while the bottom number (diastolic) represents the pressure when the heart rests between beats.",
            "key_info": "Blood pressure categories include: Normal (Less than 120/80 mmHg), Elevated (120-129/less than 80 mmHg), Hypertension Stage 1 (130-139/80-89 mmHg), Hypertension Stage 2 (140+/90+ mmHg), and Hypertensive Crisis (Higher than 180/120 mmHg - requires immediate medical attention).",
            "guidelines": "Regular blood pressure checks are recommended for all adults. More frequent monitoring is advised for those with elevated readings or risk factors. Home monitoring may be beneficial for ongoing assessment.",
            "considerations": "Blood pressure can fluctuate throughout the day. Multiple readings over time provide more accurate assessment. Various factors like stress, caffeine, and activity can temporarily affect readings."
        }
    
    @staticmethod
    def get_heart_health():
        return {
            "overview": "Heart health refers to the overall condition and functioning of your heart. Maintaining good heart health is essential for overall well-being and longevity.",
            "key_info": "The heart is a muscular organ that pumps blood throughout the body, supplying oxygen and nutrients to tissues and removing carbon dioxide and other wastes. Cardiovascular disease remains the leading cause of death globally.",
            "guidelines": "Maintain a healthy diet rich in fruits, vegetables, whole grains, and lean proteins. Exercise regularly, aiming for at least 150 minutes of moderate-intensity activity per week. Avoid smoking and limit alcohol consumption. Manage stress through relaxation techniques or mindfulness practices. Maintain a healthy weight and get regular check-ups.",
            "considerations": "Family history of heart disease increases risk. Age, gender, and ethnicity can influence heart disease risk. Certain medical conditions like diabetes or high blood pressure significantly increase heart disease risk. Early detection and treatment of risk factors can prevent complications."
        }
    
    @staticmethod
    def get_ibuprofen():
        return {
            "overview": "Ibuprofen is a nonsteroidal anti-inflammatory drug (NSAID) used to reduce fever and treat pain or inflammation. It's available over-the-counter or by prescription in various forms including tablets, capsules, and oral suspensions.",
            "key_info": "Ibuprofen works by reducing hormones that cause inflammation and pain in the body. It's commonly used for headaches, toothaches, back pain, arthritis, menstrual cramps, or minor injuries.",
            "guidelines": "For adults, typical dosage is 200-400mg every 4-6 hours as needed, not exceeding 1200mg in 24 hours without doctor supervision. Take with food or milk to reduce stomach upset. Use the lowest effective dose for the shortest duration needed.",
            "side_effects": "Common side effects include stomach pain, heartburn, nausea, vomiting, headache, dizziness, and rash. Serious side effects requiring immediate medical attention include shortness of breath, chest pain, slurred speech, black/bloody stools, and swelling.",
            "considerations": "Not recommended for those with certain conditions including heart problems, hypertension, kidney disease, or history of stomach ulcers. May interact with various medications including aspirin, blood thinners, and ACE inhibitors. Not recommended during late pregnancy."
        }
    
    @staticmethod
    def get_seasonal_allergies():
        return {
            "overview": "Seasonal allergies, also known as allergic rhinitis or hay fever, are immune reactions to specific airborne substances that appear during certain times of the year, typically when plants pollinate.",
            "symptoms": "Common symptoms include nasal congestion, runny nose with clear discharge, sneezing, postnasal drip, itchy or watery eyes, itchy throat or ears, temporary loss of smell, fatigue, and irritability.",
            "causes": "Common triggers include tree pollen (spring), grass pollen (late spring and summer), weed pollen (fall, especially ragweed), and mold spores (can occur in any season, especially in damp weather).",
            "management": "Management approaches include monitoring pollen counts and limiting outdoor exposure when high, keeping windows closed during high pollen seasons, showering after outdoor activities, using air purifiers with HEPA filters, and medication options including over-the-counter antihistamines, nasal sprays, or prescription treatments for severe cases."
        }
    
    @staticmethod
    def get_content_by_topic(topic: str):
        """Get fallback content for a specific topic or return general health information."""
        
        topic_lower = topic.lower()
        
        if any(term in topic_lower for term in ["water", "hydration", "drink", "fluid"]):
            return MedicalFallbackContent.get_water_intake()
            
        if any(term in topic_lower for term in ["blood pressure", "hypertension", "bp"]):
            return MedicalFallbackContent.get_blood_pressure()
            
        if any(term in topic_lower for term in ["heart", "cardiovascular", "cardiac"]):
            return MedicalFallbackContent.get_heart_health()
            
        if any(term in topic_lower for term in ["ibuprofen", "advil", "motrin", "nsaid"]):
            return MedicalFallbackContent.get_ibuprofen()
            
        if any(term in topic_lower for term in ["allergy", "allergies", "hay fever", "seasonal"]):
            return MedicalFallbackContent.get_seasonal_allergies()
            
        # Return general health information if no specific topic matches
        return {
            "overview": "Maintaining good health involves balanced nutrition, regular physical activity, adequate sleep, stress management, and preventive healthcare.",
            "key_info": "The World Health Organization defines health as 'a state of complete physical, mental and social well-being and not merely the absence of disease or infirmity.'",
            "guidelines": "Eat a balanced diet rich in fruits, vegetables, whole grains, and lean proteins. Exercise regularly, aiming for at least 150 minutes of moderate activity weekly. Get 7-9 hours of quality sleep per night. Manage stress through relaxation techniques. Get regular check-ups and screenings.",
            "considerations": "Individual health needs vary based on age, gender, genetic factors, and pre-existing conditions. Consult healthcare professionals for personalized advice and recommendations."
        }