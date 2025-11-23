from typing import Dict, Any, List
import asyncio
from agents.base_agent import BaseAgent
from tools.builtin_tools.google_search import GoogleSearchTool
from tools.custom_tools.drug_interaction_checker import DrugInteractionCheckerTool
from tools.mcp_tools.patient_records import PatientRecordsMCP
from tools.openapi_tools.ehr_integration import EHROpenAPITool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage


class TreatmentAgent(BaseAgent):
    """
    Treatment Agent for evidence-based treatment recommendations.
    Uses LLM to suggest treatments based on diagnosis, patient history, and contraindications.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="treatment_agent",
            name="Treatment Agent",
            description="Evidence-based treatment recommendations"
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            max_tokens=2000
        )
        
        # Initialize tools
        self.google_search = GoogleSearchTool()
        self.drug_interaction_checker = DrugInteractionCheckerTool()
        self.patient_records = PatientRecordsMCP()
        self.ehr_integration = EHROpenAPITool()
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert medical treatment advisor. Based on the patient's diagnosis, medical history, and contraindications, provide evidence-based treatment recommendations.
            
            Consider:
            - Primary diagnosis and differential diagnoses
            - Patient's medical history and allergies
            - Current medications and potential interactions
            - Patient demographics and comorbidities
            - Clinical guidelines and best practices
            
            Provide recommendations for:
            1. Primary treatment options (ranked by appropriateness)
            2. Alternative treatments
            3. Medication recommendations with dosing
            4. Non-pharmacological interventions
            5. Monitoring requirements
            6. Contraindications and precautions"""),
            HumanMessage(content="""Patient Information:
Diagnosis: {diagnosis}
Medical History: {medical_history}
Current Medications: {current_medications}
Contraindications: {contraindications}
Treatment Preferences: {treatment_preferences}
Age: {age}
Weight: {weight}

Provide evidence-based treatment recommendations:""")
        ])
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute treatment recommendations based on patient information.
        """
        try:
            # Extract input data
            diagnosis = input_data.get("diagnosis", "")
            medical_history = input_data.get("medical_history", "")
            current_medications = input_data.get("current_medications", "")
            contraindications = input_data.get("contraindications", "")
            treatment_preferences = input_data.get("treatment_preferences", "")
            age = input_data.get("age", "Adult")
            weight = input_data.get("weight", "Unknown")
            
            # Check for drug interactions
            interaction_check = await self.drug_interaction_checker.run({
                "current_medications": current_medications,
                "potential_medications": []  # Will be populated based on recommendations
            })
            
            # Get patient records for additional context
            patient_history = await self.patient_records.get_patient_history(
                input_data.get("patient_id", "")
            )
            
            # Prepare the prompt with input data
            messages = self.prompt.format_messages(
                diagnosis=diagnosis,
                medical_history=medical_history,
                current_medications=current_medications,
                contraindications=contraindications,
                treatment_preferences=treatment_preferences,
                age=age,
                weight=weight
            )
            
            # Get LLM response
            response = await self.llm.ainvoke(messages)
            
            # Parse the response
            treatment_result = self._parse_treatment_response(response.content)
            
            # Enhance with drug interaction check
            treatment_result["drug_interaction_check"] = interaction_check
            treatment_result["patient_history"] = patient_history
            treatment_result["confidence"] = self._calculate_confidence(treatment_result)
            
            # Log the treatment recommendation
            self.logger.info(f"Treatment recommendations generated for diagnosis: {diagnosis}")
            
            return treatment_result
            
        except Exception as e:
            self.logger.error(f"Error in treatment recommendation: {str(e)}")
            return {
                "primary_treatments": [],
                "alternative_treatments": [],
                "medication_recommendations": [],
                "non_pharmacological_interventions": [],
                "monitoring_requirements": [],
                "contraindications_noted": [],
                "explanation": f"Error processing treatment recommendation: {str(e)}",
                "confidence": 0.0
            }
    
    def _parse_treatment_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the LLM response to extract treatment information.
        """
        # This is a simplified parsing - in a real implementation, 
        # this would use more sophisticated NLP techniques
        return {
            "primary_treatments": ["Primary treatment option 1", "Primary treatment option 2"],
            "alternative_treatments": ["Alternative treatment 1", "Alternative treatment 2"],
            "medication_recommendations": [
                {"name": "Medication 1", "dosage": "Dosage 1", "frequency": "Frequency 1"},
                {"name": "Medication 2", "dosage": "Dosage 2", "frequency": "Frequency 2"}
            ],
            "non_pharmacological_interventions": ["Intervention 1", "Intervention 2"],
            "monitoring_requirements": ["Monitoring requirement 1", "Monitoring requirement 2"],
            "contraindications_noted": ["Contraindication 1", "Contraindication 2"],
            "explanation": response_text
        }
    
    def _calculate_confidence(self, treatment_result: Dict[str, Any]) -> float:
        """
        Calculate confidence score for the treatment recommendations.
        """
        # In a real implementation, this would analyze various factors
        # like guideline adherence, evidence quality, etc.
        explanation = treatment_result.get("explanation", "")
        
        # Simple confidence calculation based on explanation length and keywords
        if len(explanation) > 300:
            return 0.9
        elif len(explanation) > 150:
            return 0.75
        else:
            return 0.6
    
    async def loop_treatment_recommendation(self, input_data: Dict[str, Any], max_iterations: int = 3) -> Dict[str, Any]:
        """
        Perform iterative treatment recommendations, refining based on feedback or outcomes.
        """
        current_input = input_data.copy()
        all_recommendations = []
        
        for iteration in range(max_iterations):
            # Get treatment recommendation
            recommendation = await self.execute(current_input)
            all_recommendations.append({
                "iteration": iteration + 1,
                "recommendation": recommendation
            })
            
            # Check if we should continue based on confidence or other criteria
            if recommendation.get("confidence", 0) > 0.8:
                break  # High confidence, no need to iterate further
            
            # Update input for next iteration with feedback
            current_input["previous_recommendation"] = recommendation
            current_input["iteration"] = iteration + 1
            
            # Add a small delay to avoid overwhelming the system
            await asyncio.sleep(0.1)
        
        return {
            "all_iterations": all_recommendations,
            "final_recommendation": all_recommendations[-1]["recommendation"] if all_recommendations else {},
            "iterations_completed": len(all_recommendations)
        }