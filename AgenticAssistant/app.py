"""
Multi-Agent AI Personal Assistant - Clean & Simple UI
"""
import streamlit as st
from datetime import datetime
import hashlib
import time
from typing import Optional

from config import config
from database import DatabaseManager
from agents import Orchestrator
from utils import voice_utils
import extra_streamlit_components as stx


# Page configuration must be the very first command
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)


def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def get_manager():
    """
    Initialize Cookie Manager.
    We use a simplified singleton pattern here to ensure it persists across reruns.
    """
    return stx.CookieManager(key="auth_cookie_manager")


def initialize_session_state():
    """Initialize Streamlit session state and handle Auto-Login."""
    
    # 1. Initialize core state variables
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
    
    # 2. Initialize Cookie Manager
    # We store it in session state so we can access it in the sidebar later
    if 'cookie_manager' not in st.session_state:
        st.session_state.cookie_manager = get_manager()

    # 3. Auto-Login Logic (Check Cookies)
    # Only check if user is NOT currently logged in
    if st.session_state.user is None:
        try:
            cookie_manager = st.session_state.cookie_manager
            # get_all() triggers a re-render if cookies are loading
            cookies = cookie_manager.get_all()
            
            if cookies and isinstance(cookies, dict):
                token = cookies.get('auth_token')
                
                if token:
                    # VALIDATE AGAINST DATABASE
                    session = st.session_state.db_manager.get_session(token)
                    
                    if session:
                        # Session is valid, log the user in
                        user = st.session_state.db_manager.get_user_by_id(session.user_id)
                        if user:
                            st.session_state.user = user
                            st.session_state.user_id = user.user_id
                            load_conversation_history()
        except Exception as e:
            print(f"Auto-login check failed (this is normal during startup): {e}")


def check_configuration():
    """Check if configuration is valid."""
    is_valid, errors = config.validate()
    
    if not is_valid:
        st.error("⚠️ **Configuration Error**")
        st.markdown("### Please set up your API keys:")
        for error in errors:
            st.markdown(f"- {error}")
        st.stop()


def login_page():
    """Simple centered login page."""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("# 🤖 AI Assistant")
        st.markdown("### Your Personal Multi-Agent Assistant")
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.markdown("#### Login to your account")
            username = st.text_input("Username", key="login_user", placeholder="Enter username")
            password = st.text_input("Password", type="password", key="login_pass", placeholder="Enter password")
            
            if st.button("Login", use_container_width=True, type="primary"):
                if username and password:
                    user = st.session_state.db_manager.get_user_by_username(username)
                    
                    if user and st.session_state.db_manager.verify_password(username, hash_password(password)):
                        # 1. Set Session State
                        st.session_state.user = user
                        st.session_state.user_id = user.user_id
                        
                        # 2. Create Persistent DB Session
                        session = st.session_state.db_manager.create_session(user.user_id)
                        
                        # 3. Set Cookie
                        # Expiry set to 30 days
                        try:
                            expires = datetime.fromisoformat(session.expires_at)
                            st.session_state.cookie_manager.set('auth_token', session.token, expires_at=expires, key="set_auth_cookie")
                        except Exception as e:
                            print(f"Cookie setting error: {e}")
                        
                        load_conversation_history()
                        st.success("✅ Login successful!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
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
                            st.session_state.db_manager.create_user(new_username, hash_password(new_password))
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
    st.title("💬 Chat")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant" and "agent" in message:
                agent_emoji = {'chat': '💬', 'productivity': '✅', 'creative': '🎨', 'memory': '🧠'}
                emoji = agent_emoji.get(message["agent"], '🤖')
                st.caption(f"{emoji} {message['agent'].title()} Agent")
    
    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
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
                    agent_emoji = {'chat': '💬', 'productivity': '✅', 'creative': '🎨', 'memory': '🧠'}
                    emoji = agent_emoji.get(agent_type, '🤖')
                    st.caption(f"{emoji} {agent_type.title()} Agent")
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response,
                        "agent": agent_type
                    })
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")


def task_dashboard():
    st.title("📋 Tasks")
    
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
                st.session_state.db_manager.create_task(
                    user_id=st.session_state.user_id,
                    title=title,
                    description=description,
                    priority=priority,
                    due_date=str(due_date) if due_date else None
                )
                st.success("✅ Task created!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Please enter a task title")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Status", ["all", "pending", "in_progress", "completed"])
    with col2:
        priority_filter = st.selectbox("Priority", ["all", "high", "medium", "low"])
    
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
                if task.description: st.caption(task.description)
                if task.due_date: st.caption(f"📅 {task.due_date}")
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
            page = st.radio("Navigation", ["💬 Chat", "📋 Tasks"], label_visibility="collapsed")
            st.markdown("---")
            
            with st.expander("⚙️ Settings"):
                st.caption(f"Model: {config.DEFAULT_MODEL}")
                if voice_utils.stt_available: st.caption(f"✅ STT: {voice_utils.stt_method}")
                if voice_utils.tts_available: st.caption(f"✅ TTS: {voice_utils.tts_method}")
            
            # --- SAFE LOGOUT LOGIC ---
            if st.button("Logout", use_container_width=True):
                try:
                    # 1. Get cookies safely
                    cookies = st.session_state.cookie_manager.get_all()
                    
                    if cookies and isinstance(cookies, dict):
                        # 2. Delete from DB if token exists
                        token = cookies.get('auth_token')
                        if token:
                            st.session_state.db_manager.delete_session(token)
                        
                        # 3. Delete from Browser (ONLY if key exists)
                        if 'auth_token' in cookies:
                            st.session_state.cookie_manager.delete('auth_token', key="logout_delete")
                except Exception as e:
                    # Log error but proceed with logout
                    print(f"Logout cleanup warning: {e}")
                
                # 4. Clear Local Session State (Critical)
                st.session_state.user = None
                st.session_state.user_id = None
                st.session_state.messages = []
                
                # 5. Rerun to show login page
                st.rerun()
            
            return page
    return "💬 Chat"


def main():
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