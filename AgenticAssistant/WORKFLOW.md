# 🔄 Development Workflow

This guide explains how to work with the AI Assistant codebase.

## 🚀 Getting Started

### 1. Environment Setup
```bash
# Activate conda environment
conda activate ai-assistant

# Or activate venv
source venv/bin/activate
```

### 2. Configuration
```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

### 3. Run the App
```bash
streamlit run app.py
```

## 📁 Project Structure

### Core Files
- `app.py` - Main Streamlit application
- `config.py` - Configuration and environment variables
- `.env` - Your API keys (gitignored)
- `.env.example` - Template for environment variables

### Agents (`agents/`)
- `base_agent.py` - Base class for all agents
- `chat_agent.py` - Handles casual conversation
- `productivity_agent.py` - Manages tasks and productivity
- `creative_agent.py` - Generates creative content
- `memory_agent.py` - Stores and retrieves user context
- `orchestrator.py` - Routes messages to appropriate agents

### LLM Integration (`llm/`)
- `llm_client.py` - Groq API client with streaming support
- `prompts.py` - System prompts for each agent

### Database (`database/`)
- `models.py` - Database schema definitions
- `db_manager.py` - CRUD operations for all tables

### Utilities (`utils/`)
- `langsmith_tracker.py` - LangSmith integration for tracking
- `voice_utils.py` - Voice input/output utilities

## 🛠️ Common Development Tasks

### Adding a New Agent

1. **Create agent file** in `agents/`:
```python
from agents.base_agent import BaseAgent
from llm.prompts import YOUR_AGENT_PROMPT

class YourAgent(BaseAgent):
    def __init__(self, db_manager):
        super().__init__(
            agent_name="your_agent",
            system_prompt=YOUR_AGENT_PROMPT,
            db_manager=db_manager
        )
    
    def process(self, user_id, message, context=None):
        # Your agent logic here
        response = self.create_response(user_id, message)
        
        # Save conversation
        self.db_manager.add_conversation(
            user_id=user_id,
            agent_type=self.agent_name,
            message=message,
            response=response
        )
        
        return response
```

2. **Add prompt** in `llm/prompts.py`:
```python
YOUR_AGENT_PROMPT = """
You are a specialized agent for [purpose].
Your responsibilities:
- [Responsibility 1]
- [Responsibility 2]
"""
```

3. **Register in orchestrator** (`agents/orchestrator.py`):
```python
self.agents = {
    'chat': ChatAgent(db_manager),
    'productivity': ProductivityAgent(db_manager),
    'your_agent': YourAgent(db_manager),  # Add here
}
```

4. **Update routing logic** in `orchestrator.py`:
```python
# In _fallback_routing method
elif any(word in message_lower for word in ['keyword1', 'keyword2']):
    return {
        'primary_agent': 'your_agent',
        'secondary_agents': [],
        'reasoning': 'Keyword match for your agent'
    }
```

### Modifying Database Schema

1. **Update schema** in `database/models.py`:
```python
CREATE_YOUR_TABLE = """
CREATE TABLE IF NOT EXISTS your_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    your_field TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
"""
```

2. **Add CRUD methods** in `database/db_manager.py`:
```python
def create_your_item(self, user_id, data):
    with self.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO your_table (user_id, your_field) VALUES (?, ?)",
            (user_id, data)
        )
        return cursor.lastrowid
```

3. **Delete old database** to recreate with new schema:
```bash
rm data/assistant.db
```

### Changing LLM Model

Edit `.env`:
```bash
# Change from
DEFAULT_MODEL=llama-3.3-70b-versatile

