from typing import Dict, Any
import asyncio
import requests
from app.config import get_config


class GoogleSearchTool:
    """
    Built-in tool for performing Google searches.
    Uses Google Custom Search API to search for medical information.
    """
    
    def __init__(self):
        self.config = get_config()
        self.api_key = self.config.google_api_key
        self.search_engine_id = "medical-search-engine-id"  # Would be configured in a real implementation
        self.base_url = "https://www.googleapis.com/customsearch/v1"
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a Google search with the provided query.
        """
        query = input_data.get("query", "")
        max_results = input_data.get("max_results", 5)
        
        if not self.api_key:
            return {
                "error": "Google API key not configured",
                "results": []
            }
        
        try:
            # Make the API request
            params = {
                "key": self.api_key,
                "q": query,
                "num": max_results,
                "cx": self.search_engine_id  # Search engine ID
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Process the results
            results = []
            if "items" in data:
                for item in data["items"]:
                    result = {
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "displayLink": item.get("displayLink", "")
                    }
                    results.append(result)
            
            return {
                "query": query,
                "results": results,
                "total_results": len(results)
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Search request failed: {str(e)}",
                "results": []
            }
        except Exception as e:
            return {
                "error": f"Search failed: {str(e)}",
                "results": []
            }
    
    async def search_medical_literature(self, query: str) -> Dict[str, Any]:
        """
        Perform a search specifically for medical literature.
        """
        medical_query = f"medical literature {query}"
        return await self.run({
            "query": medical_query,
            "max_results": 10
        })
    
    async def search_clinical_guidelines(self, condition: str) -> Dict[str, Any]:
        """
        Search for clinical guidelines related to a specific condition.
        """
        guideline_query = f"clinical guidelines {condition} treatment"
        return await self.run({
            "query": guideline_query,
            "max_results": 8
        })