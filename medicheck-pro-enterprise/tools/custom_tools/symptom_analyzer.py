from typing import Dict, Any, List
import asyncio
import re


class SymptomAnalyzerTool:
    """
    Custom tool for analyzing symptoms and suggesting possible conditions.
    """
    
    def __init__(self):
        # In a real implementation, this would connect to a comprehensive symptom database
        self._symptom_condition_map = self._load_symptom_database()
    
    def _load_symptom_database(self) -> Dict[str, Any]:
        """
        Load symptom to condition mapping database.
        In a real implementation, this would load from a comprehensive medical database.
        """
        # Placeholder for symptom-condition database
        return {
            "chest pain": ["myocardial infarction", "angina", "costochondritis", "gastroesophageal reflux disease"],
            "shortness of breath": ["asthma", "heart failure", "pulmonary embolism", "pneumonia"],
            "headache": ["migraine", "tension headache", "cluster headache", "meningitis"],
            "abdominal pain": ["appendicitis", "gastroenteritis", "peptic ulcer", "gallstones"],
            "fever": ["infection", "flu", "pneumonia", "urinary tract infection"],
            "fatigue": ["anemia", "hypothyroidism", "depression", "chronic fatigue syndrome"],
            "weight loss": ["hyperthyroidism", "diabetes", "malignancy", "malabsorption"],
            "cough": ["upper respiratory infection", "asthma", "pneumonia", "chronic bronchitis"],
            "dizziness": ["orthostatic hypotension", "benign positional vertigo", "dehydration", "anemia"],
            "nausea": ["gastroenteritis", "pregnancy", "medication side effect", "migraine"],
            "joint pain": ["osteoarthritis", "rheumatoid arthritis", "gout", "lupus"],
            "rash": ["contact dermatitis", "eczema", "psoriasis", "allergic reaction"]
        }
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze symptoms and suggest possible conditions.
        """
        symptoms = input_data.get("symptoms", "")
        chief_complaint = input_data.get("chief_complaint", "")
        
        # Combine symptoms and chief complaint for analysis
        all_symptoms_text = f"{chief_complaint} {symptoms}".lower()
        
        # Extract individual symptoms from the text
        extracted_symptoms = self._extract_symptoms(all_symptoms_text)
        
        # Find possible conditions for each symptom
        possible_conditions = {}
        symptom_severity = {}
        
        for symptom in extracted_symptoms:
            conditions = self._get_possible_conditions(symptom)
            possible_conditions[symptom] = conditions
            
            # Determine symptom severity based on associated conditions
            severity = self._determine_symptom_severity(symptom, conditions)
            symptom_severity[symptom] = severity
        
        # Identify common conditions across multiple symptoms
        common_conditions = self._find_common_conditions(possible_conditions)
        
        return {
            "extracted_symptoms": extracted_symptoms,
            "possible_conditions": possible_conditions,
            "symptom_severity": symptom_severity,
            "common_conditions": common_conditions,
            "red_flags": self._identify_red_flags(extracted_symptoms),
            "urgency_assessment": self._assess_urgency(extracted_symptoms, common_conditions)
        }
    
    def _extract_symptoms(self, text: str) -> List[str]:
        """
        Extract symptoms from text input.
        """
        # Common symptoms that might appear in patient descriptions
        symptom_keywords = list(self._symptom_condition_map.keys())
        
        found_symptoms = []
        text_lower = text.lower()
        
        for symptom in symptom_keywords:
            if symptom in text_lower:
                found_symptoms.append(symptom)
        
        # Use regex to find other potential symptoms (simple implementation)
        # In a real implementation, this would use NLP techniques
        other_symptoms = re.findall(r'\b\w+ pain\b|\b\w+ ache\b|\bshortness of breath\b|\bfever\b|\bdizziness\b|\bnausea\b|\bvomiting\b|\bheadache\b|\bfatigue\b|\bweakness\b', text_lower)
        
        for symptom in other_symptoms:
            if symptom not in found_symptoms:
                found_symptoms.append(symptom.strip())
        
        # Remove duplicates while preserving order
        unique_symptoms = []
        for symptom in found_symptoms:
            if symptom not in unique_symptoms:
                unique_symptoms.append(symptom)
        
        return unique_symptoms
    
    def _get_possible_conditions(self, symptom: str) -> List[str]:
        """
        Get possible conditions associated with a symptom.
        """
        # Normalize the symptom to match our database
        normalized_symptom = symptom.lower().strip()
        
        # Look for exact match first
        if normalized_symptom in self._symptom_condition_map:
            return self._symptom_condition_map[normalized_symptom]
        
        # If no exact match, look for partial matches
        for db_symptom in self._symptom_condition_map:
            if normalized_symptom in db_symptom or db_symptom in normalized_symptom:
                return self._symptom_condition_map[db_symptom]
        
        # If no match found, return empty list
        return []
    
    def _determine_symptom_severity(self, symptom: str, conditions: List[str]) -> str:
        """
        Determine the severity of a symptom based on associated conditions.
        """
        # Conditions that indicate high severity
        high_severity_conditions = [
            "myocardial infarction", "pulmonary embolism", "meningitis", 
            "stroke", "sepsis", "anaphylaxis", "malignancy"
        ]
        
        # Check if any associated conditions are high severity
        for condition in conditions:
            if any(hsc in condition.lower() for hsc in high_severity_conditions):
                return "High"
        
        # Check for moderate severity conditions
        moderate_severity_conditions = [
            "angina", "heart failure", "pneumonia", "appendicitis", 
            "gallstones", "kidney stones"
        ]
        
        for condition in conditions:
            if any(msc in condition.lower() for msc in moderate_severity_conditions):
                return "Moderate"
        
        # Default to low severity
        return "Low"
    
    def _find_common_conditions(self, possible_conditions: Dict[str, List[str]]) -> List[str]:
        """
        Find conditions that are associated with multiple symptoms.
        """
        condition_counts = {}
        
        for symptom, conditions in possible_conditions.items():
            for condition in conditions:
                if condition in condition_counts:
                    condition_counts[condition] += 1
                else:
                    condition_counts[condition] = 1
        
        # Find conditions that appear with multiple symptoms
        common_conditions = [
            condition for condition, count in condition_counts.items() 
            if count > 1
        ]
        
        # Sort by count (most common first)
        common_conditions.sort(key=lambda x: condition_counts[x], reverse=True)
        
        return common_conditions
    
    def _identify_red_flags(self, symptoms: List[str]) -> List[str]:
        """
        Identify red flag symptoms that require immediate attention.
        """
        red_flags = []
        
        red_flag_symptoms = [
            "chest pain", "severe headache", "sudden vision loss", 
            "difficulty breathing", "severe abdominal pain", 
            "sudden weakness", "severe dizziness", "high fever"
        ]
        
        for symptom in symptoms:
            if any(rfs in symptom.lower() for rfs in red_flag_symptoms):
                red_flags.append(symptom)
        
        return red_flags
    
    def _assess_urgency(self, symptoms: List[str], common_conditions: List[str]) -> str:
        """
        Assess the overall urgency based on symptoms and possible conditions.
        """
        # Check for red flags first
        red_flags = self._identify_red_flags(symptoms)
        if red_flags:
            return "Immediate - Red flag symptoms present"
        
        # Check for high severity conditions
        high_severity_conditions = [
            "myocardial infarction", "pulmonary embolism", "meningitis", 
            "stroke", "sepsis", "anaphylaxis"
        ]
        
        for condition in common_conditions:
            if any(hsc in condition.lower() for hsc in high_severity_conditions):
                return "Urgent - Serious condition possible"
        
        # Check for moderate severity conditions
        moderate_severity_conditions = [
            "angina", "heart failure", "pneumonia", "appendicitis"
        ]
        
        for condition in common_conditions:
            if any(msc in condition.lower() for msc in moderate_severity_conditions):
                return "Prompt - Medical attention needed"
        
        # Default to routine
        return "Routine - Standard medical evaluation appropriate"
    
    async def get_symptom_timeline(self, symptom: str) -> Dict[str, Any]:
        """
        Get typical timeline and progression for a symptom.
        """
        # In a real implementation, this would query detailed symptom information
        timeline_map = {
            "chest pain": {
                "onset": "Sudden or gradual",
                "duration": "Minutes to hours",
                "progression": "May be constant or episodic",
                "associated_factors": ["Activity", "Stress", "Eating", "Position"]
            },
            "headache": {
                "onset": "Sudden (thunderclap) to gradual",
                "duration": "Minutes to days",
                "progression": "May be constant or pulsating",
                "associated_factors": ["Stress", "Sleep", "Food", "Environmental triggers"]
            },
            "abdominal pain": {
                "onset": "Sudden or gradual",
                "duration": "Minutes to days",
                "progression": "May localize or remain diffuse",
                "associated_factors": ["Eating", "Bowel movements", "Menstruation", "Position"]
            }
        }
        
        return timeline_map.get(symptom.lower(), {
            "onset": "Variable",
            "duration": "Variable",
            "progression": "Variable",
            "associated_factors": ["Multiple factors possible"]
        })