# To any available model
DEFAULT_MODEL=mixtral-8x7b-32768
```

See `AVAILABLE_MODELS.md` for options.

### Adjusting LLM Parameters

Edit `.env`:
```bash
TEMPERATURE=0.7      # 0.0-1.0 (higher = more creative)
MAX_TOKENS=2048      # Maximum response length
```

## 🧪 Testing

### Manual Testing Checklist

**Authentication**:
- [ ] Register new user
- [ ] Login with correct credentials
- [ ] Login with wrong password (should fail)
- [ ] Logout and login again

**Chat Interface**:
- [ ] Send a casual message (should use Chat Agent)
- [ ] Ask to create a task (should use Productivity Agent)
- [ ] Request creative content (should use Creative Agent)
- [ ] Ask about memories (should use Memory Agent)

**Task Management**:
- [ ] Create task via chat
- [ ] Create task via dashboard
- [ ] View tasks in dashboard
- [ ] Start a task
- [ ] Complete a task
- [ ] Delete a task
- [ ] Filter by status
- [ ] Filter by priority

**Memory**:
- [ ] Have a conversation
- [ ] Check sidebar for memories
- [ ] Ask "what do you remember about me?"
- [ ] Verify memories persist across sessions

### Testing with Different Models

```bash
# Test with fast model
DEFAULT_MODEL=llama-3.1-8b-instant

# Test with large context
DEFAULT_MODEL=mixtral-8x7b-32768

# Test with default
DEFAULT_MODEL=llama-3.3-70b-versatile
```

## 🐛 Debugging

### Enable Verbose Logging

Add to `config.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check LangSmith Dashboard

1. Go to https://smith.langchain.com
2. Select your project
3. View all LLM calls and agent interactions

### Common Issues

**Tasks not appearing in dashboard**:
- Check if task was actually created in database
- Verify user_id matches
- Try refreshing the page
- Check browser console for errors

**Agent routing incorrectly**:
- Check orchestrator logs
- Verify keywords in `_fallback_routing`
- Test LLM-based routing decision

**Database errors**:
- Delete and recreate: `rm data/assistant.db`
- Check schema in `database/models.py`
- Verify foreign key constraints

## 📦 Deployment Workflow

### 1. Prepare for Deployment

```bash
# Test locally first
streamlit run app.py

# Verify all features work
# Check .env.example is up to date
# Update README if needed
```

### 2. Deploy to Streamlit Cloud

```bash
# Push to GitHub
git add .
git commit -m "Ready for deployment"
git push origin main

# Go to share.streamlit.io
# Connect repository
# Add secrets from .env
# Deploy!
```

### 3. Monitor Deployment

- Check Streamlit Cloud logs
- Test deployed app
- Monitor LangSmith for errors
- Verify database persistence

## 🔄 Update Workflow

### Updating Dependencies

```bash
# Update requirements.txt
pip freeze > requirements.txt

# Update environment.yml
conda env export > environment.yml
```

### Updating Documentation

When adding features:
1. Update `README.md` with new features
2. Update `QUICKSTART.md` if setup changes
3. Add to `WORKFLOW.md` if development process changes
4. Update `.env.example` if new env vars added

## 📊 Performance Optimization

### Database Optimization

```python
# Add indexes for frequently queried fields
CREATE INDEX idx_user_tasks ON tasks(user_id, status);
CREATE INDEX idx_conversations ON conversations(user_id, timestamp);
```

### LLM Optimization

```bash
# Use faster model for simple tasks
DEFAULT_MODEL=llama-3.1-8b-instant

# Reduce max tokens for shorter responses
MAX_TOKENS=1024

# Lower temperature for more focused responses
TEMPERATURE=0.5
```

### Caching

Streamlit has built-in caching:
```python
@st.cache_data
def expensive_operation():
    # This will be cached
    pass
```

## 🔐 Security Best Practices

1. **Never commit `.env`** - It's gitignored
2. **Use environment variables** for all secrets
3. **Hash passwords** - Already implemented with SHA-256
4. **Validate user input** - Sanitize before database queries
5. **Use parameterized queries** - Already implemented

## 📝 Code Style

### Python Style Guide

- Follow PEP 8
- Use type hints
- Add docstrings to all functions
- Keep functions focused and small

### Example:
```python
def process_message(
    self,
    user_id: int,
    message: str
) -> str:
    """
    Process a user message.
    
    Args:
        user_id: User ID
        message: User message
        
    Returns:
        Agent response
    """
    # Implementation
    pass
```

## 🎯 Next Steps

Potential enhancements:
- [ ] Add unit tests
- [ ] Implement vector search for memories
- [ ] Add more agents (email, calendar, etc.)
- [ ] Improve UI/UX
- [ ] Add export functionality
- [ ] Implement conversation search
- [ ] Add analytics dashboard
- [ ] Support multiple languages

---

**Happy coding! 🚀**

For questions, check the main README.md or other documentation files.
