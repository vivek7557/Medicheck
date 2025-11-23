from typing import Dict, Any, List
import asyncio
from datetime import datetime


class PatientRecordsMCP:
    """
    Model Context Protocol tool for interacting with patient records.
    Provides access to patient history, demographics, and medical records.
    """
    
    def __init__(self):
        # In a real implementation, this would connect to an EHR system
        self._patient_database = {}
    
    async def get_patient_history(self, patient_id: str) -> Dict[str, Any]:
        """
        Retrieve patient medical history.
        """
        # In a real implementation, this would query a secure patient database
        # For simulation, we'll return a placeholder
        if patient_id in self._patient_database:
            return self._patient_database[patient_id]
        else:
            # Return a simulated patient record
            return {
                "patient_id": patient_id,
                "demographics": {
                    "age": "45",
                    "gender": "Female",
                    "blood_type": "O+"
                },
                "medical_history": [
                    {"condition": "Hypertension", "diagnosed": "2020-01-15", "status": "Controlled"},
                    {"condition": "Type 2 Diabetes", "diagnosed": "2019-03-22", "status": "Managed"}
                ],
                "medications": [
                    {"name": "Lisinopril", "dosage": "10mg", "frequency": "Daily"},
                    {"name": "Metformin", "dosage": "500mg", "frequency": "BID"}
                ],
                "allergies": ["Penicillin"],
                "last_visit": "2023-10-15",
                "primary_care_physician": "Dr. Smith"
            }
    
    async def get_patient_demographics(self, patient_id: str) -> Dict[str, Any]:
        """
        Retrieve patient demographic information.
        """
        patient_record = await self.get_patient_history(patient_id)
        return patient_record.get("demographics", {})
    
    async def get_current_medications(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve patient's current medications.
        """
        patient_record = await self.get_patient_history(patient_id)
        return patient_record.get("medications", [])
    
    async def get_medical_conditions(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve patient's medical conditions.
        """
        patient_record = await self.get_patient_history(patient_id)
        return patient_record.get("medical_history", [])
    
    async def get_allergies(self, patient_id: str) -> List[str]:
        """
        Retrieve patient's allergies.
        """
        patient_record = await self.get_patient_history(patient_id)
        return patient_record.get("allergies", [])
    
    async def update_patient_record(self, patient_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update patient record with new information.
        """
        # In a real implementation, this would securely update the patient database
        # For simulation, we'll just store in memory
        if patient_id not in self._patient_database:
            self._patient_database[patient_id] = await self.get_patient_history(patient_id)
        
        # Update the record
        for key, value in updates.items():
            if key in self._patient_database[patient_id]:
                if isinstance(self._patient_database[patient_id][key], list):
                    self._patient_database[patient_id][key].extend(value)
                else:
                    self._patient_database[patient_id][key] = value
            else:
                self._patient_database[patient_id][key] = value
        
        return True
    
    async def add_medication(self, patient_id: str, medication: Dict[str, Any]) -> bool:
        """
        Add a medication to the patient's record.
        """
        current_medications = await self.get_current_medications(patient_id)
        current_medications.append(medication)
        
        return await self.update_patient_record(patient_id, {"medications": current_medications})
    
    async def add_condition(self, patient_id: str, condition: Dict[str, Any]) -> bool:
        """
        Add a medical condition to the patient's record.
        """
        current_conditions = await self.get_medical_conditions(patient_id)
        current_conditions.append(condition)
        
        return await self.update_patient_record(patient_id, {"medical_history": current_conditions})
    
    async def check_medication_interaction(self, patient_id: str, new_medication: str) -> Dict[str, Any]:
        """
        Check for potential interactions with patient's current medications.
        """
        current_meds = await self.get_current_medications(patient_id)
        
        # In a real implementation, this would query a drug interaction database
        # For simulation, we'll return placeholder results
        interactions = []
        for med in current_meds:
            if med["name"].lower() == new_medication.lower():
                interactions.append({
                    "interaction_type": "Duplicate therapy",
                    "severity": "Moderate",
                    "description": f"Potential duplicate therapy with {med['name']}"
                })
        
        return {
            "medication": new_medication,
            "current_medications": current_meds,
            "interactions": interactions,
            "safe_to_prescribe": len(interactions) == 0
        }