from typing import Dict, Any
import asyncio
import requests
from app.config import get_config


class EHROpenAPITool:
    """
    OpenAPI tool for integrating with Electronic Health Record (EHR) systems.
    Provides access to patient records, scheduling, and clinical documentation.
    """
    
    def __init__(self):
        self.config = get_config()
        self.ehr_base_url = "https://ehr-system.example.com"  # Would be configured in a real implementation
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        # In a real implementation, this would include proper authentication
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute EHR API operations based on the input data.
        """
        operation = input_data.get("operation", "")
        patient_id = input_data.get("patient_id", "")
        
        try:
            if operation == "get_patient_record":
                return await self.get_patient_record(patient_id)
            elif operation == "update_patient_record":
                updates = input_data.get("updates", {})
                return await self.update_patient_record(patient_id, updates)
            elif operation == "get_appointments":
                return await self.get_appointments(patient_id)
            elif operation == "schedule_appointment":
                appointment_data = input_data.get("appointment_data", {})
                return await self.schedule_appointment(patient_id, appointment_data)
            elif operation == "get_medications":
                return await self.get_medications(patient_id)
            elif operation == "add_medication":
                medication_data = input_data.get("medication_data", {})
                return await self.add_medication(patient_id, medication_data)
            else:
                return {
                    "error": "Invalid operation",
                    "supported_operations": [
                        "get_patient_record", "update_patient_record", 
                        "get_appointments", "schedule_appointment",
                        "get_medications", "add_medication"
                    ]
                }
        
        except Exception as e:
            return {
                "error": f"EHR API operation failed: {str(e)}",
                "operation": operation
            }
    
    async def get_patient_record(self, patient_id: str) -> Dict[str, Any]:
        """
        Get complete patient record from EHR.
        """
        url = f"{self.ehr_base_url}/patients/{patient_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return {
                "patient_id": patient_id,
                "data": response.json(),
                "status": "success"
            }
        
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Failed to get patient record: {str(e)}",
                "patient_id": patient_id
            }
    
    async def update_patient_record(self, patient_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update patient record in EHR.
        """
        url = f"{self.ehr_base_url}/patients/{patient_id}"
        
        try:
            response = requests.put(url, json=updates, headers=self.headers)
            response.raise_for_status()
            
            return {
                "patient_id": patient_id,
                "updates": updates,
                "status": "success",
                "updated_record": response.json()
            }
        
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Failed to update patient record: {str(e)}",
                "patient_id": patient_id
            }
    
    async def get_appointments(self, patient_id: str) -> Dict[str, Any]:
        """
        Get patient's appointments from EHR.
        """
        url = f"{self.ehr_base_url}/patients/{patient_id}/appointments"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            return {
                "patient_id": patient_id,
                "appointments": data,
                "status": "success",
                "count": len(data)
            }
        
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Failed to get appointments: {str(e)}",
                "patient_id": patient_id
            }
    
    async def schedule_appointment(self, patient_id: str, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Schedule a new appointment for the patient.
        """
        url = f"{self.ehr_base_url}/patients/{patient_id}/appointments"
        
        try:
            response = requests.post(url, json=appointment_data, headers=self.headers)
            response.raise_for_status()
            
            return {
                "patient_id": patient_id,
                "appointment_data": appointment_data,
                "new_appointment": response.json(),
                "status": "success"
            }
        
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Failed to schedule appointment: {str(e)}",
                "patient_id": patient_id
            }
    
    async def get_medications(self, patient_id: str) -> Dict[str, Any]:
        """
        Get patient's current medications from EHR.
        """
        url = f"{self.ehr_base_url}/patients/{patient_id}/medications"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            return {
                "patient_id": patient_id,
                "medications": data,
                "status": "success",
                "count": len(data)
            }
        
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Failed to get medications: {str(e)}",
                "patient_id": patient_id
            }
    
    async def add_medication(self, patient_id: str, medication_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new medication to patient's record.
        """
        url = f"{self.ehr_base_url}/patients/{patient_id}/medications"
        
        try:
            response = requests.post(url, json=medication_data, headers=self.headers)
            response.raise_for_status()
            
            return {
                "patient_id": patient_id,
                "medication_data": medication_data,
                "new_medication": response.json(),
                "status": "success"
            }
        
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Failed to add medication: {str(e)}",
                "patient_id": patient_id
            }
    
    async def get_clinical_notes(self, patient_id: str, encounter_id: str = None) -> Dict[str, Any]:
        """
        Get clinical notes for a patient, optionally for a specific encounter.
        """
        if encounter_id:
            url = f"{self.ehr_base_url}/patients/{patient_id}/encounters/{encounter_id}/notes"
        else:
            url = f"{self.ehr_base_url}/patients/{patient_id}/notes"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            return {
                "patient_id": patient_id,
                "encounter_id": encounter_id,
                "notes": data,
                "status": "success",
                "count": len(data)
            }
        
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Failed to get clinical notes: {str(e)}",
                "patient_id": patient_id,
                "encounter_id": encounter_id
            }
    
    async def add_clinical_note(self, patient_id: str, note_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a clinical note to patient's record.
        """
        url = f"{self.ehr_base_url}/patients/{patient_id}/notes"
        
        try:
            response = requests.post(url, json=note_data, headers=self.headers)
            response.raise_for_status()
            
            return {
                "patient_id": patient_id,
                "note_data": note_data,
                "new_note": response.json(),
                "status": "success"
            }
        
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Failed to add clinical note: {str(e)}",
                "patient_id": patient_id
            }