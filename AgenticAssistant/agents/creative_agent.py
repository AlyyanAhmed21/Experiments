"""
Creative Agent for generating poems, summaries, and creative content.
"""
from typing import Optional, Dict, Any

from agents.base_agent import BaseAgent
from llm.prompts import CREATIVE_AGENT_PROMPT
from database.db_manager import DatabaseManager


class CreativeAgent(BaseAgent):
    """Agent for creative content generation."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize Creative Agent."""
        super().__init__(
            agent_name="creative",
            system_prompt=CREATIVE_AGENT_PROMPT,
            db_manager=db_manager
        )
    
    def process(
        self,
        user_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process a creative content request.
        
        Args:
            user_id: User ID
            message: User message
            context: Optional context
            
        Returns:
            Creative response
        """
        # Determine creative task type
        task_type = self._identify_creative_task(message)
        
        # Add task-specific context
        additional_context = f"Creative task type: {task_type}"
        
        # Generate creative content
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
            metadata={'task_type': task_type}
        )
        
        return response
    
    def _identify_creative_task(self, message: str) -> str:
        """Identify the type of creative task."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['poem', 'poetry', 'verse']):
            return 'poem'
        elif any(word in message_lower for word in ['story', 'tale', 'narrative']):
            return 'story'
        elif any(word in message_lower for word in ['summary', 'summarize', 'tldr']):
            return 'summary'
        elif any(word in message_lower for word in ['report', 'analysis', 'review']):
            return 'report'
        elif any(word in message_lower for word in ['brainstorm', 'ideas', 'suggest']):
            return 'brainstorming'
        else:
            return 'general_creative'
    
    def generate_proactive_suggestion(self, user_id: int) -> Optional[str]:
        """
        Generate a proactive suggestion based on user context.
        
        Args:
            user_id: User ID
            
        Returns:
            Suggestion or None
        """
        # Get user context
        context = self.get_user_context(user_id)
        
        if not context or "No previous context" in context:
            return None
        
        # Generate suggestion
        suggestion_prompt = """Based on the user's recent activity and preferences, 
        generate a brief, helpful suggestion or creative idea they might enjoy. 
        Keep it concise (2-3 sentences) and relevant."""
        
        try:
            suggestion = self.create_response(
                user_id,
                suggestion_prompt,
                additional_context="This is a proactive suggestion."
            )
            return suggestion
        except:
            return None
