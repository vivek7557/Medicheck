from typing import Dict, Any, List
import asyncio
from agents.base_agent import BaseAgent
from tools.builtin_tools.google_search import GoogleSearchTool
from tools.builtin_tools.pubmed_search import PubMedSearchTool
from tools.mcp_tools.medical_database import MedicalDatabaseMCP
from tools.openapi_tools.fhir_api import FHIROpenAPITool
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage


class ResearchAgent(BaseAgent):
    """
    Research Agent for medical literature research and evidence gathering.
    Uses LLM to search and synthesize medical literature and research.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="research_agent",
            name="Research Agent",
            description="Medical literature research and evidence gathering"
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            max_tokens=2500
        )
        
        # Initialize tools
        self.google_search = GoogleSearchTool()
        self.pubmed_search = PubMedSearchTool()
        self.medical_database = MedicalDatabaseMCP()
        self.fhir_api = FHIROpenAPITool()
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert medical researcher. Synthesize information from medical literature to answer clinical questions and provide evidence-based insights.
            
            Consider:
            - Latest research findings
            - Clinical trial results
            - Evidence quality and study design
            - Relevance to the clinical question
            - Potential biases in the literature
            
            Provide:
            1. Summary of key findings
            2. Quality assessment of evidence
            3. Clinical implications
            4. Recommendations based on evidence
            5. Limitations of current research"""),
            HumanMessage(content="""Research Query: {query}
Keywords: {keywords}
Patient Context: {patient_context}

Conduct comprehensive medical literature research and provide evidence-based summary:""")
        ])
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute medical literature research based on query.
        """
        try:
            # Extract input data
            query = input_data.get("query", "")
            keywords = input_data.get("keywords", "")
            patient_context = input_data.get("patient_context", "")
            
            # Perform literature search using multiple tools
            google_results_task = self.google_search.run({
                "query": f"medical research {query} {keywords}"
            })
            
            pubmed_results_task = self.pubmed_search.run({
                "query": f"{query} {keywords}",
                "max_results": 10
            })
            
            # Execute searches in parallel
            google_results, pubmed_results = await asyncio.gather(
                google_results_task,
                pubmed_results_task,
                return_exceptions=True
            )
            
            # Prepare the prompt with input data and search results
            messages = self.prompt.format_messages(
                query=query,
                keywords=keywords,
                patient_context=patient_context
            )
            
            # Get LLM response
            response = await self.llm.ainvoke(messages)
            
            # Parse the response
            research_result = self._parse_research_response(response.content)
            
            # Enhance with search results
            research_result["google_search_results"] = google_results if not isinstance(google_results, Exception) else str(google_results)
            research_result["pubmed_search_results"] = pubmed_results if not isinstance(pubmed_results, Exception) else str(pubmed_results)
            research_result["confidence"] = self._calculate_confidence(research_result)
            
            # Log the research
            self.logger.info(f"Research completed for query: {query}")
            
            return research_result
            
        except Exception as e:
            self.logger.error(f"Error in research: {str(e)}")
            return {
                "key_findings": [],
                "evidence_quality": "UNDETERMINED",
                "clinical_implications": [],
                "recommendations": [],
                "limitations": ["Research could not be completed due to error"],
                "explanation": f"Error processing research: {str(e)}",
                "confidence": 0.0
            }
    
    def _parse_research_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the LLM response to extract research information.
        """
        # This is a simplified parsing - in a real implementation, 
        # this would use more sophisticated NLP techniques
        return {
            "key_findings": ["Key finding 1", "Key finding 2"],
            "evidence_quality": "High/Medium/Low",
            "clinical_implications": ["Clinical implication 1", "Clinical implication 2"],
            "recommendations": ["Recommendation 1", "Recommendation 2"],
            "limitations": ["Limitation 1", "Limitation 2"],
            "explanation": response_text
        }
    
    def _calculate_confidence(self, research_result: Dict[str, Any]) -> float:
        """
        Calculate confidence score for the research findings.
        """
        # In a real implementation, this would analyze various factors
        # like source quality, study design, etc.
        explanation = research_result.get("explanation", "")
        
        # Simple confidence calculation based on explanation length and keywords
        if len(explanation) > 400:
            return 0.9
        elif len(explanation) > 200:
            return 0.75
        else:
            return 0.6
    
    async def long_running_research(self, input_data: Dict[str, Any], pause_callback=None) -> Dict[str, Any]:
        """
        Perform long-running research with pause/resume capability.
        """
        query = input_data.get("query", "")
        keywords = input_data.get("keywords", "")
        
        # Step 1: Initial search
        self.logger.info(f"Starting long-running research for: {query}")
        
        # Perform initial broad search
        initial_results = await self.pubmed_search.run({
            "query": f"{query} {keywords}",
            "max_results": 20
        })
        
        # Allow pausing if callback is provided
        if pause_callback:
            await pause_callback("initial_search_complete", initial_results)
        
        # Step 2: Deep dive into relevant articles
        refined_query = self._generate_refined_query(query, initial_results)
        
        deep_results = await self.pubmed_search.run({
            "query": refined_query,
            "max_results": 30
        })
        
        # Allow pausing if callback is provided
        if pause_callback:
            await pause_callback("deep_search_complete", deep_results)
        
        # Step 3: Synthesize findings
        synthesis_input = {
            "query": query,
            "keywords": keywords,
            "initial_results": initial_results,
            "deep_results": deep_results
        }
        
        final_result = await self.execute(synthesis_input)
        
        return {
            "initial_results": initial_results,
            "deep_results": deep_results,
            "final_synthesis": final_result,
            "process_completed": True
        }
    
    def _generate_refined_query(self, original_query: str, initial_results: Any) -> str:
        """
        Generate a more specific query based on initial results.
        """
        # In a real implementation, this would analyze the initial results
        # and generate a more targeted query
        return f"{original_query} clinical trial meta-analysis"