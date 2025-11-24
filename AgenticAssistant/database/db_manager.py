"""
Database manager for the Multi-Agent AI Personal Assistant.
Handles all database operations including CRUD for users, conversations, memory, and tasks.
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import json
from contextlib import contextmanager

from database.models import (
    User, Conversation, Memory, Task, DatabaseSchema
)


class DatabaseManager:
    """Manages all database operations."""
    
    def __init__(self, db_path: str = "data/assistant.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _initialize_database(self):
        """Create tables and indexes if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute(DatabaseSchema.CREATE_USERS_TABLE)
            cursor.execute(DatabaseSchema.CREATE_CONVERSATIONS_TABLE)
            cursor.execute(DatabaseSchema.CREATE_MEMORY_TABLE)
            cursor.execute(DatabaseSchema.CREATE_TASKS_TABLE)
            
            # Create indexes
            for index_sql in DatabaseSchema.CREATE_INDEXES:
                cursor.execute(index_sql)
    
    # ==================== User Operations ====================
    
    def create_user(self, username: str, password_hash: Optional[str] = None, preferences: Optional[Dict] = None) -> User:
        """
        Create a new user.
        
        Args:
            username: Unique username
            password_hash: Hashed password (SHA-256)
            preferences: Optional user preferences dictionary
            
        Returns:
            User object with assigned user_id
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            prefs_json = json.dumps(preferences) if preferences else None
            
            cursor.execute(
                "INSERT INTO users (username, password_hash, preferences) VALUES (?, ?, ?)",
                (username, password_hash, prefs_json)
            )
            
            user_id = cursor.lastrowid
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            
            return User(
                user_id=row['user_id'],
                username=row['username'],
                created_at=row['created_at'],
                preferences=row['preferences']
            )
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            
            if row:
                return User(
                    user_id=row['user_id'],
                    username=row['username'],
                    created_at=row['created_at'],
                    preferences=row['preferences']
                )
            return None
    
    def get_or_create_user(self, username: str, password_hash: Optional[str] = None) -> User:
        """Get existing user or create new one."""
        user = self.get_user_by_username(username)
        if user:
            return user
        return self.create_user(username, password_hash)
    
    def verify_password(self, username: str, password_hash: str) -> bool:
        """Verify user password."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT password_hash FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            
            if row and row['password_hash']:
                return row['password_hash'] == password_hash
            return False
    
    def update_password(self, username: str, password_hash: str) -> bool:
        """Update user password."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (password_hash, username)
            )
            return cursor.rowcount > 0
    
    # ==================== Conversation Operations ====================
    
    def add_conversation(
        self,
        user_id: int,
        agent_type: str,
        message: str,
        response: str,
        metadata: Optional[Dict] = None
    ) -> Conversation:
        """
        Add a conversation entry.
        
        Args:
            user_id: User ID
            agent_type: Type of agent that handled the conversation
            message: User's message
            response: Agent's response
            metadata: Optional metadata dictionary
            
        Returns:
            Conversation object
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute(
                """INSERT INTO conversations 
                   (user_id, agent_type, message, response, metadata)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, agent_type, message, response, metadata_json)
            )
            
            conv_id = cursor.lastrowid
            cursor.execute("SELECT * FROM conversations WHERE conversation_id = ?", (conv_id,))
            row = cursor.fetchone()
            
            return Conversation(
                conversation_id=row['conversation_id'],
                user_id=row['user_id'],
                timestamp=row['timestamp'],
                agent_type=row['agent_type'],
                message=row['message'],
                response=row['response'],
                metadata=row['metadata']
            )
    
    def get_conversation_history(
        self,
        user_id: int,
        limit: int = 50,
        agent_type: Optional[str] = None
    ) -> List[Conversation]:
        """
        Get conversation history for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of conversations to retrieve
            agent_type: Optional filter by agent type
            
        Returns:
            List of Conversation objects
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if agent_type:
                cursor.execute(
                    """SELECT * FROM conversations 
                       WHERE user_id = ? AND agent_type = ?
                       ORDER BY timestamp DESC LIMIT ?""",
                    (user_id, agent_type, limit)
                )
            else:
                cursor.execute(
                    """SELECT * FROM conversations 
                       WHERE user_id = ?
                       ORDER BY timestamp DESC LIMIT ?""",
                    (user_id, limit)
                )
            
            rows = cursor.fetchall()
            conversations = []
            
            for row in rows:
                conversations.append(Conversation(
                    conversation_id=row['conversation_id'],
                    user_id=row['user_id'],
                    timestamp=row['timestamp'],
                    agent_type=row['agent_type'],
                    message=row['message'],
                    response=row['response'],
                    metadata=row['metadata']
                ))
            
            return list(reversed(conversations))  # Return in chronological order
    
    # ==================== Memory Operations ====================
    
    def set_memory(
        self,
        user_id: int,
        key: str,
        value: str,
        context: Optional[str] = None
    ) -> Memory:
        """
        Set or update a memory entry.
        
        Args:
            user_id: User ID
            key: Memory key
            value: Memory value
            context: Optional context
            
        Returns:
            Memory object
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """INSERT INTO memory (user_id, key, value, context)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(user_id, key) 
                   DO UPDATE SET value=?, context=?, last_updated=CURRENT_TIMESTAMP""",
                (user_id, key, value, context, value, context)
            )
            
            cursor.execute(
                "SELECT * FROM memory WHERE user_id = ? AND key = ?",
                (user_id, key)
            )
            row = cursor.fetchone()
            
            return Memory(
                memory_id=row['memory_id'],
                user_id=row['user_id'],
                key=row['key'],
                value=row['value'],
                context=row['context'],
                last_updated=row['last_updated']
            )
    
    def get_memory(self, user_id: int, key: str) -> Optional[Memory]:
        """Get a specific memory entry."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM memory WHERE user_id = ? AND key = ?",
                (user_id, key)
            )
            row = cursor.fetchone()
            
            if row:
                return Memory(
                    memory_id=row['memory_id'],
                    user_id=row['user_id'],
                    key=row['key'],
                    value=row['value'],
                    context=row['context'],
                    last_updated=row['last_updated']
                )
            return None
    
    def get_all_memories(self, user_id: int) -> List[Memory]:
        """Get all memory entries for a user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM memory WHERE user_id = ? ORDER BY last_updated DESC",
                (user_id,)
            )
            rows = cursor.fetchall()
            
            memories = []
            for row in rows:
                memories.append(Memory(
                    memory_id=row['memory_id'],
                    user_id=row['user_id'],
                    key=row['key'],
                    value=row['value'],
                    context=row['context'],
                    last_updated=row['last_updated']
                ))
            
            return memories
    
    # ==================== Task Operations ====================
    
    def create_task(
        self,
        user_id: int,
        title: str,
        description: Optional[str] = None,
        priority: str = "medium",
        due_date: Optional[str] = None
    ) -> Task:
        """
        Create a new task.
        
        Args:
            user_id: User ID
            title: Task title
            description: Optional task description
            priority: Priority level (low, medium, high)
            due_date: Optional due date
            
        Returns:
            Task object
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """INSERT INTO tasks (user_id, title, description, priority, due_date)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, title, description, priority, due_date)
            )
            
            task_id = cursor.lastrowid
            cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            
            return Task(
                task_id=row['task_id'],
                user_id=row['user_id'],
                title=row['title'],
                description=row['description'],
                priority=row['priority'],
                status=row['status'],
                due_date=row['due_date'],
                created_at=row['created_at'],
                completed_at=row['completed_at']
            )
    
    def update_task_status(
        self,
        task_id: int,
        status: str
    ) -> Optional[Task]:
        """Update task status."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            completed_at = datetime.now().isoformat() if status == "completed" else None
            
            cursor.execute(
                "UPDATE tasks SET status = ?, completed_at = ? WHERE task_id = ?",
                (status, completed_at, task_id)
            )
            
            cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            
            if row:
                return Task(
                    task_id=row['task_id'],
                    user_id=row['user_id'],
                    title=row['title'],
                    description=row['description'],
                    priority=row['priority'],
                    status=row['status'],
                    due_date=row['due_date'],
                    created_at=row['created_at'],
                    completed_at=row['completed_at']
                )
            return None
    
    def get_tasks(
        self,
        user_id: int,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[Task]:
        """
        Get tasks for a user with optional filters.
        
        Args:
            user_id: User ID
            status: Optional status filter
            priority: Optional priority filter
            
        Returns:
            List of Task objects
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM tasks WHERE user_id = ?"
            params = [user_id]
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            if priority:
                query += " AND priority = ?"
                params.append(priority)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            tasks = []
            for row in rows:
                tasks.append(Task(
                    task_id=row['task_id'],
                    user_id=row['user_id'],
                    title=row['title'],
                    description=row['description'],
                    priority=row['priority'],
                    status=row['status'],
                    due_date=row['due_date'],
                    created_at=row['created_at'],
                    completed_at=row['completed_at']
                ))
            
            return tasks
    
    def delete_task(self, task_id: int) -> bool:
        """Delete a task."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
            return cursor.rowcount > 0
