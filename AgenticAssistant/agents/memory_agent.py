"""
Memory Agent for managing user context and preferences.
"""
from typing import Optional, Dict, Any, List

from agents.base_agent import BaseAgent
from llm.prompts import MEMORY_AGENT_PROMPT
from database.db_manager import DatabaseManager


class MemoryAgent(BaseAgent):
    """Agent for memory management."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize Memory Agent."""
        super().__init__(
            agent_name="memory",
            system_prompt=MEMORY_AGENT_PROMPT,
            db_manager=db_manager
        )
    
    def process(
        self,
        user_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process a memory-related request.
        
        Args:
            user_id: User ID
            message: User message
            context: Optional context
            
        Returns:
            Memory response
        """
        # Get all memories
        memories = self.db_manager.get_all_memories(user_id)
        
        # Format memories for response
        if memories:
            memory_list = "\n".join([f"- {m.key}: {m.value}" for m in memories[:20]])
            response = f"Here's what I remember about you:\n\n{memory_list}"
        else:
            response = "I don't have any stored memories about you yet. As we interact more, I'll learn your preferences!"
        
        # Save conversation
        self.db_manager.add_conversation(
            user_id=user_id,
            agent_type=self.agent_name,
            message=message,
            response=response
        )
        
        return response
    
    def extract_and_store_memories(
        self,
        user_id: int,
        conversation: str
    ) -> List[Dict[str, str]]:
        """
        Extract memories from a conversation and store them.
        
        Args:
            user_id: User ID
            conversation: Conversation text
            
        Returns:
            List of extracted memories
        """
        # Use LLM to extract memories
        extraction_prompt = f"""Analyze this conversation and extract any important user preferences, 
        facts, or patterns that should be remembered.

Conversation: "{conversation}"

Provide a JSON array of memories:
[
    {{"key": "preference_name", "value": "preference_value", "context": "why this matters"}},
    ...
]

Only extract genuinely useful information. Return empty array if nothing notable."""
        
        try:
            response = self.create_response(user_id, extraction_prompt)
            memories_data = self.llm_client.parse_json_response(response)
            
            if not memories_data:
                return []
            
            # Handle both dict and list responses
            if isinstance(memories_data, dict):
                memories_data = [memories_data]
            
            # Store extracted memories
            stored_memories = []
            for memory_data in memories_data:
                if isinstance(memory_data, dict) and 'key' in memory_data and 'value' in memory_data:
                    self.db_manager.set_memory(
                        user_id=user_id,
                        key=memory_data['key'],
                        value=memory_data['value'],
                        context=memory_data.get('context')
                    )
                    stored_memories.append(memory_data)
            
            return stored_memories
        
        except Exception as e:
            print(f"Error extracting memories: {e}")
            return []
    
    def get_relevant_context(
        self,
        user_id: int,
        query: str
    ) -> str:
        """
        Get relevant context for a query.
        
        Args:
            user_id: User ID
            query: Query to find context for
            
        Returns:
            Relevant context string
        """
        # Get all memories
        memories = self.db_manager.get_all_memories(user_id)
        
        # Get recent conversations
        conversations = self.db_manager.get_conversation_history(user_id, limit=10)
        
        # Format context
        context_parts = []
        
        if memories:
            context_parts.append("User Information:")
            for memory in memories[:15]:
                context_parts.append(f"- {memory.key}: {memory.value}")
        
        if conversations:
            context_parts.append("\nRecent Interactions:")
            for conv in conversations[-5:]:
                context_parts.append(f"User: {conv.message}")
                context_parts.append(f"Assistant ({conv.agent_type}): {conv.response[:100]}...")
        
        return "\n".join(context_parts) if context_parts else ""
