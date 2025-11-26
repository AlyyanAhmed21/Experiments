"""
Base agent class providing common functionality for all agents.
"""
from typing import Optional, List, Dict, Any, Generator
from abc import ABC, abstractmethod

from llm.llm_client import llm_client
from database.db_manager import DatabaseManager
from utils.langsmith_tracker import langsmith_tracker


class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(
        self,
        agent_name: str,
        system_prompt: str,
        db_manager: DatabaseManager
    ):
        """
        Initialize base agent.
        
        Args:
            agent_name: Name of the agent
            system_prompt: System prompt for this agent
            db_manager: Database manager instance
        """
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.db_manager = db_manager
        self.llm_client = llm_client
    
    @abstractmethod
    def process(
        self,
        user_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process a user message.
        
        Args:
            user_id: User ID
            message: User message
            context: Optional context dictionary
            
        Returns:
            Agent response
        """
        pass
    
    def process_stream(
        self,
        user_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Generator[str, None, None]:
        """
        Process a user message and stream the response.
        
        Args:
            user_id: User ID
            message: User message
            context: Optional context dictionary
            
        Yields:
            Response chunks
        """
        # Default implementation uses create_response_stream (to be added)
        # Subclasses can override if they need custom logic
        return self.create_response_stream(user_id, message)
    
    def get_user_context(self, user_id: int) -> str:
        """
        Get formatted user context.
        
        Args:
            user_id: User ID
            
        Returns:
            Formatted context string
        """
        # Get recent conversations
        conversations = self.db_manager.get_conversation_history(user_id, limit=5)
        
        # Get user memories
        memories = self.db_manager.get_all_memories(user_id)
        
        # Format context
        context_parts = []
        
        if memories:
            context_parts.append("User Preferences and Information:")
            for memory in memories[:10]:  # Limit to 10 most recent
                context_parts.append(f"- {memory.key}: {memory.value}")
        
        if conversations:
            context_parts.append("\nRecent Conversation History:")
            # Reverse to show oldest first in the context block
            for i, conv in enumerate(reversed(conversations)):
                context_parts.append(f"User: {conv.message}")
                # Don't truncate the most recent response so the agent remembers what it just said (e.g. a riddle)
                if i == len(conversations) - 1:
                    context_parts.append(f"Assistant: {conv.response}")
                else:
                    context_parts.append(f"Assistant: {conv.response[:200]}...")
        
        return "\n".join(context_parts) if context_parts else "No previous context available."
    
    def create_response(
        self,
        user_id: int,
        message: str,
        additional_context: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Create a response using the LLM.
        
        Args:
            user_id: User ID
            message: User message
            additional_context: Optional additional context
            conversation_history: Optional conversation history
            
        Returns:
            LLM response
        """
        # Get user context
        user_context = self.get_user_context(user_id)
        
        # Combine contexts
        full_context = user_context
        if additional_context:
            full_context += f"\n\n{additional_context}"
        
        # Create messages
        messages = self.llm_client.create_messages(
            system_prompt=self.system_prompt,
            user_message=message,
            context=full_context,
            conversation_history=conversation_history
        )
        
        # Get response
        response = self.llm_client.get_completion_text(messages)
        
        # Log to LangSmith
        langsmith_tracker.log_interaction(
            agent_name=self.agent_name,
            user_id=user_id,
            input_text=message,
            output_text=response
        )
        
        return response

    def create_response_stream(
        self,
        user_id: int,
        message: str,
        additional_context: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Generator[str, None, None]:
        """
        Create a streaming response using the LLM.
        
        Args:
            user_id: User ID
            message: User message
            additional_context: Optional additional context
            conversation_history: Optional conversation history
            
        Yields:
            LLM response chunks
        """
        # Get user context
        user_context = self.get_user_context(user_id)
        
        # Combine contexts
        full_context = user_context
        if additional_context:
            full_context += f"\n\n{additional_context}"
        
        # Create messages
        messages = self.llm_client.create_messages(
            system_prompt=self.system_prompt,
            user_message=message,
            context=full_context,
            conversation_history=conversation_history
        )
        
        # Stream response
        # Note: We can't easily log to LangSmith here without collecting the full response first
        # For now, we'll skip LangSmith logging for streaming or add it later
        return self.llm_client.stream_completion(messages)
