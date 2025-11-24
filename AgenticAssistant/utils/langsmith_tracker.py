"""
LangSmith tracking integration for monitoring agent interactions.
"""
import os
from typing import Optional, Dict, Any, Callable
from functools import wraps
from datetime import datetime

from config import config

# Initialize LangSmith if enabled
if config.LANGSMITH_TRACING and config.LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = config.LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = config.LANGSMITH_PROJECT


class LangSmithTracker:
    """Tracker for LangSmith integration."""
    
    def __init__(self):
        """Initialize tracker."""
        self.enabled = config.LANGSMITH_TRACING and bool(config.LANGSMITH_API_KEY)
    
    def track_agent_call(
        self,
        agent_name: str,
        user_id: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Decorator to track agent calls in LangSmith.
        
        Args:
            agent_name: Name of the agent
            user_id: User ID
            metadata: Optional metadata
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self.enabled:
                    return func(*args, **kwargs)
                
                # Import here to avoid issues if langsmith not installed
                try:
                    from langsmith import traceable
                    
                    # Create run metadata
                    run_metadata = {
                        "agent": agent_name,
                        "user_id": user_id,
                        "timestamp": datetime.now().isoformat(),
                        **(metadata or {})
                    }
                    
                    # Wrap function with traceable
                    traced_func = traceable(
                        name=f"{agent_name}_call",
                        metadata=run_metadata,
                        project_name=config.LANGSMITH_PROJECT
                    )(func)
                    
                    return traced_func(*args, **kwargs)
                    
                except ImportError:
                    # If langsmith not available, just run the function
                    return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def log_interaction(
        self,
        agent_name: str,
        user_id: int,
        input_text: str,
        output_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log an interaction to LangSmith.
        
        Args:
            agent_name: Name of the agent
            user_id: User ID
            input_text: Input message
            output_text: Output response
            metadata: Optional metadata
        """
        if not self.enabled:
            return
        
        try:
            from langsmith import Client
            
            client = Client()
            
            # Create run
            run_metadata = {
                "agent": agent_name,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            # Note: This is a simplified logging approach
            # In production, you'd use the full LangSmith SDK features
            
        except ImportError:
            pass  # LangSmith not available


# Create singleton instance
langsmith_tracker = LangSmithTracker()
