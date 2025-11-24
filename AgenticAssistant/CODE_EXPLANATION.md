# 📖 Code Explanation Guide

A complete walkthrough of the AI Assistant codebase to help you understand how everything works.

---

## 📁 Project Overview

```
AgenticAssistant/
├── app.py                    # Main Streamlit UI
├── config.py                 # Configuration & settings
├── agents/                   # All AI agents
├── llm/                      # LLM API integration
├── database/                 # Data storage
└── utils/                    # Helper utilities
```

---

## 1️⃣ Entry Point: `app.py`

**What it does**: The main Streamlit application that users interact with.

### Key Components

#### Session State Initialization
```python
def initialize_session_state():
    if 'user' not in st.session_state:
        st.session_state.user = None
```
**Purpose**: Stores data that persists across page reloads (user info, messages, database connection).

#### Login Page
```python
def login_page():
    tab1, tab2 = st.tabs(["Login", "Register"])
```
**Purpose**: 
- Displays centered login/register forms
- Validates credentials against database
- Hashes passwords with SHA-256
- Creates new users or logs in existing ones

#### Chat Interface
```python
def chat_interface():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
```
**Purpose**:
- Displays conversation history
- Shows which agent handled each message
- Sends new messages to orchestrator
- Handles streaming responses

#### Task Dashboard
```python
def task_dashboard():
    tasks = st.session_state.db_manager.get_tasks(user_id)
```
**Purpose**:
- Create tasks with form
- Display tasks with filters
- Update task status (pending → in_progress → completed)
- Delete tasks

**Flow**:
```
User opens app → Login → Chat/Tasks → Orchestrator → Agent → Response
```

---

## 2️⃣ Configuration: `config.py`

**What it does**: Manages all settings and environment variables.

### Key Parts

#### Environment Loading
```python
from dotenv import load_dotenv
load_dotenv()
```
**Purpose**: Loads `.env` file so you can use `GROQ_API_KEY` etc.

#### Config Class
```python
class Config:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "llama-3.3-70b-versatile")
```
**Purpose**: 
- Centralized settings
- Type hints for clarity
- Default values if env var not set

#### Validation
```python
def validate(cls) -> tuple[bool, list[str]]:
    if not cls.GROQ_API_KEY:
        errors.append("GROQ_API_KEY is required")
```
**Purpose**: Checks that required API keys are present before app starts.

---

## 3️⃣ Database Layer: `database/`

### `models.py` - Database Schema

**What it does**: Defines the structure of your SQLite database.

#### User Model
```python
@dataclass
class User:
    user_id: int
    username: str
    password_hash: Optional[str]
    created_at: str
    preferences: Optional[Dict]
```
**Purpose**: Represents a user in the system.

#### SQL Schema
```python
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    ...
)
"""
```
**Purpose**: Creates the actual database table when app first runs.

### `db_manager.py` - Database Operations

**What it does**: Handles all database interactions (CRUD operations).

#### Context Manager
```python
@contextmanager
def get_connection(self):
    conn = sqlite3.connect(self.db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
```
**Purpose**: 
- Opens database connection
- Automatically commits changes
- Always closes connection (even if error)
- Prevents database locks

#### CRUD Operations
```python
def create_user(self, username: str, password_hash: str) -> User:
    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, password_hash)
    )
```
**Purpose**: 
- `?` prevents SQL injection
- Returns User object with new ID
- Handles errors gracefully

**Key Methods**:
- `create_user()` - Register new user
- `get_user_by_username()` - Login lookup
- `verify_password()` - Check password hash
- `create_task()` - Add new task
- `get_tasks()` - Query tasks with filters
- `add_conversation()` - Save chat history
- `create_memory()` - Store user preferences

---

## 4️⃣ LLM Integration: `llm/`

### `llm_client.py` - Groq API Client

**What it does**: Talks to Groq API to get LLM responses.

#### Initialization
```python
def __init__(self):
    self.client = Groq(api_key=config.GROQ_API_KEY)
    self.default_model = config.DEFAULT_MODEL
```
**Purpose**: Sets up Groq client with your API key.

#### LangSmith Tracing
```python
@self.traceable(
    name=f"groq_{model}",
    run_type="llm",
    metadata={...}
)
def traced_call():
    return self._raw_completion(...)
```
**Purpose**: 
- Wraps API calls for tracking
- Sends data to LangSmith dashboard
- Records input, output, latency

#### Chat Completion
```python
def chat_completion(self, messages, model, temperature):
    response = self.client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
```
**Purpose**: 
- Sends messages to LLM
- Gets response back
- Handles errors

#### Message Formatting
```python
def create_messages(self, system_prompt, user_message, context):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
```
**Purpose**: 
- Formats messages for API
- Adds system prompt (agent instructions)
- Includes user context (memories)
- Adds conversation history

### `prompts.py` - System Prompts

