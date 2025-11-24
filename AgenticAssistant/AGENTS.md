# 🤖 Agent Guide - Detailed Documentation

## Overview

The AI Assistant uses **5 specialized agents** coordinated by an **Orchestrator**. Each agent has specific responsibilities and expertise.

## Agent Architecture

```
User Message
     ↓
Orchestrator (Routes message)
     ↓
Primary Agent (Handles request)
     ↓
Memory Agent (Extracts context)
     ↓
Response to User
```

---

## 1. Chat Agent 💬

### Purpose
Handle casual conversations, greetings, and general questions.

### Capabilities
- Friendly conversation
- General knowledge
- Small talk
- Getting to know the user
- Answering questions

### When It's Used
- Greetings: "Hi", "Hello", "How are you?"
- General questions: "What's the weather?", "Tell me about..."
- Casual chat: "I'm feeling great today!"
- Default fallback when no other agent matches

### Example Interactions

**Greeting**:
```
User: Hi! How's it going?
Chat Agent: Hello! I'm doing great, thanks for asking! 
How can I help you today?
```

**General Question**:
```
User: What do you think about AI?
Chat Agent: AI is fascinating! It's transforming how we work 
and interact with technology. What aspects interest you most?
```

### Technical Details
- **File**: `agents/chat_agent.py`
- **Prompt**: `CHAT_AGENT_PROMPT` in `llm/prompts.py`
- **Features**: 
  - Adapts to user's communication style
  - Maintains conversation context
  - Friendly and helpful tone

---

## 2. Productivity Agent ✅

### Purpose
Manage tasks, reminders, scheduling, and productivity.

### Capabilities
- Create tasks from natural language
- List and query tasks
- Prioritize tasks (high, medium, low)
- Set due dates
- Update task status
- Provide productivity advice

### When It's Used
- Task creation: "Create a task...", "Remind me to...", "I need to..."
- Task queries: "What are my tasks?", "Show my pending tasks"
- Productivity: "How should I prioritize?", "Help me organize"

### Example Interactions

**Creating a Task**:
```
User: Remind me to finish the project report by Friday, 
      it's high priority
      
Productivity Agent: ✅ Task created: finish the project report
                    Priority: HIGH
                    Due: 2024-11-29
                    
                    I've added this to your task list!
```

**Querying Tasks**:
```
User: What are my pending tasks?

Productivity Agent: 📋 You have 3 pending tasks:
                    
                    1. 🔴 finish the project report (Due: 2024-11-29)
                    2. 🟡 Review code changes
                    3. 🟢 Update documentation
```

**Productivity Advice**:
```
User: How should I organize my day?

Productivity Agent: Based on your 3 pending tasks, I recommend:
                    1. Start with the high-priority report (due Friday)
                    2. Then review the code changes
                    3. Update documentation when you have time
                    
                    Focus on one task at a time for best results!
```

### Technical Details
- **File**: `agents/productivity_agent.py`
- **Prompt**: `PRODUCTIVITY_AGENT_PROMPT`
- **Features**:
  - Natural language task extraction
  - Priority detection
  - Due date parsing
  - Task status management
  - Database integration

### Task Detection Keywords
- `create task`, `add task`, `new task`
- `remind me`, `reminder`
- `todo`, `need to`, `have to`
- `schedule`, `deadline`, `priority`

---

## 3. Creative Agent 🎨

### Purpose
Generate creative content, ideas, and summaries.

### Capabilities
- Write poems (haikus, sonnets, free verse)
- Create stories and narratives
- Generate summaries
- Brainstorm ideas
- Provide creative suggestions
- Content generation

### When It's Used
- Creative writing: "Write a poem...", "Tell me a story..."
- Summaries: "Summarize...", "Give me the key points..."
- Ideas: "Brainstorm...", "Give me ideas for..."
- Content: "Create...", "Generate..."

### Example Interactions

**Poetry**:
```
User: Write me a haiku about AI

Creative Agent: Silicon minds think
                Patterns emerge from the code
                Intelligence blooms
```

