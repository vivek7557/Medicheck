from typing import Dict, Any, List
import asyncio
from agents.base_agent import BaseAgent
from tools.builtin_tools.google_search import GoogleSearchTool
from tools.mcp_tools.medical_database import MedicalDatabaseMCP
from tools.openapi_tools.fhir_api import FHIROpenAPITool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage


class SpecialistRouterAgent(BaseAgent):
    """
    Specialist Router Agent for intelligent routing to appropriate specialists.
    Uses LLM to determine the most appropriate specialist based on diagnosis and patient factors.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="specialist_router_agent",
            name="Specialist Router Agent",
            description="Intelligent routing to appropriate specialists"
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            max_tokens=1000
        )
        
        # Initialize tools
        self.google_search = GoogleSearchTool()
        self.medical_database = MedicalDatabaseMCP()
        self.fhir_api = FHIROpenAPITool()
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert medical specialist router. Based on the patient's diagnosis, symptoms, and other factors, determine the most appropriate specialist to consult.
            
            Consider:
            - Primary diagnosis and differential diagnoses
            - Patient demographics and comorbidities
            - Urgency level
            - Geographic availability of specialists
            - Insurance/network considerations (if available)
            
            Provide:
            1. Recommended specialist type
            2. Justification for recommendation
            3. Suggested timeline for consultation
            4. Additional specialists to consider
            5. Pre-referral requirements"""),
            HumanMessage(content="""Patient Information:
Diagnosis: {diagnosis}
Symptoms: {symptoms}
Demographics: {demographics}
Urgency Level: {urgency_level}
Medical History: {medical_history}
Current Medications: {current_medications}

Determine the most appropriate specialist for referral:""")
        ])
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute specialist routing based on patient information.
        """
        try:
            # Extract input data
            diagnosis = input_data.get("diagnosis", "")
            symptoms = input_data.get("symptoms", "")
            demographics = input_data.get("demographics", {})
            urgency_level = input_data.get("urgency_level", "Routine")
            medical_history = input_data.get("medical_history", "")
            current_medications = input_data.get("current_medications", "")
            
            # Query medical database for specialist recommendations
            specialist_recommendations = await self.medical_database.get_specialist_recommendations({
                "diagnosis": diagnosis,
                "symptoms": symptoms,
                "urgency": urgency_level
            })
            
            # Prepare the prompt with input data
            messages = self.prompt.format_messages(
                diagnosis=diagnosis,
                symptoms=symptoms,
                demographics=str(demographics),
                urgency_level=urgency_level,
                medical_history=medical_history,
                current_medications=current_medications
            )
            
            # Get LLM response
            response = await self.llm.ainvoke(messages)
            
            # Parse the response
            routing_result = self._parse_routing_response(response.content)
            
            # Enhance with database recommendations
            routing_result["database_recommendations"] = specialist_recommendations
            routing_result["confidence"] = self._calculate_confidence(routing_result)
            
            # Log the routing decision
            self.logger.info(f"Specialist routing completed: {routing_result['recommended_specialist']}")
            
            return routing_result
            
        except Exception as e:
            self.logger.error(f"Error in specialist routing: {str(e)}")
            return {
                "recommended_specialist": "UNDETERMINED",
                "justification": f"Error processing specialist routing: {str(e)}",
                "timeline": "Immediate consultation required",
                "additional_considerations": ["Refer to general physician first"],
                "pre_referral_requirements": ["Complete basic workup"],
                "confidence": 0.0
            }
    
    def _parse_routing_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the LLM response to extract routing information.
        """
        # This is a simplified parsing - in a real implementation, 
        # this would use more sophisticated NLP techniques
        return {
            "recommended_specialist": "Recommended specialist type",
            "justification": response_text,
            "timeline": "Recommended timeline",
            "additional_considerations": ["Additional consideration 1", "Additional consideration 2"],
            "pre_referral_requirements": ["Requirement 1", "Requirement 2"],
            "confidence": 0.8
        }
    
    def _calculate_confidence(self, routing_result: Dict[str, Any]) -> float:
        """
        Calculate confidence score for the specialist routing.
        """
        # In a real implementation, this would analyze various factors
        # like diagnostic clarity, specialist availability, etc.
        explanation = routing_result.get("justification", "")
        
        # Simple confidence calculation based on explanation length and keywords
        if len(explanation) > 150:
            return 0.85
        elif len(explanation) > 75:
            return 0.7
        else:
            return 0.55
    
    async def route_with_consultation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route to specialist with consultation from other agents.
        """
        # First, get initial routing recommendation
        initial_routing = await self.execute(input_data)
        
        # Consult with other agents for additional input
        consultation_results = {}
        
        # If diagnosis is unclear, consult diagnosis agent for clarification
        if input_data.get("diagnosis_unclear", False):
            from agents.diagnosis_agent import DiagnosisAgent
            diagnosis_agent = DiagnosisAgent()
            clarification = await diagnosis_agent.execute(input_data)
            consultation_results["diagnosis_clarification"] = clarification
        
        # If treatment history is complex, consult treatment agent
        if input_data.get("complex_treatment_history", False):
            from agents.treatment_agent import TreatmentAgent
            treatment_agent = TreatmentAgent()
            treatment_review = await treatment_agent.execute(input_data)
            consultation_results["treatment_review"] = treatment_review
        
        # Combine initial routing with consultations
        final_routing = {
            **initial_routing,
            "consultation_results": consultation_results,
            "final_recommendation": self._combine_recommendations(
                initial_routing, 
                consultation_results
            )
        }
        
        return final_routing
    
    def _combine_recommendations(self, initial_routing: Dict[str, Any], consultation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine initial routing with consultation results to form final recommendation.
        """
        # In a real implementation, this would have more sophisticated logic
        # to combine multiple inputs and resolve conflicts
        return {
            "recommended_specialist": initial_routing.get("recommended_specialist"),
            "confidence": initial_routing.get("confidence", 0.0) + 0.1 if consultation_results else initial_routing.get("confidence", 0.0),
            "combined_justification": f"Initial: {initial_routing.get('justification', '')} | Consultations: {len(consultation_results)} reviewed"
        }