**What it does**: Contains instructions for each agent.

```python
CHAT_AGENT_PROMPT = """
You are a friendly AI assistant.
Be conversational and helpful.
"""
```
**Purpose**: Tells the LLM how to behave for each agent type.

---

## 5️⃣ Agents: `agents/`

### `base_agent.py` - Base Class

**What it does**: Common functionality all agents share.

#### Inheritance
```python
class BaseAgent:
    def __init__(self, agent_name, system_prompt, db_manager):
        self.agent_name = agent_name
        self.system_prompt = system_prompt
```
**Purpose**: 
- All agents inherit from this
- Provides common methods
- Reduces code duplication

#### Context Retrieval
```python
def get_user_context(self, user_id):
    memories = self.db_manager.get_all_memories(user_id)
    context = "\n".join([f"{m.key}: {m.value}" for m in memories])
```
**Purpose**: 
- Gets user's stored memories
- Formats as text
- Adds to LLM prompt

#### Response Creation
```python
def create_response(self, user_id, message):
    user_context = self.get_user_context(user_id)
    messages = self.llm_client.create_messages(
        self.system_prompt, message, user_context
    )
    response = self.llm_client.get_completion_text(messages)
```
**Purpose**: 
- Gets user context
- Creates formatted messages
- Calls LLM
- Returns response

### `chat_agent.py` - Chat Agent

**What it does**: Handles casual conversation.

```python
class ChatAgent(BaseAgent):
    def process(self, user_id, message):
        response = self.create_response(user_id, message)
        self.db_manager.add_conversation(...)
        return response
```
**Purpose**: 
- Uses base class methods
- Saves conversation to database
- Returns friendly response

### `productivity_agent.py` - Productivity Agent

**What it does**: Manages tasks and productivity.

#### Task Detection
```python
def _is_task_creation(self, message):
    keywords = ['create task', 'remind me', 'todo']
    return any(keyword in message.lower() for keyword in keywords)
```
**Purpose**: Checks if user wants to create a task.

#### Task Creation
```python
def _handle_task_creation(self, user_id, message):
    # Ask LLM to extract task details
    task_data = self.llm_client.parse_json_response(response)
    
    # Create task in database
    task = self.db_manager.create_task(
        user_id=user_id,
        title=task_data.get('title'),
        priority=task_data.get('priority')
    )
```
**Purpose**: 
1. Extracts task details from natural language
2. Creates task in database
3. Returns confirmation message

#### Task Query
```python
def _handle_task_query(self, user_id, message):
    tasks = self.db_manager.get_tasks(user_id, status='pending')
    response = f"You have {len(tasks)} pending tasks:\n"
```
**Purpose**: Lists user's tasks with formatting.

### `creative_agent.py` - Creative Agent

**What it does**: Generates creative content.

```python
def process(self, user_id, message):
    task_type = self._identify_task_type(message)
    
    if task_type == "poem":
        # Generate poem
    elif task_type == "story":
        # Generate story
```
**Purpose**: 
- Identifies what type of content to create
- Uses LLM to generate
- Returns creative output

### `memory_agent.py` - Memory Agent

**What it does**: Stores and retrieves user information.

#### Memory Extraction
```python
def extract_and_store_memories(self, user_id, conversation):
    extraction_prompt = """
    Extract key information from this conversation.
    Return JSON: {"key": "value"}
    """
    
    memories = self.llm_client.parse_json_response(response)
    
    for key, value in memories.items():
        self.db_manager.create_memory(user_id, key, value)
```
**Purpose**: 
1. Analyzes conversation
2. Extracts important info (preferences, facts)
3. Stores in database

#### Context Retrieval
```python
def get_relevant_context(self, user_id, query):
    memories = self.db_manager.get_all_memories(user_id)
    # Format and return relevant memories
```
**Purpose**: Gets user's memories to personalize responses.

### `orchestrator.py` - Orchestrator

**What it does**: Routes messages to the right agent.

#### Message Routing
```python
def process_message(self, user_id, message):
    # 1. Decide which agent to use
    routing_decision = self._route_message(user_id, message)
    
    # 2. Get response from primary agent
    primary_agent = routing_decision['primary_agent']
    response = self.agents[primary_agent].process(user_id, message)
    
    # 3. Extract memories
    self._update_memories(user_id, message, response)
    
    return response
```

#### Routing Decision
```python
def _route_message(self, user_id, message):
    # Try LLM-based routing
    routing_prompt = """
    Which agent should handle: "{message}"?
    Options: chat, productivity, creative, memory
    """
    
    decision = self.llm_client.parse_json_response(response)
    
    # Fallback to keywords if LLM fails
    if not decision:
        return self._fallback_routing(message)
```
**Purpose**: 
- **Primary**: Uses LLM to analyze message
- **Fallback**: Uses keyword matching
- Returns which agent to use

