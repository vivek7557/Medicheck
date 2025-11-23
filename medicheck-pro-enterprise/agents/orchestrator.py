import asyncio
from typing import Dict, Any, List
from agents.triage_agent import TriageAgent
from agents.diagnosis_agent import DiagnosisAgent
from agents.treatment_agent import TreatmentAgent
from agents.research_agent import ResearchAgent
from agents.specialist_router_agent import SpecialistRouterAgent
from memory.session_service import SessionService
from observability.logger import Logger
from protocols.a2a_protocol import A2AMessage, A2AMessageType
from protocols.message_bus import MessageBus


class MedicalOrchestrator:
    """
    Multi-agent orchestrator that coordinates the workflow between different medical agents.
    Manages the flow of information between agents and handles complex medical workflows.
    """
    
    def __init__(self):
        self.logger = Logger("MedicalOrchestrator")
        self.session_service = SessionService()
        self.message_bus = MessageBus()
        
        # Initialize all agents
        self.triage_agent = TriageAgent()
        self.diagnosis_agent = DiagnosisAgent()
        self.treatment_agent = TreatmentAgent()
        self.research_agent = ResearchAgent()
        self.specialist_router_agent = SpecialistRouterAgent()
        
        # Keep track of active sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def run_triage(self, patient_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the triage agent with the provided patient information.
        """
        self.logger.info("Starting triage assessment")
        
        # Create a new session
        session_id = await self.session_service.create_session({
            "phase": "triage",
            "patient_info": patient_info
        })
        
        # Run triage with parallel assessment
        result = await self.triage_agent.get_parallel_assessment(patient_info)
        
        # Store in session
        await self.session_service.update_session(session_id, {
            "triage_result": result,
            "current_phase": "triage_completed"
        })
        
        self.logger.info(f"Triage assessment completed with urgency: {result.get('urgency_level', 'Unknown')}")
        return result
    
    async def run_diagnosis(self, patient_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the diagnosis agent with the provided patient information.
        """
        self.logger.info("Starting diagnosis process")
        
        # Create a new session or continue existing
        session_id = patient_info.get("session_id") or await self.session_service.create_session({
            "phase": "diagnosis",
            "patient_info": patient_info
        })
        
        # Run diagnosis with sequential refinement
        result = await self.diagnosis_agent.sequential_diagnosis(patient_info)
        
        # Store in session
        await self.session_service.update_session(session_id, {
            "diagnosis_result": result,
            "current_phase": "diagnosis_completed"
        })
        
        self.logger.info(f"Diagnosis completed: {result.get('primary_diagnosis', 'Unknown')}")
        return result
    
    async def run_treatment(self, patient_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the treatment agent with the provided patient information.
        """
        self.logger.info("Starting treatment recommendation process")
        
        # Create a new session or continue existing
        session_id = patient_info.get("session_id") or await self.session_service.create_session({
            "phase": "treatment",
            "patient_info": patient_info
        })
        
        # Run treatment with iterative refinement
        result = await self.treatment_agent.loop_treatment_recommendation(patient_info)
        
        # Store in session
        await self.session_service.update_session(session_id, {
            "treatment_result": result,
            "current_phase": "treatment_completed"
        })
        
        self.logger.info(f"Treatment recommendations generated")
        return result
    
    async def run_research(self, query: str, keywords: str = "") -> Dict[str, Any]:
        """
        Run the research agent with the provided query and keywords.
        """
        self.logger.info(f"Starting research for query: {query}")
        
        # Create a new session
        session_id = await self.session_service.create_session({
            "phase": "research",
            "query": query,
            "keywords": keywords
        })
        
        # Prepare input for research agent
        research_input = {
            "query": query,
            "keywords": keywords,
            "patient_context": ""  # Could be populated from session context
        }
        
        # Run research with long-running capability
        result = await self.research_agent.execute(research_input)
        
        # Store in session
        await self.session_service.update_session(session_id, {
            "research_result": result,
            "current_phase": "research_completed"
        })
        
        self.logger.info(f"Research completed for query: {query}")
        return result
    
    async def route_to_specialist(self, patient_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the specialist router agent with the provided patient information.
        """
        self.logger.info("Starting specialist routing process")
        
        # Create a new session or continue existing
        session_id = patient_info.get("session_id") or await self.session_service.create_session({
            "phase": "specialist_routing",
            "patient_info": patient_info
        })
        
        # Run routing with consultation from other agents
        result = await self.specialist_router_agent.route_with_consultation(patient_info)
        
        # Store in session
        await self.session_service.update_session(session_id, {
            "specialist_routing_result": result,
            "current_phase": "specialist_routing_completed"
        })
        
        self.logger.info(f"Specialist routing completed: {result.get('recommended_specialist', 'Unknown')}")
        return result
    
    async def run_complete_workflow(self, patient_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the complete multi-agent workflow: triage -> diagnosis -> treatment -> specialist routing.
        """
        self.logger.info("Starting complete medical workflow")
        
        workflow_results = {}
        
        try:
            # Step 1: Triage
            triage_result = await self.run_triage(patient_info)
            workflow_results["triage"] = triage_result
            
            # Step 2: Diagnosis (only if triage indicates it's appropriate)
            if triage_result.get("urgency_level") in ["ROUTINE", "URGENT"]:
                diagnosis_input = {**patient_info, **triage_result}
                diagnosis_result = await self.run_diagnosis(diagnosis_input)
                workflow_results["diagnosis"] = diagnosis_result
            else:
                # For immediate cases, may skip to emergency treatment
                workflow_results["diagnosis"] = {"skipped": True, "reason": "Immediate attention required"}
            
            # Step 3: Treatment (if diagnosis was performed)
            if "diagnosis" in workflow_results and not workflow_results["diagnosis"].get("skipped"):
                treatment_input = {**patient_info, **workflow_results["diagnosis"]}
                treatment_result = await self.run_treatment(treatment_input)
                workflow_results["treatment"] = treatment_result
            else:
                # For immediate cases or when diagnosis was skipped
                treatment_input = {**patient_info, "diagnosis": "EMERGENCY"}
                treatment_result = await self.run_treatment(treatment_input)
                workflow_results["treatment"] = treatment_result
            
            # Step 4: Specialist routing (if appropriate)
            if workflow_results["treatment"].get("needs_specialist", True):
                routing_input = {**patient_info, **workflow_results["treatment"]}
                routing_result = await self.route_to_specialist(routing_input)
                workflow_results["specialist_routing"] = routing_result
            
            self.logger.info("Complete workflow finished")
            return workflow_results
            
        except Exception as e:
            self.logger.error(f"Error in complete workflow: {str(e)}")
            return {"error": str(e), "workflow_results": workflow_results}
    
    async def run_parallel_agents(self, patient_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run multiple agents in parallel to get comprehensive assessment.
        """
        self.logger.info("Starting parallel agent assessment")
        
        # Run all agents in parallel
        triage_task = self.triage_agent.get_parallel_assessment(patient_info)
        diagnosis_task = self.diagnosis_agent.execute(patient_info)
        research_task = self.research_agent.execute({
            "query": f"condition related to {patient_info.get('symptoms', '')}",
            "keywords": patient_info.get("chief_complaint", "")
        })
        
        # Execute tasks in parallel
        triage_result, diagnosis_result, research_result = await asyncio.gather(
            triage_task,
            diagnosis_task,
            research_task,
            return_exceptions=True
        )
        
        parallel_results = {
            "triage": triage_result if not isinstance(triage_result, Exception) else str(triage_result),
            "diagnosis": diagnosis_result if not isinstance(diagnosis_result, Exception) else str(diagnosis_result),
            "research": research_result if not isinstance(research_result, Exception) else str(research_result)
        }
        
        # Combine results using the LLM
        combined_result = await self._combine_parallel_results(parallel_results, patient_info)
        
        self.logger.info("Parallel agent assessment completed")
        return combined_result
    
    async def _combine_parallel_results(self, parallel_results: Dict[str, Any], patient_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to combine results from parallel agents into a coherent assessment.
        """
        from langchain_openai import ChatOpenAI
        from langchain.prompts import ChatPromptTemplate
        from langchain.schema import HumanMessage, SystemMessage
        
        llm = ChatOpenAI(model="gpt-4", temperature=0.1)
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert medical coordinator. Synthesize information from multiple medical agents to provide a comprehensive patient assessment.
            
            Consider:
            - Triage urgency level and recommendations
            - Diagnostic possibilities and confidence
            - Treatment recommendations
            - Research findings
            - Any contradictions or complementary findings
            
            Provide a unified assessment with clear next steps."""),
            HumanMessage(content=f"""Parallel Agent Results:
Triage: {parallel_results.get('triage', {})}
Diagnosis: {parallel_results.get('diagnosis', {})}
Research: {parallel_results.get('research', {})}

Patient Info: {patient_info}

Provide unified medical assessment:""")
        ])
        
        messages = prompt.format_messages()
        response = await llm.ainvoke(messages)
        
        return {
            "unified_assessment": response.content,
            "parallel_results": parallel_results,
            "next_steps": self._extract_next_steps(response.content)
        }
    
    def _extract_next_steps(self, assessment: str) -> List[str]:
        """
        Extract next steps from the unified assessment.
        """
        # In a real implementation, this would use more sophisticated NLP
        return ["Follow up with primary care physician", "Schedule follow-up appointment"]
    
    async def pause_workflow(self, session_id: str):
        """
        Pause a running workflow.
        """
        self.logger.info(f"Pausing workflow for session: {session_id}")
        
        # In a real implementation, this would store the current state
        # and allow resumption later
        session = await self.session_service.get_session(session_id)
        await self.session_service.update_session(session_id, {
            **session,
            "workflow_status": "paused"
        })
    
    async def resume_workflow(self, session_id: str):
        """
        Resume a paused workflow.
        """
        self.logger.info(f"Resuming workflow for session: {session_id}")
        
        # In a real implementation, this would restore the state
        # and continue from where it left off
        session = await self.session_service.get_session(session_id)
        await self.session_service.update_session(session_id, {
            **session,
            "workflow_status": "running"
        })
    
    async def communicate_between_agents(self, sender_agent: str, target_agent: str, message_content: Dict[str, Any]):
        """
        Facilitate communication between agents using the A2A protocol.
        """
        message = A2AMessage(
            message_type=A2AMessageType.REQUEST,
            sender_id=sender_agent,
            target_id=target_agent,
            content=message_content,
            timestamp=None
        )
        
        response = await self.message_bus.send_message(target_agent, message)
        return response