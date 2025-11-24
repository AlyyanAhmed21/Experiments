"""
Orchestrator for coordinating multiple agents.
Analyzes user input and routes to appropriate agent(s).
"""
from typing import Optional, Dict, Any, List
import json

from agents.base_agent import BaseAgent
from agents.chat_agent import ChatAgent
from agents.productivity_agent import ProductivityAgent
from agents.creative_agent import CreativeAgent
from agents.memory_agent import MemoryAgent
from llm.prompts import ORCHESTRATOR_PROMPT
from llm.llm_client import llm_client
from database.db_manager import DatabaseManager


class Orchestrator:
    """Orchestrates multiple agents to handle user requests."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize orchestrator with all agents.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.llm_client = llm_client
        
        # Initialize all agents
        self.agents = {
            'chat': ChatAgent(db_manager),
            'productivity': ProductivityAgent(db_manager),
            'creative': CreativeAgent(db_manager),
            'memory': MemoryAgent(db_manager)
        }
    
    def process_message(
        self,
        user_id: int,
        message: str
    ) -> Dict[str, Any]:
        """
        Process a user message by routing to appropriate agent(s).
        
        Args:
            user_id: User ID
            message: User message
            
        Returns:
            Dictionary with response and metadata
        """
        # Determine which agent(s) should handle this
        routing_decision = self._route_message(user_id, message)
        
        primary_agent = routing_decision.get('primary_agent', 'chat')
        secondary_agents = routing_decision.get('secondary_agents', [])
        
        # Get response from primary agent
        if primary_agent in self.agents:
            primary_response = self.agents[primary_agent].process(user_id, message)
        else:
            # Fallback to chat agent
            primary_response = self.agents['chat'].process(user_id, message)
            primary_agent = 'chat'
        
        # Optionally get responses from secondary agents
        secondary_responses = {}
        for agent_name in secondary_agents:
            if agent_name in self.agents and agent_name != primary_agent:
                try:
                    secondary_responses[agent_name] = self.agents[agent_name].process(
                        user_id, message
                    )
                except:
                    pass  # Skip if secondary agent fails
        
        # Extract and store memories from this interaction
        self._update_memories(user_id, message, primary_response)
        
        # Prepare response
        result = {
            'response': primary_response,
            'primary_agent': primary_agent,
            'secondary_responses': secondary_responses,
            'routing_reasoning': routing_decision.get('reasoning', '')
        }
        
        return result
    
    def _route_message(
        self,
        user_id: int,
        message: str
    ) -> Dict[str, Any]:
        """
        Determine which agent(s) should handle the message.
        
        Args:
            user_id: User ID
            message: User message
            
        Returns:
            Routing decision dictionary
        """
        # Get user context for better routing
        memory_agent = self.agents['memory']
        context = memory_agent.get_relevant_context(user_id, message)
        
        # Create routing prompt
        routing_prompt = f"""User message: "{message}"

Analyze this message and determine which agent should handle it.

Available agents:
- chat: Casual conversation, greetings, general questions
- productivity: Tasks, reminders, scheduling, time management
- creative: Poems, stories, summaries, brainstorming, creative content
- memory: Retrieving user information, preferences, past conversations

Respond with JSON:
{{
    "primary_agent": "agent_name",
    "secondary_agents": [],
    "reasoning": "brief explanation"
}}"""
        
        # Get routing decision from LLM
        messages = [
            {"role": "system", "content": ORCHESTRATOR_PROMPT},
            {"role": "user", "content": routing_prompt}
        ]
        
        if context:
            messages[0]["content"] += f"\n\nUser Context:\n{context}"
        
        try:
            response = self.llm_client.get_completion_text(messages)
            decision = self.llm_client.parse_json_response(response)
            
            if decision and 'primary_agent' in decision:
                return decision
        except:
            pass
        
        # Fallback: use simple keyword matching
        return self._fallback_routing(message)
    
    def _fallback_routing(self, message: str) -> Dict[str, Any]:
        """Fallback routing using keyword matching."""
        message_lower = message.lower()
        
        # Productivity keywords
        if any(word in message_lower for word in [
            'task', 'todo', 'remind', 'schedule', 'deadline', 'priority'
        ]):
            return {
                'primary_agent': 'productivity',
                'secondary_agents': [],
                'reasoning': 'Keyword match for productivity'
            }
        
        # Creative keywords
        elif any(word in message_lower for word in [
            'poem', 'story', 'write', 'create', 'summary', 'brainstorm', 'ideas'
        ]):
            return {
                'primary_agent': 'creative',
                'secondary_agents': [],
                'reasoning': 'Keyword match for creative'
            }
        
        # Memory keywords
        elif any(word in message_lower for word in [
            'remember', 'what do you know', 'my preferences', 'tell me about me'
        ]):
            return {
                'primary_agent': 'memory',
                'secondary_agents': [],
                'reasoning': 'Keyword match for memory'
            }
        
        # Default to chat
        else:
            return {
                'primary_agent': 'chat',
                'secondary_agents': [],
                'reasoning': 'Default to chat agent'
            }
    
    def _update_memories(
        self,
        user_id: int,
        message: str,
        response: str
    ):
        """
        Extract and update memories from conversation.
        
        Args:
            user_id: User ID
            message: User message
            response: Agent response
        """
        # Combine message and response
        conversation = f"User: {message}\nAssistant: {response}"
        
        # Use memory agent to extract memories
        memory_agent = self.agents['memory']
        
        try:
            memory_agent.extract_and_store_memories(user_id, conversation)
        except:
            pass  # Don't fail if memory extraction fails