#### Keyword Fallback
```python
def _fallback_routing(self, message):
    if any(word in message for word in ['task', 'remind']):
        return {'primary_agent': 'productivity'}
    elif any(word in message for word in ['poem', 'story']):
        return {'primary_agent': 'creative'}
```
**Purpose**: Simple keyword matching if LLM routing fails.

---

## 6️⃣ Utilities: `utils/`

### `langsmith_tracker.py` - LangSmith Integration

**What it does**: Tracks agent interactions for debugging.

```python
if config.LANGSMITH_TRACING:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = config.LANGSMITH_API_KEY
```
**Purpose**: 
- Sets environment variables
- Enables automatic tracing
- Logs to LangSmith dashboard

### `voice_utils.py` - Voice Features

**What it does**: Speech-to-text and text-to-speech.

```python
def _init_local_whisper(self):
    from transformers import pipeline
    self.whisper_pipeline = pipeline(
        "automatic-speech-recognition",
        model="openai/whisper-base"
    )
```
**Purpose**: 
- Loads local Whisper model (free!)
- Transcribes audio to text
- Optional TTS with OpenAI

---

## 🔄 Complete Flow Example

### User: "Remind me to finish the report by Friday"

**1. App.py - Chat Interface**
```python
prompt = st.chat_input("Type your message...")
# User types message
```

**2. Orchestrator - Route Message**
```python
routing_decision = self._route_message(user_id, message)
# Decision: {'primary_agent': 'productivity'}
```

**3. Productivity Agent - Process**
```python
if self._is_task_creation(message):
    return self._handle_task_creation(user_id, message)
```

**4. LLM Client - Extract Details**
```python
# Sends to Groq API: "Extract task details from: 'Remind me...'"
# Response: {"title": "finish the report", "priority": "medium", "due_date": "2024-11-29"}
```

**5. Database - Create Task**
```python
task = db_manager.create_task(
    user_id=1,
    title="finish the report",
    priority="medium",
    due_date="2024-11-29"
)
# Saves to SQLite database
```

**6. Response to User**
```python
response = "✅ Task created: finish the report\nPriority: MEDIUM\nDue: 2024-11-29"
# Displayed in chat
```

**7. Memory Agent - Extract Context**
```python
# Automatically extracts: "user has work deadline on Friday"
# Stores in memory table
```

**8. LangSmith - Track Everything**
```python
# Logs to dashboard:
# - Orchestrator routing decision
# - Productivity agent LLM call
# - Task extraction
# - Total latency
```

---

## 🎯 Key Concepts

### 1. **Separation of Concerns**
- **App**: UI only
- **Agents**: Business logic
- **Database**: Data storage
- **LLM**: AI capabilities

### 2. **Inheritance**
- All agents inherit from `BaseAgent`
- Reduces code duplication
- Consistent interface

### 3. **Dependency Injection**
- Agents receive `db_manager` in constructor
- Easy to test and modify
- Loose coupling

### 4. **Error Handling**
- Try-except blocks everywhere
- Graceful degradation
- User-friendly error messages

### 5. **Context Management**
- Database connections auto-close
- Prevents resource leaks
- Transaction safety

---

## 📝 Code Patterns

### Pattern 1: Database Operations
```python
with self.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ...")
    # Auto-commits and closes
```

### Pattern 2: Agent Processing
```python
def process(self, user_id, message):
    # 1. Get context
    context = self.get_user_context(user_id)
    
    # 2. Call LLM
    response = self.create_response(user_id, message)
    
    # 3. Save conversation
    self.db_manager.add_conversation(...)
    
    # 4. Return response
    return response
```

### Pattern 3: LLM Calls
```python
# 1. Create messages
messages = self.llm_client.create_messages(
    system_prompt, user_message, context
)

# 2. Get response
response = self.llm_client.get_completion_text(messages)

# 3. Parse if needed
data = self.llm_client.parse_json_response(response)
```

---

## 🔍 Where to Look

**Want to understand...**

- **How login works?** → `app.py` → `login_page()`
- **How tasks are created?** → `agents/productivity_agent.py` → `_handle_task_creation()`
- **How routing works?** → `agents/orchestrator.py` → `_route_message()`
- **How database works?** → `database/db_manager.py`
- **How LLM calls work?** → `llm/llm_client.py` → `chat_completion()`
- **How memories are stored?** → `agents/memory_agent.py` → `extract_and_store_memories()`

---

## 💡 Tips for Reading Code

1. **Start with `app.py`** - See the big picture
2. **Follow the flow** - User action → Orchestrator → Agent → Database
3. **Read docstrings** - Every function has explanation
4. **Check type hints** - Shows what data types are expected
5. **Look at imports** - See what dependencies are used

---

**Next Steps**: 
- Read `README.md` for usage guide
- Check `WORKFLOW.md` for development
- See `AGENTS.md` for agent details

Happy coding! 🚀
