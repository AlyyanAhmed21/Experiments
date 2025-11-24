"""LLM package initialization."""
from llm.llm_client import LLMClient, llm_client
from llm.prompts import (
    ORCHESTRATOR_PROMPT,
    CHAT_AGENT_PROMPT,
    PRODUCTIVITY_AGENT_PROMPT,
    CREATIVE_AGENT_PROMPT,
    MEMORY_AGENT_PROMPT
)

__all__ = [
    'LLMClient',
    'llm_client',
    'ORCHESTRATOR_PROMPT',
    'CHAT_AGENT_PROMPT',
    'PRODUCTIVITY_AGENT_PROMPT',
    'CREATIVE_AGENT_PROMPT',
    'MEMORY_AGENT_PROMPT'
]
