from typing import Dict, Any
import asyncio
import requests
from app.config import get_config


class FHIROpenAPITool:
    """
    OpenAPI tool for interacting with FHIR (Fast Healthcare Interoperability Resources) compliant systems.
    Provides access to patient data, clinical resources, and healthcare information exchange.
    """
    
    def __init__(self):
        self.config = get_config()
        self.fhir_base_url = "https://fhir-server.example.com"  # Would be configured in a real implementation
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json+fhir"
        }
        # In a real implementation, this would include proper authentication
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute FHIR API operations based on the input data.
        """
        operation = input_data.get("operation", "")
        resource_type = input_data.get("resource_type", "")
        resource_id = input_data.get("resource_id", "")
        patient_id = input_data.get("patient_id", "")
        
        try:
            if operation == "read" and resource_type and resource_id:
                return await self.read_resource(resource_type, resource_id)
            elif operation == "search" and resource_type:
                search_params = input_data.get("search_params", {})
                return await self.search_resources(resource_type, search_params)
            elif operation == "patient_resources" and patient_id:
                resource_type = input_data.get("resource_type", "Observation")
                return await self.get_patient_resources(patient_id, resource_type)
            else:
                return {
                    "error": "Invalid operation or missing parameters",
                    "supported_operations": ["read", "search", "patient_resources"]
                }
        
        except Exception as e:
            return {
                "error": f"FHIR API operation failed: {str(e)}",
                "operation": operation
            }
    
    async def read_resource(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        """
        Read a specific FHIR resource by type and ID.
        """
        url = f"{self.fhir_base_url}/{resource_type}/{resource_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return {
                "resource_type": resource_type,
                "resource_id": resource_id,
                "data": response.json(),
                "status": "success"
            }
        
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Failed to read resource: {str(e)}",
                "resource_type": resource_type,
                "resource_id": resource_id
            }
    
    async def search_resources(self, resource_type: str, search_params: Dict[str, str]) -> Dict[str, Any]:
        """
        Search for FHIR resources of a specific type with given parameters.
        """
        url = f"{self.fhir_base_url}/{resource_type}"
        
        try:
            response = requests.get(url, headers=self.headers, params=search_params)
            response.raise_for_status()
            
            data = response.json()
            resources = data.get("entry", [])
            
            return {
                "resource_type": resource_type,
                "search_params": search_params,
                "total": data.get("total", len(resources)),
                "resources": [entry.get("resource", {}) for entry in resources],
                "status": "success"
            }
        
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Failed to search resources: {str(e)}",
                "resource_type": resource_type,
                "search_params": search_params
            }
    
    async def get_patient_resources(self, patient_id: str, resource_type: str) -> Dict[str, Any]:
        """
        Get all resources of a specific type for a given patient.
        """
        search_params = {"patient": patient_id}
        
        return await self.search_resources(resource_type, search_params)
    
    async def get_patient_demographics(self, patient_id: str) -> Dict[str, Any]:
        """
        Get patient demographics information.
        """
        return await self.read_resource("Patient", patient_id)
    
    async def get_patient_conditions(self, patient_id: str) -> Dict[str, Any]:
        """
        Get patient's medical conditions.
        """
        return await self.get_patient_resources(patient_id, "Condition")
    
    async def get_patient_medications(self, patient_id: str) -> Dict[str, Any]:
        """
        Get patient's medications.
        """
        return await self.get_patient_resources(patient_id, "MedicationRequest")
    
    async def get_patient_observations(self, patient_id: str, category: str = None) -> Dict[str, Any]:
        """
        Get patient's observations (lab results, vital signs, etc.).
        """
        search_params = {"patient": patient_id}
        if category:
            search_params["category"] = category
        
        return await self.get_patient_resources(patient_id, "Observation")
    
    async def get_patient_allergies(self, patient_id: str) -> Dict[str, Any]:
        """
        Get patient's allergies.
        """
        return await self.get_patient_resources(patient_id, "AllergyIntolerance")
    
    async def get_patient_procedures(self, patient_id: str) -> Dict[str, Any]:
        """
        Get patient's procedures.
        """
        return await self.get_patient_resources(patient_id, "Procedure")