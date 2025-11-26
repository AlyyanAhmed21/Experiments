"""
Multi-Agent AI Personal Assistant - Clean & Simple UI
"""
import streamlit as st
from datetime import datetime
import time
import hashlib
from typing import Optional

from config import config
from database import DatabaseManager
from agents import Orchestrator
from utils import voice_utils


def main():
    """Main application entry point."""
    # Page configuration
    st.set_page_config(
        page_title=config.APP_TITLE,
        page_icon=config.APP_ICON,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    load_css()
    
    # Check configuration
    check_configuration()


def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def load_css():
    """Load custom CSS."""
    st.markdown("""
        <style>
        /* Chat Input Styling */
        .stChatInputContainer {
            padding-bottom: 20px;
        }
        .stChatInputContainer textarea {
            background-color: #2b313e;
            color: #ffffff;
            border: 1px solid #4a4e69;
            border-radius: 15px;
        }
        
        /* Message Bubbles */
        .stChatMessage {
            padding: 1rem;
            border-radius: 15px;
            margin-bottom: 10px;
        }
        
        /* User Message (Right Aligned) */
        div[data-testid="stChatMessage"]:nth-child(odd) {
            background-color: #2b313e;
            border: 1px solid #4a4e69;
        }
        
        /* Assistant Message (Left Aligned) */
        div[data-testid="stChatMessage"]:nth-child(even) {
            background-color: #1e212b;
            border: 1px solid #2b313e;
        }
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #1a1d24;
        }
        </style>
    """, unsafe_allow_html=True)

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
            caption_placeholder = st.empty()
            caption_placeholder.caption("Thinking...")
            
            try:
                # Get streaming generator
                stream_gen = st.session_state.orchestrator.process_message_stream(
                    st.session_state.user_id,
                    prompt
                )
                
                # Handle metadata first (first item is always metadata)
                metadata = next(stream_gen)
                agent_type = metadata.get('primary_agent', 'chat')
                
                agent_emoji = {'chat': '💬', 'productivity': '✅', 'creative': '🎨', 'memory': '🧠'}
                emoji = agent_emoji.get(agent_type, '🤖')
                caption_placeholder.caption(f"{emoji} {agent_type.title()} Agent")
                
                # Wrapper to extract content chunks for st.write_stream
                # and capture full response for history
                full_response_container = {"text": ""}
                
                def content_generator():
                    for item in stream_gen:
                        if item['type'] == 'chunk':
                            full_response_container["text"] += item['content']
                            # Add a tiny delay for smoother reading effect
                            time.sleep(0.02)
                            yield item['content']
                
                # Stream the response
                st.write_stream(content_generator())
                
                # Add to messages
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response_container["text"],
                    "agent": agent_type
                })
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.info("💡 Make sure your Groq API key is valid in the `.env` file")


def sidebar():
    """Sidebar."""
    with st.sidebar:
        st.title("🤖 AI Assistant")
        
        if st.session_state.user:
            st.write(f"**User:** {st.session_state.user.username}")
            
            st.divider()
            
            # User Info Section (instead of empty settings)
            st.caption("ℹ️ Session Info")
            st.info(f"Logged in as: {st.session_state.user.username}")
            
            # Spacer to push logout to bottom
            st.markdown("---")
            # Logout
            if st.button("Logout"):
                st.session_state.user = None
                st.session_state.user_id = None
                st.session_state.messages = []
                st.rerun()
            



def main():
    """Main application."""
    initialize_session_state()
    check_configuration()
    
    if not st.session_state.user:
        login_page()
    else:
        sidebar()
        chat_interface()


if __name__ == "__main__":
    main()
