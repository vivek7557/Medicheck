from typing import Dict, Any, List
import asyncio
from datetime import datetime, timedelta


class LabResultsMCP:
    """
    Model Context Protocol tool for interacting with laboratory results.
    Provides access to patient lab results, imaging studies, and diagnostic tests.
    """
    
    def __init__(self):
        # In a real implementation, this would connect to a laboratory information system
        self._lab_results_database = {}
    
    async def get_latest_lab_results(self, patient_id: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Retrieve patient's latest lab results within the specified time period.
        """
        # In a real implementation, this would query a lab results database
        # For simulation, we'll return placeholder results
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Return simulated lab results
        return [
            {
                "test_name": "Complete Blood Count (CBC)",
                "date": "2023-10-15",
                "results": {
                    "WBC": {"value": 7.2, "unit": "x10^3/uL", "reference": "4.0-11.0", "status": "Normal"},
                    "RBC": {"value": 4.5, "unit": "x10^6/uL", "reference": "4.2-5.4", "status": "Normal"},
                    "Hemoglobin": {"value": 13.2, "unit": "g/dL", "reference": "12.0-15.5", "status": "Normal"},
                    "Hematocrit": {"value": 39.5, "unit": "%", "reference": "36.0-46.0", "status": "Normal"},
                    "Platelets": {"value": 280, "unit": "x10^3/uL", "reference": "150-450", "status": "Normal"}
                },
                "status": "Completed",
                "abnormal_flags": []
            },
            {
                "test_name": "Basic Metabolic Panel (BMP)",
                "date": "2023-10-15",
                "results": {
                    "Glucose": {"value": 145, "unit": "mg/dL", "reference": "70-99", "status": "High"},
                    "Creatinine": {"value": 1.1, "unit": "mg/dL", "reference": "0.6-1.2", "status": "Normal"},
                    "BUN": {"value": 18, "unit": "mg/dL", "reference": "7-20", "status": "Normal"},
                    "Sodium": {"value": 140, "unit": "mEq/L", "reference": "136-145", "status": "Normal"},
                    "Potassium": {"value": 4.2, "unit": "mEq/L", "reference": "3.5-5.0", "status": "Normal"},
                    "Chloride": {"value": 102, "unit": "mEq/L", "reference": "98-107", "status": "Normal"},
                    "CO2": {"value": 24, "unit": "mEq/L", "reference": "23-29", "status": "Normal"},
                    "Calcium": {"value": 9.8, "unit": "mg/dL", "reference": "8.5-10.2", "status": "Normal"}
                },
                "status": "Completed",
                "abnormal_flags": ["Glucose"]
            }
        ]
    
    async def get_lab_result_by_name(self, patient_id: str, test_name: str) -> List[Dict[str, Any]]:
        """
        Retrieve specific lab results by test name.
        """
        all_results = await self.get_latest_lab_results(patient_id, 365)  # Look back a year
        return [result for result in all_results if test_name.lower() in result["test_name"].lower()]
    
    async def get_historical_trends(self, patient_id: str, test_name: str) -> List[Dict[str, Any]]:
        """
        Get historical trends for a specific lab test.
        """
        # In a real implementation, this would query historical data
        # For simulation, we'll return placeholder trend data
        return [
            {
                "date": "2023-07-15",
                "value": 138,
                "unit": "mg/dL",
                "reference": "70-99",
                "status": "High"
            },
            {
                "date": "2023-08-15",
                "value": 142,
                "unit": "mg/dL",
                "reference": "70-99",
                "status": "High"
            },
            {
                "date": "2023-09-15",
                "value": 140,
                "unit": "mg/dL",
                "reference": "70-99",
                "status": "High"
            },
            {
                "date": "2023-10-15",
                "value": 145,
                "unit": "mg/dL",
                "reference": "70-99",
                "status": "High"
            }
        ]
    
    async def get_critical_values(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve any critical or abnormal lab values.
        """
        all_results = await self.get_latest_lab_results(patient_id)
        critical_results = []
        
        for result in all_results:
            if result["abnormal_flags"]:
                critical_results.append(result)
        
        return critical_results
    
    async def add_lab_result(self, patient_id: str, lab_result: Dict[str, Any]) -> bool:
        """
        Add a new lab result to the patient's record.
        """
        # In a real implementation, this would securely add to the lab database
        # For simulation, we'll just store in memory
        if patient_id not in self._lab_results_database:
            self._lab_results_database[patient_id] = []
        
        self._lab_results_database[patient_id].append(lab_result)
        return True
    
    async def get_imaging_studies(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve patient's imaging studies (X-rays, MRIs, CTs, etc.).
        """
        # For simulation, return placeholder imaging results
        return [
            {
                "study_type": "Chest X-Ray",
                "date": "2023-10-10",
                "finding": "Clear lung fields, no acute cardiopulmonary process",
                "status": "Completed",
                "radiologist": "Dr. Johnson",
                "follow_up_needed": False
            },
            {
                "study_type": "ECG",
                "date": "2023-10-10",
                "finding": "Normal sinus rhythm, no acute changes",
                "status": "Completed",
                "cardiologist": "Dr. Williams",
                "follow_up_needed": False
            }
        ]
    
    async def get_diagnostic_tests(self, patient_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve other diagnostic tests (not lab/imaging).
        """
        # For simulation, return placeholder diagnostic test results
        return [
            {
                "test_name": "HbA1c",
                "date": "2023-10-15",
                "value": 7.2,
                "unit": "%",
                "reference": "<5.7",
                "status": "High",
                "interpretation": "Indicates diabetes control needs improvement"
            }
        ]