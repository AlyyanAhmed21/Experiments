"""
Chat Agent for handling casual conversation with adaptive personality.
"""
from typing import Optional, Dict, Any

from agents.base_agent import BaseAgent
from llm.prompts import CHAT_AGENT_PROMPT
from database.db_manager import DatabaseManager


class ChatAgent(BaseAgent):
    """Agent for casual conversation."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize Chat Agent."""
        super().__init__(
            agent_name="chat",
            system_prompt=CHAT_AGENT_PROMPT,
            db_manager=db_manager
        )
    
    def process(
        self,
        user_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process a chat message.
        
        Args:
            user_id: User ID
            message: User message
            context: Optional context
            
        Returns:
            Chat response
        """
        # Create response using base class method
        response = self.create_response(user_id, message)
        
        # Save conversation
        self.db_manager.add_conversation(
            user_id=user_id,
            agent_type=self.agent_name,
            message=message,
            response=response
        )
        
        return response

    def process_stream(
        self,
        user_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Process a chat message and stream the response.
        
        Args:
            user_id: User ID
            message: User message
            context: Optional context
            
        Yields:
            Response chunks
        """
        # Stream response using base class method
        full_response = ""
        for chunk in self.create_response_stream(user_id, message):
            full_response += chunk
            yield chunk
        
        # Save conversation
        self.db_manager.add_conversation(
            user_id=user_id,
            agent_type=self.agent_name,
            message=message,
            response=full_response
        )
