"""
Database models for the Multi-Agent AI Personal Assistant.
Defines the schema for users, conversations, memory, and tasks.
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
import json


@dataclass
class User:
    """User model."""
    user_id: Optional[int] = None
    username: str = ""
    created_at: Optional[str] = None
    preferences: Optional[str] = None  # JSON string
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Conversation:
    """Conversation model."""
    conversation_id: Optional[int] = None
    user_id: int = 0
    timestamp: Optional[str] = None
    agent_type: str = ""  # chat, productivity, creative, memory, orchestrator
    message: str = ""
    response: str = ""
    metadata: Optional[str] = None  # JSON string for additional data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Memory:
    """Memory model for storing user context and preferences."""
    memory_id: Optional[int] = None
    user_id: int = 0
    key: str = ""  # e.g., "favorite_color", "communication_style"
    value: str = ""
    context: Optional[str] = None  # Additional context about this memory
    last_updated: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Task:
    """Task model for productivity features."""
    task_id: Optional[int] = None
    user_id: int = 0
    title: str = ""
    description: Optional[str] = None
    priority: str = "medium"  # low, medium, high
    status: str = "pending"  # pending, in_progress, completed, cancelled
    due_date: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class DatabaseSchema:
    """SQL schema definitions."""
    

    # SQLite Schema
    SQLITE_CREATE_USERS_TABLE = """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        preferences TEXT
    )
    """
    
    SQLITE_CREATE_CONVERSATIONS_TABLE = """
    CREATE TABLE IF NOT EXISTS conversations (
        conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        agent_type TEXT NOT NULL,
        message TEXT NOT NULL,
        response TEXT NOT NULL,
        metadata TEXT,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    """
    
    SQLITE_CREATE_MEMORY_TABLE = """
    CREATE TABLE IF NOT EXISTS memory (
        memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        context TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        UNIQUE(user_id, key)
    )
    """
    
    SQLITE_CREATE_TASKS_TABLE = """
    CREATE TABLE IF NOT EXISTS tasks (
        task_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        priority TEXT DEFAULT 'medium',
        status TEXT DEFAULT 'pending',
        due_date TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    """
    
    # PostgreSQL Schema
    POSTGRES_CREATE_USERS_TABLE = """
    CREATE TABLE IF NOT EXISTS users (
        user_id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        preferences TEXT
    )
    """
    
    POSTGRES_CREATE_CONVERSATIONS_TABLE = """
    CREATE TABLE IF NOT EXISTS conversations (
        conversation_id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        agent_type TEXT NOT NULL,
        message TEXT NOT NULL,
        response TEXT NOT NULL,
        metadata TEXT,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    """
    
    POSTGRES_CREATE_MEMORY_TABLE = """
    CREATE TABLE IF NOT EXISTS memory (
        memory_id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        context TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        UNIQUE(user_id, key)
    )
    """
    
    POSTGRES_CREATE_TASKS_TABLE = """
    CREATE TABLE IF NOT EXISTS tasks (
        task_id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        priority TEXT DEFAULT 'medium',
        status TEXT DEFAULT 'pending',
        due_date TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    """
    
    CREATE_INDEXES = [
        "CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_memory_user ON memory(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
    ]
    
    @classmethod
    def get_schema(cls, dialect: str = 'sqlite') -> Dict[str, str]:
        """Get schema queries based on dialect."""
        if dialect == 'postgres':
            return {
                'users': cls.POSTGRES_CREATE_USERS_TABLE,
                'conversations': cls.POSTGRES_CREATE_CONVERSATIONS_TABLE,
                'memory': cls.POSTGRES_CREATE_MEMORY_TABLE,
                'tasks': cls.POSTGRES_CREATE_TASKS_TABLE,
                'indexes': cls.CREATE_INDEXES
            }
        else:
            return {
                'users': cls.SQLITE_CREATE_USERS_TABLE,
                'conversations': cls.SQLITE_CREATE_CONVERSATIONS_TABLE,
                'memory': cls.SQLITE_CREATE_MEMORY_TABLE,
                'tasks': cls.SQLITE_CREATE_TASKS_TABLE,
                'indexes': cls.CREATE_INDEXES
            }
