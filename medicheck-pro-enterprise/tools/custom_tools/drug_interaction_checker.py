from typing import Dict, Any, List
import asyncio


class DrugInteractionCheckerTool:
    """
    Custom tool for checking potential drug interactions.
    """
    
    def __init__(self):
        # In a real implementation, this would connect to a comprehensive drug interaction database
        self._drug_interaction_db = self._load_interaction_database()
    
    def _load_interaction_database(self) -> Dict[str, Any]:
        """
        Load drug interaction database.
        In a real implementation, this would load from a comprehensive medical database.
        """
        # Placeholder for drug interaction database
        return {
            # Sample interactions - in reality this would be much more comprehensive
            "warfarin": ["aspirin", "ibuprofen", "naproxen", "amiodarone", "fluconazole"],
            "lisinopril": ["potassium", "spironolactone", "nsaids"],
            "metformin": ["contrast_dyes", "alcohol"],
            "simvastatin": ["clarithromycin", "itraconazole", "gemfibrozil"],
            "digoxin": ["amiodarone", "quinidine", "verapamil"],
            "sildenafil": ["nitrates", "nitroglycerin"]
        }
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for potential drug interactions.
        """
        current_medications = input_data.get("current_medications", [])
        potential_medications = input_data.get("potential_medications", [])
        
        # Normalize medication names for comparison
        current_meds_lower = [med.lower() if isinstance(med, str) else med.get("name", "").lower() 
                              for med in current_medications]
        potential_meds_lower = [med.lower() if isinstance(med, str) else med.get("name", "").lower() 
                                for med in potential_medications]
        
        # Check for interactions
        interactions = []
        
        for current_med in current_meds_lower:
            for potential_med in potential_meds_lower:
                if self._check_interaction(current_med, potential_med):
                    interaction = self._get_interaction_details(current_med, potential_med)
                    interactions.append(interaction)
        
        # Also check within current medications if no potential medications provided
        if not potential_medications:
            for i, med1 in enumerate(current_meds_lower):
                for j, med2 in enumerate(current_meds_lower[i+1:], i+1):
                    if self._check_interaction(med1, med2):
                        interaction = self._get_interaction_details(med1, med2)
                        interactions.append(interaction)
        
        return {
            "interactions_found": len(interactions) > 0,
            "interactions": interactions,
            "severity_summary": self._summarize_severity(interactions),
            "recommendations": self._generate_recommendations(interactions)
        }
    
    def _check_interaction(self, med1: str, med2: str) -> bool:
        """
        Check if two medications have a known interaction.
        """
        # Check both directions since interactions are bidirectional
        med1_interactions = self._drug_interaction_db.get(med1, [])
        med2_interactions = self._drug_interaction_db.get(med2, [])
        
        return med2 in med1_interactions or med1 in med2_interactions
    
    def _get_interaction_details(self, med1: str, med2: str) -> Dict[str, Any]:
        """
        Get detailed information about a drug interaction.
        """
        # In a real implementation, this would retrieve detailed interaction information
        # For now, we'll return a placeholder with basic information
        return {
            "medication_1": med1,
            "medication_2": med2,
            "interaction_type": "Potential interaction",
            "severity": self._determine_severity(med1, med2),
            "description": f"Potential interaction between {med1} and {med2}",
            "clinical_significance": self._determine_clinical_significance(med1, med2)
        }
    
    def _determine_severity(self, med1: str, med2: str) -> str:
        """
        Determine the severity of a drug interaction.
        """
        high_risk_pairs = [
            ("warfarin", "aspirin"), ("warfarin", "ibuprofen"), ("sildenafil", "nitrates"),
            ("digoxin", "verapamil"), ("metformin", "contrast_dyes")
        ]
        
        pair = (med1.lower(), med2.lower())
        if pair in high_risk_pairs or (pair[1], pair[0]) in high_risk_pairs:
            return "High"
        elif any(med in ["warfarin", "digoxin", "sildenafil", "metformin"] for med in pair):
            return "Moderate"
        else:
            return "Low"
    
    def _determine_clinical_significance(self, med1: str, med2: str) -> str:
        """
        Determine the clinical significance of a drug interaction.
        """
        severity = self._determine_severity(med1, med2)
        
        if severity == "High":
            return "Avoid combination; serious adverse effects possible"
        elif severity == "Moderate":
            return "Use with caution; monitor for adverse effects"
        else:
            return "Minor interaction; generally acceptable"
    
    def _summarize_severity(self, interactions: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Summarize the severity of found interactions.
        """
        severity_counts = {"High": 0, "Moderate": 0, "Low": 0}
        
        for interaction in interactions:
            severity = interaction.get("severity", "Low")
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        return severity_counts
    
    def _generate_recommendations(self, interactions: List[Dict[str, Any]]) -> List[str]:
        """
        Generate recommendations based on found interactions.
        """
        recommendations = []
        
        if not interactions:
            return ["No significant drug interactions detected"]
        
        high_risk_interactions = [i for i in interactions if i.get("severity") == "High"]
        if high_risk_interactions:
            recommendations.append("DISCONTINUE: High-risk interactions detected. Consult pharmacist or physician immediately.")
        
        moderate_interactions = [i for i in interactions if i.get("severity") == "Moderate"]
        if moderate_interactions:
            recommendations.append("MONITOR: Moderate-risk interactions. Monitor patient for adverse effects.")
        
        if not high_risk_interactions and not moderate_interactions:
            recommendations.append("Minor interactions detected. Generally acceptable but monitor as appropriate.")
        
        return recommendations
    
    async def get_interaction_risk_factors(self, medication: str) -> List[str]:
        """
        Get risk factors associated with a specific medication.
        """
        # In a real implementation, this would query detailed drug information
        risk_factors_map = {
            "warfarin": [
                "Bleeding risk",
                "INR monitoring required",
                "Dietary restrictions (vitamin K)",
                "Multiple drug interactions"
            ],
            "metformin": [
                "Risk of lactic acidosis",
                "Renal function monitoring",
                "Avoid with contrast procedures"
            ],
            "digoxin": [
                "Narrow therapeutic window",
                "Electrolyte monitoring (K+, Mg2+)",
                "Cardiac monitoring"
            ]
        }
        
        return risk_factors_map.get(medication.lower(), ["No specific risk factors found"])