from typing import Dict, Any, List
import asyncio
from agents.base_agent import BaseAgent
from tools.builtin_tools.google_search import GoogleSearchTool
from tools.custom_tools.symptom_analyzer import SymptomAnalyzerTool
from tools.mcp_tools.medical_database import MedicalDatabaseMCP
from tools.openapi_tools.fhir_api import FHIROpenAPITool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage


class DiagnosisAgent(BaseAgent):
    """
    Diagnosis Agent for medical condition identification and analysis.
    Uses LLM to analyze symptoms, medical history, and other data to suggest possible diagnoses.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="diagnosis_agent",
            name="Diagnosis Agent",
            description="Medical condition identification and analysis"
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            max_tokens=1500
        )
        
        # Initialize tools
        self.google_search = GoogleSearchTool()
        self.symptom_analyzer = SymptomAnalyzerTool()
        self.medical_database = MedicalDatabaseMCP()
        self.fhir_api = FHIROpenAPITool()
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert medical diagnostician. Analyze the provided patient information to suggest possible diagnoses.
            
            Consider:
            - Chief complaint and symptoms
            - Duration and severity
            - Medical history
            - Vital signs
            - Patient demographics
            
            Provide a ranked list of possible diagnoses with:
            1. Primary diagnosis (most likely)
            2. Differential diagnoses (alternative possibilities)
            3. Supporting evidence for each diagnosis
            4. Recommended diagnostic tests
            5. Confidence level for each diagnosis"""),
            HumanMessage(content="""Patient Information:
Chief Complaint: {chief_complaint}
Symptoms: {symptoms}
Duration: {duration}
Severity: {severity}
Additional Symptoms: {additional_symptoms}
Medical History: {medical_history}
Vital Signs: {vital_signs}

Provide your diagnostic analysis:""")
        ])
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute diagnosis based on patient information.
        """
        try:
            # Extract input data
            chief_complaint = input_data.get("chief_complaint", "")
            symptoms = input_data.get("symptoms", "")
            duration = input_data.get("duration", "")
            severity = input_data.get("severity", "Moderate")
            additional_symptoms = input_data.get("additional_symptoms", "")
            medical_history = input_data.get("medical_history", "")
            vital_signs = input_data.get("vital_signs", "")
            
            # Use symptom analyzer for initial assessment
            symptom_analysis = await self.symptom_analyzer.run({
                "symptoms": f"{symptoms} {additional_symptoms}",
                "chief_complaint": chief_complaint
            })
            
            # Query medical database for similar cases
            similar_cases = await self.medical_database.search_similar_cases({
                "symptoms": f"{symptoms} {additional_symptoms}",
                "demographics": input_data.get("demographics", {})
            })
            
            # Prepare the prompt with input data
            messages = self.prompt.format_messages(
                chief_complaint=chief_complaint,
                symptoms=symptoms,
                duration=duration,
                severity=severity,
                additional_symptoms=additional_symptoms,
                medical_history=medical_history,
                vital_signs=vital_signs
            )
            
            # Get LLM response
            response = await self.llm.ainvoke(messages)
            
            # Parse the response
            diagnosis_result = self._parse_diagnosis_response(response.content)
            
            # Enhance with symptom analysis and similar cases
            diagnosis_result["symptom_analysis"] = symptom_analysis
            diagnosis_result["similar_cases"] = similar_cases
            diagnosis_result["confidence"] = self._calculate_confidence(diagnosis_result)
            
            # Log the diagnosis
            self.logger.info(f"Diagnosis completed: {diagnosis_result['primary_diagnosis']}")
            
            return diagnosis_result
            
        except Exception as e:
            self.logger.error(f"Error in diagnosis: {str(e)}")
            return {
                "primary_diagnosis": "UNDETERMINED",
                "differential_diagnoses": [],
                "supporting_evidence": [],
                "recommended_tests": [],
                "explanation": f"Error processing diagnosis: {str(e)}",
                "confidence": 0.0
            }
    
    def _parse_diagnosis_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the LLM response to extract diagnosis information.
        """
        # This is a simplified parsing - in a real implementation, 
        # this would use more sophisticated NLP techniques
        return {
            "primary_diagnosis": "Primary diagnosis extracted from response",
            "differential_diagnoses": ["Differential diagnosis 1", "Differential diagnosis 2"],
            "supporting_evidence": ["Evidence 1", "Evidence 2"],
            "recommended_tests": ["Test 1", "Test 2"],
            "explanation": response_text
        }
    
    def _calculate_confidence(self, diagnosis_result: Dict[str, Any]) -> float:
        """
        Calculate confidence score for the diagnosis.
        """
        # In a real implementation, this would analyze various factors
        # like symptom consistency, medical history alignment, etc.
        explanation = diagnosis_result.get("explanation", "")
        
        # Simple confidence calculation based on explanation length and keywords
        if len(explanation) > 200:
            return 0.85
        elif len(explanation) > 100:
            return 0.7
        else:
            return 0.5
    
    async def sequential_diagnosis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform diagnosis in a sequential manner, refining the diagnosis with each step.
        """
        # Step 1: Initial broad diagnosis
        initial_result = await self.execute(input_data)
        
        # Step 2: Refine based on additional information
        refined_input = {
            **input_data,
            "initial_diagnosis": initial_result.get("primary_diagnosis"),
            "differential_diagnoses": initial_result.get("differential_diagnoses", [])
        }
        
        # Step 3: Search for more specific information
        if initial_result.get("primary_diagnosis"):
            search_query = f"medical guidelines {initial_result['primary_diagnosis']} diagnosis"
            search_results = await self.google_search.run({"query": search_query})
            refined_input["search_results"] = search_results
        
        # Step 4: Get final refined diagnosis
        final_result = await self.execute(refined_input)
        
        return {
            "initial_diagnosis": initial_result,
            "refined_diagnosis": final_result,
            "sequential_process": True
        }