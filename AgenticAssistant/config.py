"""
Configuration management for the Multi-Agent AI Personal Assistant.
Loads environment variables and provides centralized settings.
"""
import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()


class Config:
    """Central configuration class for the application."""
    
    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")  # Optional for voice features
    
    # LangSmith Configuration
    LANGSMITH_PROJECT: str = os.getenv("LANGSMITH_PROJECT", "multi-agent-assistant")
    LANGSMITH_TRACING: bool = os.getenv("LANGSMITH_TRACING", "true").lower() == "true"
    
    # LLM Configuration
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "llama-3.3-70b-versatile")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2048"))
    
    # Database Configuration
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/assistant.db")
    
    # Application Settings
    APP_TITLE: str = "Multi-Agent AI Personal Assistant"
    APP_ICON: str = "🤖"
    
    # Voice Features (Optional)
    ENABLE_VOICE_INPUT: bool = os.getenv("ENABLE_VOICE_INPUT", "false").lower() == "true"
    ENABLE_VOICE_OUTPUT: bool = os.getenv("ENABLE_VOICE_OUTPUT", "false").lower() == "true"
    
    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """
        Validate required configuration.
        
        Returns:
            tuple: (is_valid, list of error messages)
        """
        errors = []
        
        if not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY is required. Get one at https://console.groq.com")
        
        if not cls.LANGSMITH_API_KEY:
            errors.append("LANGSMITH_API_KEY is required. Get one at https://smith.langchain.com")
        
        if cls.ENABLE_VOICE_INPUT or cls.ENABLE_VOICE_OUTPUT:
            if not cls.OPENAI_API_KEY:
                errors.append("OPENAI_API_KEY is required for voice features")
        
        return len(errors) == 0, errors
    
    @classmethod
    def get_available_models(cls) -> list[str]:
        """Get list of available Groq models (November 2024)."""
        return [
            "llama-3.3-70b-versatile",  # Latest, recommended
            "llama-3.1-8b-instant",     # Fastest
            "llama3-70b-8192",          # Large context
            "llama3-8b-8192",           # Fast with context
            "mixtral-8x7b-32768",       # 32k context window
            "gemma2-9b-it",             # Google's model
        ]


# Create a singleton instance
config = Config()