**Story**:
```
User: Tell me a short story about a robot

Creative Agent: Once upon a time, there was a curious robot 
                named Chip who dreamed of understanding human 
                emotions. One day, Chip discovered that the 
                secret wasn't in complex algorithms, but in 
                simply listening and caring...
```

**Summary**:
```
User: Summarize our last conversation

Creative Agent: Here's a summary of our discussion:
                
                Key Points:
                - You asked about task management
                - We discussed prioritization strategies
                - You created 2 new high-priority tasks
                - We talked about productivity tips
                
                Main Takeaway: Focus on one task at a time 
                for maximum productivity.
```

**Brainstorming**:
```
User: Give me 5 ideas for a blog post about AI

Creative Agent: Here are 5 blog post ideas:
                
                1. "How AI is Transforming Daily Life"
                2. "The Future of AI Assistants"
                3. "AI Ethics: What You Need to Know"
                4. "Building Your First AI Project"
                5. "AI vs Human Creativity: A Comparison"
```

### Technical Details
- **File**: `agents/creative_agent.py`
- **Prompt**: `CREATIVE_AGENT_PROMPT`
- **Features**:
  - Task type identification
  - Creative content generation
  - Proactive suggestions
  - Multiple formats (poems, stories, summaries)

### Creative Keywords
- `poem`, `haiku`, `sonnet`
- `story`, `narrative`, `tale`
- `write`, `create`, `generate`
- `summary`, `summarize`
- `brainstorm`, `ideas`, `suggestions`

---

## 4. Memory Agent 🧠

### Purpose
Store and retrieve user context, preferences, and information.

### Capabilities
- Extract memories from conversations
- Store user preferences
- Remember important information
- Retrieve relevant context
- Build user profile
- Provide personalized responses

### When It's Used
- Memory queries: "What do you remember?", "What do you know about me?"
- Preference setting: "I prefer...", "Remember that I..."
- Context retrieval: Automatically used by other agents
- Profile building: Continuous background process

### Example Interactions

**Memory Query**:
```
User: What do you remember about me?

Memory Agent: Here's what I remember about you:
              
              - communication_style: friendly and casual
              - interests: AI and technology
              - current_project: multi-agent assistant
              - preferred_priority: high for work tasks
              - work_schedule: prefers morning meetings
              - learning_goals: master Python and AI
```

**Setting Preferences**:
```
User: Remember that I prefer morning meetings

Memory Agent: ✅ I'll remember that you prefer morning meetings.
              This has been added to your preferences.
```

**Context Retrieval** (used by other agents):
```
Internal: Memory agent provides context to Chat agent
Context: "User prefers concise responses, interested in AI"

Chat Agent: [Uses this context to tailor response]
```

### Technical Details
- **File**: `agents/memory_agent.py`
- **Prompt**: `MEMORY_AGENT_PROMPT`
- **Features**:
  - Automatic memory extraction
  - Key-value storage
  - Context retrieval
  - Relevance scoring
  - Privacy-conscious

### Memory Types Stored
- **Preferences**: Communication style, work habits
- **Interests**: Topics, hobbies, goals
- **Context**: Current projects, ongoing tasks
- **Personal**: Important dates, information

---

## 5. Orchestrator 🎯

### Purpose
Coordinate all agents and route messages to the right agent(s).

### Capabilities
- Analyze user messages
- Determine appropriate agent
- Route to primary agent
- Coordinate secondary agents
- Manage agent interactions
- Extract memories automatically

### How It Works

1. **Message Analysis**:
   - Receives user message
   - Gets user context from Memory Agent
   - Analyzes intent and content

2. **Routing Decision**:
   - **Primary Method**: LLM-based decision
     - Uses Groq API to analyze message
     - Considers user context
     - Returns agent choice with reasoning
   
   - **Fallback Method**: Keyword matching
     - If LLM fails, uses keywords
     - Fast and reliable
     - Pattern-based routing

3. **Agent Execution**:
   - Routes to primary agent
   - Optionally involves secondary agents
   - Collects responses

4. **Memory Update**:
   - Automatically extracts memories
   - Stores in database
   - Updates user context

### Routing Logic

