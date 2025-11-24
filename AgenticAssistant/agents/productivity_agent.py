"""
Productivity Agent for task management and prioritization.
"""
from typing import Optional, Dict, Any
import re
from datetime import datetime, timedelta

from agents.base_agent import BaseAgent
from llm.prompts import PRODUCTIVITY_AGENT_PROMPT
from database.db_manager import DatabaseManager


class ProductivityAgent(BaseAgent):
    """Agent for productivity and task management."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize Productivity Agent."""
        super().__init__(
            agent_name="productivity",
            system_prompt=PRODUCTIVITY_AGENT_PROMPT,
            db_manager=db_manager
        )
    
    def process(
        self,
        user_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process a productivity-related message.
        
        Args:
            user_id: User ID
            message: User message
            context: Optional context
            
        Returns:
            Productivity response
        """
        # Check if this is a task creation request
        if self._is_task_creation(message):
            return self._handle_task_creation(user_id, message)
        
        # Check if this is a task query
        elif self._is_task_query(message):
            return self._handle_task_query(user_id, message)
        
        # General productivity advice
        else:
            return self._handle_general_productivity(user_id, message)
    
    def _is_task_creation(self, message: str) -> bool:
        """Check if message is requesting task creation."""
        keywords = ['create task', 'add task', 'new task', 'remind me', 'todo', 'need to']
        return any(keyword in message.lower() for keyword in keywords)
    
    def _is_task_query(self, message: str) -> bool:
        """Check if message is querying tasks."""
        keywords = ['my tasks', 'show tasks', 'list tasks', 'what do i need', 'what should i']
        return any(keyword in message.lower() for keyword in keywords)
    
    def _handle_task_creation(self, user_id: int, message: str) -> str:
        """Handle task creation."""
        # Get task details from LLM
        extraction_prompt = f"""Extract task details from this message: "{message}"

Provide a JSON response with:
{{
    "title": "task title",
    "description": "optional description",
    "priority": "low|medium|high",
    "due_date": "YYYY-MM-DD or null"
}}"""
        
        response = self.create_response(user_id, extraction_prompt)
        task_data = self.llm_client.parse_json_response(response)
        
        if task_data:
            # Create task in database
            task = self.db_manager.create_task(
                user_id=user_id,
                title=task_data.get('title', 'New Task'),
                description=task_data.get('description'),
                priority=task_data.get('priority', 'medium'),
                due_date=task_data.get('due_date')
            )
            
            # Save conversation
            response_text = f"✅ Task created: **{task.title}**\n"
            response_text += f"Priority: {task.priority.upper()}\n"
            if task.due_date:
                response_text += f"Due: {task.due_date}\n"
            response_text += f"\nI've added this to your task list!"
        else:
            # Fallback: create simple task
            task = self.db_manager.create_task(
                user_id=user_id,
                title=message[:100],
                priority='medium'
            )
            response_text = f"✅ Task created: **{task.title}**"
        
        # Save conversation
        self.db_manager.add_conversation(
            user_id=user_id,
            agent_type=self.agent_name,
            message=message,
            response=response_text
        )
        
        return response_text
    
    def _handle_task_query(self, user_id: int, message: str) -> str:
        """Handle task queries."""
        # Get pending tasks
        tasks = self.db_manager.get_tasks(user_id, status='pending')
        
        if not tasks:
            response = "You don't have any pending tasks. Great job! 🎉"
        else:
            response = f"📋 You have **{len(tasks)}** pending tasks:\n\n"
            
            # Sort by priority
            priority_order = {'high': 0, 'medium': 1, 'low': 2}
            sorted_tasks = sorted(tasks, key=lambda t: priority_order.get(t.priority, 1))
            
            for i, task in enumerate(sorted_tasks[:10], 1):
                priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
                emoji = priority_emoji.get(task.priority, '⚪')
                response += f"{i}. {emoji} **{task.title}**"
                if task.due_date:
                    response += f" (Due: {task.due_date})"
                response += "\n"
        
        # Save conversation
        self.db_manager.add_conversation(
            user_id=user_id,
            agent_type=self.agent_name,
            message=message,
            response=response
        )
        
        return response
    
    def _handle_general_productivity(self, user_id: int, message: str) -> str:
        """Handle general productivity questions."""
        # Get current tasks for context
        tasks = self.db_manager.get_tasks(user_id, status='pending')
        task_context = f"\nUser currently has {len(tasks)} pending tasks."
        
        response = self.create_response(user_id, message, additional_context=task_context)
        
        # Save conversation
        self.db_manager.add_conversation(
            user_id=user_id,
            agent_type=self.agent_name,
            message=message,
            response=response
        )
        
        return response
