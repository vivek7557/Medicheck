from typing import Dict, Any, List
import asyncio
from agents.base_agent import BaseAgent
from tools.builtin_tools.google_search import GoogleSearchTool
from tools.custom_tools.symptom_analyzer import SymptomAnalyzerTool
from tools.mcp_tools.patient_records import PatientRecordsMCP
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage


class TriageAgent(BaseAgent):
    """
    Triage Agent for initial patient assessment and priority determination.
    Uses LLM to analyze symptoms and assign priority level.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="triage_agent",
            name="Triage Agent",
            description="Initial patient assessment and priority determination"
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            max_tokens=1000
        )
        
        # Initialize tools
        self.google_search = GoogleSearchTool()
        self.symptom_analyzer = SymptomAnalyzerTool()
        self.patient_records = PatientRecordsMCP()
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert medical triage assistant. Your role is to assess patient symptoms and determine the urgency level for medical care.
            
            Classify the urgency as:
            - IMMEDIATE: Life-threatening conditions requiring immediate intervention
            - URGENT: Serious conditions requiring prompt attention
            - ROUTINE: Non-urgent conditions that can wait for routine care
            
            Consider factors like symptom severity, duration, patient age, and any alarming signs.
            Provide a brief explanation for your classification."""),
            HumanMessage(content="Patient presents with: {chief_complaint}\nSymptoms: {symptoms}\nDuration: {duration}\nSeverity: {severity}\n\nClassify the urgency and provide explanation:")
        ])
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute triage assessment based on patient symptoms.
        """
        try:
            # Extract input data
            chief_complaint = input_data.get("chief_complaint", "")
            symptoms = input_data.get("symptoms", "")
            duration = input_data.get("duration", "")
            severity = input_data.get("severity", "Moderate")
            
            # Use symptom analyzer for initial assessment
            symptom_analysis = await self.symptom_analyzer.run({
                "symptoms": symptoms,
                "chief_complaint": chief_complaint
            })
            
            # Prepare the prompt with input data
            messages = self.prompt.format_messages(
                chief_complaint=chief_complaint,
                symptoms=symptoms,
                duration=duration,
                severity=severity
            )
            
            # Get LLM response
            response = await self.llm.ainvoke(messages)
            
            # Parse the response
            triage_result = self._parse_triage_response(response.content)
            
            # Enhance with symptom analysis
            triage_result["symptom_analysis"] = symptom_analysis
            triage_result["confidence"] = self._calculate_confidence(triage_result)
            
            # Log the assessment
            self.logger.info(f"Triage assessment completed: {triage_result['urgency_level']}")
            
            return triage_result
            
        except Exception as e:
            self.logger.error(f"Error in triage assessment: {str(e)}")
            return {
                "urgency_level": "UNDETERMINED",
                "explanation": f"Error processing triage: {str(e)}",
                "confidence": 0.0,
                "next_steps": ["Refer to human medical professional immediately"]
            }
    
    def _parse_triage_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the LLM response to extract triage information.
        """
        # Simple parsing - in a real implementation, this would be more sophisticated
        response_lower = response_text.lower()
        
        if "immediate" in response_lower or "emergency" in response_lower or "life-threatening" in response_lower:
            urgency_level = "IMMEDIATE"
        elif "urgent" in response_lower or "serious" in response_lower or "prompt" in response_lower:
            urgency_level = "URGENT"
        else:
            urgency_level = "ROUTINE"
        
        return {
            "urgency_level": urgency_level,
            "explanation": response_text,
            "next_steps": self._get_next_steps(urgency_level)
        }
    
    def _get_next_steps(self, urgency_level: str) -> List[str]:
        """
        Get appropriate next steps based on urgency level.
        """
        next_steps_map = {
            "IMMEDIATE": [
                "Call emergency services immediately",
                "Prepare for emergency intervention",
                "Monitor vital signs continuously"
            ],
            "URGENT": [
                "Seek medical attention within 2 hours",
                "Avoid physical activity",
                "Monitor for worsening symptoms"
            ],
            "ROUTINE": [
                "Schedule routine medical appointment",
                "Monitor symptoms over next few days",
                "Consider over-the-counter remedies if appropriate"
            ]
        }
        
        return next_steps_map.get(urgency_level, ["Seek medical attention"])
    
    def _calculate_confidence(self, triage_result: Dict[str, Any]) -> float:
        """
        Calculate confidence score for the triage assessment.
        """
        # In a real implementation, this would analyze various factors
        # like symptom clarity, available data, etc.
        explanation = triage_result.get("explanation", "")
        
        # Simple confidence calculation based on explanation length and keywords
        if len(explanation) > 100:
            return 0.8
        elif len(explanation) > 50:
            return 0.6
        else:
            return 0.4
    
    async def get_parallel_assessment(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform parallel assessment using multiple approaches.
        """
        # Run multiple assessment approaches in parallel
        symptom_analysis_task = self.symptom_analyzer.run({
            "symptoms": input_data.get("symptoms", ""),
            "chief_complaint": input_data.get("chief_complaint", "")
        })
        
        # Run Google search for similar cases
        search_task = self.google_search.run({
            "query": f"medical triage {input_data.get('chief_complaint', '')} {input_data.get('symptoms', '')}"
        })
        
        # Execute tasks in parallel
        symptom_analysis, search_results = await asyncio.gather(
            symptom_analysis_task,
            search_task,
            return_exceptions=True
        )
        
        # Combine results
        combined_result = await self.execute(input_data)
        combined_result["parallel_analysis"] = {
            "symptom_analysis": symptom_analysis if not isinstance(symptom_analysis, Exception) else str(symptom_analysis),
            "search_results": search_results if not isinstance(search_results, Exception) else str(search_results)
        }
        
        return combined_result