**LLM-Based Routing**:
```python
User: "Remind me to call John tomorrow"
↓
Orchestrator analyzes with LLM
↓
Decision: {
    "primary_agent": "productivity",
    "reasoning": "User wants to create a reminder task"
}
↓
Routes to Productivity Agent
```

**Keyword-Based Fallback**:
```python
Keywords detected: ["remind", "tomorrow"]
↓
Matches productivity keywords
↓
Routes to Productivity Agent
```

### Routing Keywords

**Productivity**:
- task, todo, remind, schedule, deadline, priority

**Creative**:
- poem, story, write, create, summary, brainstorm, ideas

**Memory**:
- remember, what do you know, my preferences, tell me about me

**Chat** (default):
- Everything else

### Technical Details
- **File**: `agents/orchestrator.py`
- **Prompt**: `ORCHESTRATOR_PROMPT`
- **Features**:
  - Intelligent routing
  - Multi-agent coordination
  - Automatic memory extraction
  - Error handling and fallbacks

---

## Agent Interaction Flow

### Example: Creating a Task

```
1. User: "Remind me to finish the report by Friday"
   ↓
2. Orchestrator receives message
   ↓
3. Orchestrator gets user context from Memory Agent
   ↓
4. Orchestrator analyzes message (LLM or keywords)
   ↓
5. Decision: Route to Productivity Agent
   ↓
6. Productivity Agent:
   - Detects task creation intent
   - Extracts task details (title, priority, due date)
   - Creates task in database
   - Returns confirmation
   ↓
7. Orchestrator:
   - Receives response
   - Calls Memory Agent to extract memories
   - Returns response to user
   ↓
8. User sees: "✅ Task created: finish the report..."
```

### Example: Multi-Agent Interaction

```
1. User: "What should I work on today?"
   ↓
2. Orchestrator routes to Productivity Agent
   ↓
3. Productivity Agent:
   - Queries tasks from database
   - Gets user preferences from Memory Agent
   - Provides prioritized recommendations
   ↓
4. Memory Agent (background):
   - Extracts: "user asked about daily planning"
   - Stores context
   ↓
5. Response combines both agents' work
```

---

## Customizing Agents

### Modifying Agent Behavior

**Edit System Prompts** (`llm/prompts.py`):
```python
CHAT_AGENT_PROMPT = """
You are a friendly AI assistant.
[Modify this to change behavior]
"""
```

### Adding New Capabilities

**Example: Add email support to Productivity Agent**:

1. Update `productivity_agent.py`:
```python
def _is_email_request(self, message: str) -> bool:
    keywords = ['send email', 'email', 'message']
    return any(keyword in message.lower() for keyword in keywords)
```

2. Add handler:
```python
def _handle_email(self, user_id: int, message: str) -> str:
    # Email logic here
    pass
```

3. Update `process()` method:
```python
if self._is_email_request(message):
    return self._handle_email(user_id, message)
```

---

## Best Practices

### For Users

1. **Be specific**: "Create a high-priority task to review code by tomorrow"
2. **Use keywords**: Helps routing (task, remind, write, etc.)
3. **Check the right tab**: Tasks appear in Tasks tab, not just chat
4. **Build context**: The more you chat, the better the memory

### For Developers

1. **Keep agents focused**: Each agent should have clear responsibilities
2. **Use base class**: Inherit from `BaseAgent` for consistency
3. **Save conversations**: Always call `add_conversation()`
4. **Handle errors**: Use try-except for robustness
5. **Update routing**: Add keywords when adding features

---

## Troubleshooting

### Agent Not Responding Correctly

1. Check routing decision in logs
2. Verify keywords in orchestrator
3. Test LLM-based routing
4. Check agent's system prompt

### Tasks Not Created

1. Verify Productivity Agent is being called
2. Check database for task entry
3. Look for errors in console
4. Refresh the Tasks tab

### Memories Not Stored

1. Check Memory Agent extraction
2. Verify database writes
3. Look in sidebar for memories
4. Check conversation was saved

---

**For more details, see:**
- `README.md` - General overview
- `WORKFLOW.md` - Development guide
- Source code in `agents/` directory
