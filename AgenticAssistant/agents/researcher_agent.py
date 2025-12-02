"""
Researcher Agent for live web search using Serper API.
"""
from typing import Optional, Dict, Any
import requests
import os

from agents.base_agent import BaseAgent
from llm.prompts import RESEARCHER_AGENT_PROMPT
from database.db_manager import DatabaseManager


class ResearcherAgent(BaseAgent):
    """Agent for live web research."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize Researcher Agent."""
        super().__init__(
            agent_name="researcher",
            system_prompt=RESEARCHER_AGENT_PROMPT,
            db_manager=db_manager
        )
        self.serper_api_key = os.getenv("SERPER_API_KEY")
    
    def process(
        self,
        user_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process a research request.
        
        Args:
            user_id: User ID
            message: User message
            context: Optional context
            
        Returns:
            Research response with citations
        """
        # Perform web search
        search_results = self._search_web(message)
        
        # Generate response using LLM with search results
        if search_results:
            search_context = self._format_search_results(search_results)
            additional_context = f"Web Search Results:\n{search_context}"
        else:
            additional_context = "No search results available. Please provide a general answer based on your knowledge."
        
        response = self.create_response(
            user_id,
            message,
            additional_context=additional_context
        )
        
        # Save conversation
        self.db_manager.add_conversation(
            user_id=user_id,
            agent_type=self.agent_name,
            message=message,
            response=response,
            metadata={'search_performed': bool(search_results)}
        )
        
        return response
    
    def process_stream(
        self,
        user_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Process a research request and stream response."""
        # Perform web search
        search_results = self._search_web(message)
        
        # Generate response using LLM with search results
        if search_results:
            search_context = self._format_search_results(search_results)
            additional_context = f"Web Search Results:\n{search_context}"
        else:
            additional_context = "No search results available. Please provide a general answer based on your knowledge."
        
        # Stream response
        full_response = ""
        for chunk in self.create_response_stream(
            user_id,
            message,
            additional_context=additional_context
        ):
            full_response += chunk
            yield chunk
        
        # Save conversation
        self.db_manager.add_conversation(
            user_id=user_id,
            agent_type=self.agent_name,
            message=message,
            response=full_response,
            metadata={'search_performed': bool(search_results)}
        )
    
    def _search_web(self, query: str) -> Optional[Dict[str, Any]]:
        """Perform web search using Serper API."""
        if not self.serper_api_key:
            print("⚠️ SERPER_API_KEY not found. Skipping web search.")
            return None
        
        try:
            url = "https://google.serper.dev/search"
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "q": query,
                "num": 5  # Get top 5 results
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            print(f"Error performing web search: {e}")
            return None
    
    def _format_search_results(self, results: Dict[str, Any]) -> str:
        """Format search results for LLM context."""
        formatted = []
        
        # Add organic results
        if "organic" in results:
            for i, result in enumerate(results["organic"][:5], 1):
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                link = result.get("link", "")
                formatted.append(f"{i}. **{title}**\n   {snippet}\n   Source: {link}")
        
        # Add knowledge graph if available
        if "knowledgeGraph" in results:
            kg = results["knowledgeGraph"]
            title = kg.get("title", "")
            description = kg.get("description", "")
            if title and description:
                formatted.insert(0, f"**Knowledge Graph: {title}**\n{description}\n")
        
        return "\n\n".join(formatted) if formatted else "No results found."
