"""
LLM client for interacting with Groq API.
Provides unified interface for all agent LLM calls with LangSmith tracking.
"""
from typing import Optional, List, Dict, Any, Generator
import json
import os
from groq import Groq
from config import config

# Set up LangSmith environment variables
if config.LANGSMITH_TRACING and config.LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = config.LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = config.LANGSMITH_PROJECT
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"


class LLMClient:
    """Client for Groq API with streaming support and LangSmith tracking."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM client.
        
        Args:
            api_key: Groq API key (uses config if not provided)
        """
        self.api_key = api_key or config.GROQ_API_KEY
        if not self.api_key:
            raise ValueError("Groq API key is required")
        
        self.client = Groq(api_key=self.api_key)
        self.default_model = config.DEFAULT_MODEL
        self.temperature = config.TEMPERATURE
        self.max_tokens = config.MAX_TOKENS
        
        # Try to import langsmith for tracing
        self.langsmith_available = False
        try:
            from langsmith import traceable
            self.traceable = traceable
            self.langsmith_available = config.LANGSMITH_TRACING
            if self.langsmith_available:
                print("✅ LangSmith tracing enabled")
        except ImportError:
            print("⚠️ LangSmith not available - install with: pip install langsmith")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        run_name: Optional[str] = None
    ) -> Any:
        """
        Generate chat completion with LangSmith tracking.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use (defaults to config)
            temperature: Temperature for generation (defaults to config)
            max_tokens: Max tokens to generate (defaults to config)
            stream: Whether to stream the response
            run_name: Optional name for LangSmith run
            
        Returns:
            Completion response or generator if streaming
        """
        model_to_use = model or self.default_model
        
        # Wrap with LangSmith tracing if available
        if self.langsmith_available:
            return self._traced_completion(
                messages, model_to_use, temperature, max_tokens, stream, run_name
            )
        else:
            return self._raw_completion(
                messages, model_to_use, temperature, max_tokens, stream
            )
    
    def _traced_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: Optional[float],
        max_tokens: Optional[int],
        stream: bool,
        run_name: Optional[str]
    ) -> Any:
        """Completion with LangSmith tracing."""
        @self.traceable(
            name=run_name or f"groq_{model}",
            run_type="llm",
            metadata={
                "model": model,
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
                "stream": stream
            }
        )
        def traced_call():
            return self._raw_completion(messages, model, temperature, max_tokens, stream)
        
        return traced_call()
    
    def _raw_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: Optional[float],
        max_tokens: Optional[int],
        stream: bool
    ) -> Any:
        """Raw Groq API call without tracing."""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stream=stream
            )
            
            return response
            
        except Exception as e:
            print(f"Error in chat completion: {e}")
            raise
    
    def get_completion_text(
        self,
        messages: List[Dict[str, str]],
        run_name: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Get completion text (non-streaming) with LangSmith tracking.
        
        Args:
            messages: List of message dictionaries
            run_name: Optional name for LangSmith run
            **kwargs: Additional arguments for chat_completion
            
        Returns:
            Completion text
        """
        response = self.chat_completion(
            messages, 
            stream=False, 
            run_name=run_name,
            **kwargs
        )
        return response.choices[0].message.content
    
    def stream_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Stream completion text.
        
        Args:
            messages: List of message dictionaries
            **kwargs: Additional arguments for chat_completion
            
        Yields:
            Completion text chunks
        """
        response = self.chat_completion(messages, stream=True, **kwargs)
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def create_messages(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """
        Create message list for chat completion.
        
        Args:
            system_prompt: System prompt for the agent
            user_message: Current user message
            context: Optional context to include
            conversation_history: Optional previous messages
            
        Returns:
            List of message dictionaries
        """
        messages = []
        
        # Add system prompt with context if provided
        system_content = system_prompt
        if context:
            system_content += f"\n\nUser Context:\n{context}"
        
        messages.append({
            "role": "system",
            "content": system_content
        })
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    def parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from LLM response.
        
        Args:
            response: LLM response text
            
        Returns:
            Parsed JSON dictionary or None if parsing fails
        """
        try:
            # Try to find JSON in the response
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            
            return None
        except json.JSONDecodeError:
            return None


# Create a singleton instance
llm_client = LLMClient()

