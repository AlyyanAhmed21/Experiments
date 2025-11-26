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
        self.active_game = None
    
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
        # Load active game state for the user
        game_state = self.db_manager.get_game_state(user_id)
        self.active_game = game_state.get('active_game') if game_state else None
        
        # Determine creative task type
        task_type = self._identify_creative_task(message)
        
        # Update active game state if user explicitly asks for a game
        if task_type in ['word_chain', 'riddle', 'hangman', 'word_game']:
            self.active_game = task_type
        elif task_type in ['poem', 'story', 'summary', 'report', 'brainstorming', 'general_creative']:
            # If user switches to a different creative task, clear game state
            self.active_game = None
            
        # Add task-specific context
        additional_context = f"Creative task type: {task_type}"
        if self.active_game:
            additional_context += f"\nCURRENT ACTIVE GAME: {self.active_game.upper()}. Stick to the rules of this game."
            if game_state and game_state.get('game_data'):
                additional_context += f"\nGAME STATE: {game_state['game_data']}"
        
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
            metadata={'task_type': task_type, 'active_game': self.active_game}
        )
        
        # Persist game state (only active_game)
        self.db_manager.set_game_state(user_id, {'active_game': self.active_game})
        
        return response
        return response
    
    def process_stream(
        self,
        user_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Process a creative content request and stream response.
        
        Args:
            user_id: User ID
            message: User message
            context: Optional context
            
        Yields:
            Response chunks
        """
        # Load active game state for the user
        game_state = self.db_manager.get_game_state(user_id)
        self.active_game = game_state.get('active_game') if game_state else None
        
        # Determine creative task type
        task_type = self._identify_creative_task(message)
        
        # Update active game state based on user intent
        if task_type in ['word_chain', 'riddle', 'hangman', 'word_game']:
            self.active_game = task_type
        elif task_type in ['poem', 'story', 'summary', 'report', 'brainstorming', 'general_creative']:
            # Switching to non‑game creative task clears game state
            self.active_game = None
            
        # Add task‑specific context
        additional_context = f"Creative task type: {task_type}"
        if self.active_game:
            additional_context += f"\nCURRENT ACTIVE GAME: {self.active_game.upper()}. Stick to the rules of this game."
            if game_state and game_state.get('game_data'):
                additional_context += f"\nGAME STATE: {game_state['game_data']}"
        
        # Stream creative content
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
            metadata={'task_type': task_type, 'active_game': self.active_game}
        )
        
        # Persist game state (only active_game)
        self.db_manager.set_game_state(user_id, {'active_game': self.active_game})
    
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
        elif 'word chain' in message_lower:
            return 'word_chain'
        elif 'riddle' in message_lower:
            return 'riddle'
        elif 'hangman' in message_lower:
            return 'hangman'
        elif any(word in message_lower for word in ['game', 'play']):
            return 'word_game'
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
