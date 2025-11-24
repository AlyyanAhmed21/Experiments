"""
Multi-Agent AI Personal Assistant - Clean & Simple UI
"""
import streamlit as st
from datetime import datetime
import hashlib
from typing import Optional

from config import config
from database import DatabaseManager
from agents import Orchestrator
from utils import voice_utils


# Page configuration
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)


def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def initialize_session_state():
    """Initialize Streamlit session state."""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager(config.DATABASE_PATH)
    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = Orchestrator(st.session_state.db_manager)


def check_configuration():
    """Check if configuration is valid."""
    is_valid, errors = config.validate()
    
    if not is_valid:
        st.error("⚠️ **Configuration Error**")
        st.markdown("### Please set up your API keys:")
        for error in errors:
            st.markdown(f"- {error}")
        
        st.info("💡 **How to fix:**\n\n1. Get a free Groq API key at https://console.groq.com\n2. Get a free LangSmith API key at https://smith.langchain.com\n3. Edit your `.env` file and add the keys")
        
        st.code("""
# Example .env file
GROQ_API_KEY=gsk_your_actual_key_here
LANGSMITH_API_KEY=ls_your_actual_key_here
        """, language="bash")
        
        st.stop()


def login_page():
    """Simple centered login page."""
    # Center the content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("# 🤖 AI Assistant")
        st.markdown("### Your Personal Multi-Agent Assistant")
        st.markdown("---")
        
        # Login/Register tabs
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.markdown("#### Login to your account")
            username = st.text_input("Username", key="login_user", placeholder="Enter username")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="Enter password")
            
            if st.button("Login", use_container_width=True, type="primary"):
                if username and password:
                    user = st.session_state.db_manager.get_user_by_username(username)
                    
                    if user:
                        if st.session_state.db_manager.verify_password(username, hash_password(password)):
                            st.session_state.user = user
                            st.session_state.user_id = user.user_id
                            load_conversation_history()
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid password")
                    else:
                        st.error("❌ User not found. Please register first.")
                else:
                    st.error("Please fill in all fields")
        
        with tab2:
            st.markdown("#### Create a new account")
            new_username = st.text_input("Username", key="reg_user", placeholder="Choose a username")
            new_password = st.text_input("Password", type="password", key="reg_pass", placeholder="Choose a password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm", placeholder="Confirm password")
            
            if st.button("Create Account", use_container_width=True, type="primary"):
                if new_username and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("❌ Passwords don't match")
                    elif len(new_password) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    else:
                        existing_user = st.session_state.db_manager.get_user_by_username(new_username)
                        if existing_user:
                            st.error("❌ Username already exists")
                        else:
                            user = st.session_state.db_manager.create_user(new_username, hash_password(new_password))
                            st.success("✅ Account created! Please login.")
                else:
                    st.error("Please fill in all fields")


def load_conversation_history():
    """Load conversation history from database."""
    if st.session_state.user_id:
        conversations = st.session_state.db_manager.get_conversation_history(
            st.session_state.user_id,
            limit=20
        )
        
        st.session_state.messages = []
        for conv in conversations:
            st.session_state.messages.append({
                "role": "user",
                "content": conv.message
            })
            st.session_state.messages.append({
                "role": "assistant",
                "content": conv.response,
                "agent": conv.agent_type
            })


def chat_interface():
    """Main chat interface."""
    st.title("💬 Chat")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            # Show agent attribution
            if message["role"] == "assistant" and "agent" in message:
                agent_emoji = {
                    'chat': '💬',
                    'productivity': '✅',
                    'creative': '🎨',
                    'memory': '🧠'
                }
                emoji = agent_emoji.get(message["agent"], '🤖')
                st.caption(f"{emoji} {message['agent'].title()} Agent")
    
    # Chat input
    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    result = st.session_state.orchestrator.process_message(
                        st.session_state.user_id,
                        prompt
                    )
                    
                    response = result['response']
                    agent_type = result['primary_agent']
                    
                    st.write(response)
                    
                    agent_emoji = {
                        'chat': '💬',
                        'productivity': '✅',
                        'creative': '🎨',
                        'memory': '🧠'
                    }
                    emoji = agent_emoji.get(agent_type, '🤖')
                    st.caption(f"{emoji} {agent_type.title()} Agent")
                    
                    # Add to messages
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "agent": agent_type
                    })
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.info("💡 Make sure your Groq API key is valid in the `.env` file")


