from typing import Dict, Any
import asyncio
import requests
from app.config import get_config


class PubMedSearchTool:
    """
    Built-in tool for searching PubMed database.
    Uses PubMed API to search for medical literature and research.
    """
    
    def __init__(self):
        self.config = get_config()
        self.api_key = self.config.pubmed_api_key
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a PubMed search with the provided query.
        """
        query = input_data.get("query", "")
        max_results = input_data.get("max_results", 10)
        
        try:
            # First, search for PubMed IDs
            search_url = f"{self.base_url}/esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "api_key": self.api_key if self.api_key else None
            }
            
            # Remove api_key from params if not set
            if not self.api_key:
                del search_params["api_key"]
            
            search_response = requests.get(search_url, params=search_params)
            search_response.raise_for_status()
            
            search_data = search_response.json()
            pmids = search_data.get("esearchresult", {}).get("idlist", [])
            
            if not pmids:
                return {
                    "query": query,
                    "results": [],
                    "total_results": 0
                }
            
            # Fetch detailed information for each PMID
            fetch_url = f"{self.base_url}/efetch.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",  # We'll handle XML parsing
                "api_key": self.api_key if self.api_key else None
            }
            
            # Remove api_key from params if not set
            if not self.api_key:
                del fetch_params["api_key"]
            
            fetch_response = requests.get(fetch_url, params=fetch_params)
            fetch_response.raise_for_status()
            
            # For simplicity, we'll return the raw XML content
            # In a real implementation, this would be parsed properly
            detailed_results = self._parse_pubmed_xml(fetch_response.text, pmids)
            
            return {
                "query": query,
                "results": detailed_results,
                "total_results": len(detailed_results),
                "pmids": pmids
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "error": f"PubMed search request failed: {str(e)}",
                "results": []
            }
        except Exception as e:
            return {
                "error": f"PubMed search failed: {str(e)}",
                "results": []
            }
    
    def _parse_pubmed_xml(self, xml_content: str, pmids: list) -> list:
        """
        Parse PubMed XML response to extract relevant information.
        In a real implementation, this would use proper XML parsing.
        """
        # This is a simplified implementation
        # In reality, this would use xml.etree.ElementTree or similar
        results = []
        
        # For demonstration purposes, we'll create placeholder results
        for i, pmid in enumerate(pmids):
            results.append({
                "pmid": pmid,
                "title": f"Sample Research Title {i+1}",
                "authors": ["Author1", "Author2"],
                "journal": "Sample Journal",
                "pub_date": "2023",
                "abstract": f"This is a sample abstract for PubMed ID {pmid}. In a real implementation, this would contain the actual abstract from the research paper.",
                "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            })
        
        return results
    
    async def search_systematic_reviews(self, condition: str) -> Dict[str, Any]:
        """
        Search for systematic reviews and meta-analyses.
        """
        review_query = f"{condition} systematic review meta-analysis"
        return await self.run({
            "query": review_query,
            "max_results": 10
        })
    
    async def search_clinical_trials(self, intervention: str) -> Dict[str, Any]:
        """
        Search for clinical trials related to a specific intervention.
        """
        trial_query = f"{intervention} clinical trial"
        return await self.run({
            "query": trial_query,
            "max_results": 15
        })
    
    async def get_article_details(self, pmid: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific PubMed article.
        """
        return await self.run({
            "query": f"PMID:{pmid}",
            "max_results": 1
        })