def task_dashboard():
    """Task management dashboard."""
    st.title("📋 Tasks")
    
    # Create task
    with st.expander("➕ Create New Task"):
        title = st.text_input("Task Title")
        description = st.text_area("Description (optional)")
        
        col1, col2 = st.columns(2)
        with col1:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=1)
        with col2:
            due_date = st.date_input("Due Date (optional)", value=None)
        
        if st.button("Create Task", type="primary"):
            if title:
                task = st.session_state.db_manager.create_task(
                    user_id=st.session_state.user_id,
                    title=title,
                    description=description,
                    priority=priority,
                    due_date=str(due_date) if due_date else None
                )
                st.success(f"✅ Task created: {task.title}")
                st.rerun()
            else:
                st.error("Please enter a task title")
    
    st.markdown("---")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Status", ["all", "pending", "in_progress", "completed"])
    with col2:
        priority_filter = st.selectbox("Priority", ["all", "high", "medium", "low"])
    
    # Get tasks
    tasks = st.session_state.db_manager.get_tasks(
        st.session_state.user_id,
        status=None if status_filter == "all" else status_filter,
        priority=None if priority_filter == "all" else priority_filter
    )
    
    if not tasks:
        st.info("No tasks found")
    else:
        for task in tasks:
            priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
            status_emoji = {'pending': '⏳', 'in_progress': '🔄', 'completed': '✅'}
            
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                st.markdown(f"**{priority_emoji.get(task.priority, '')} {task.title}**")
                if task.description:
                    st.caption(task.description)
                if task.due_date:
                    st.caption(f"📅 {task.due_date}")
            
            with col2:
                st.write(f"{status_emoji.get(task.status, '')} {task.status}")
            
            with col3:
                if task.status == "pending":
                    if st.button("Start", key=f"start_{task.task_id}"):
                        st.session_state.db_manager.update_task_status(task.task_id, "in_progress")
                        st.rerun()
                elif task.status == "in_progress":
                    if st.button("Done", key=f"done_{task.task_id}"):
                        st.session_state.db_manager.update_task_status(task.task_id, "completed")
                        st.rerun()
                
                if st.button("🗑️", key=f"del_{task.task_id}"):
                    st.session_state.db_manager.delete_task(task.task_id)
                    st.rerun()
            
            st.divider()


def sidebar():
    """Sidebar."""
    with st.sidebar:
        st.markdown("# 🤖 AI Assistant")
        
        if st.session_state.user:
            st.markdown(f"**User:** {st.session_state.user.username}")
            
            # Memory
            memories = st.session_state.db_manager.get_all_memories(st.session_state.user_id)
            with st.expander(f"🧠 Memories ({len(memories)})"):
                if memories:
                    for memory in memories[:5]:
                        st.caption(f"• {memory.key}: {memory.value}")
                else:
                    st.caption("No memories yet")
            
            st.markdown("---")
            
            # Navigation
            page = st.radio("Navigation", ["💬 Chat", "📋 Tasks"], label_visibility="collapsed")
            
            st.markdown("---")
            
            # Settings
            with st.expander("⚙️ Settings"):
                st.caption(f"Model: {config.DEFAULT_MODEL}")
                st.caption(f"Temp: {config.TEMPERATURE}")
                
                if voice_utils.stt_available:
                    st.caption(f"✅ STT: {voice_utils.stt_method}")
                if voice_utils.tts_available:
                    st.caption(f"✅ TTS: {voice_utils.tts_method}")
            
            # Logout
            if st.button("Logout"):
                st.session_state.user = None
                st.session_state.user_id = None
                st.session_state.messages = []
                st.rerun()
            
            return page
    
    return "💬 Chat"


def main():
    """Main application."""
    initialize_session_state()
    check_configuration()
    
    if not st.session_state.user:
        login_page()
    else:
        page = sidebar()
        
        if page == "💬 Chat":
            chat_interface()
        elif page == "📋 Tasks":
            task_dashboard()


if __name__ == "__main__":
    main()
