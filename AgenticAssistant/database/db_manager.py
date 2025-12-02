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


try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

class DatabaseManager:
    """Manages all database operations."""
    
    def __init__(self, db_path: str = "data/assistant.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file (fallback)
        """
        self.db_url = os.getenv("DATABASE_URL")
        self.db_path = db_path
        self.dialect = 'postgres' if self.db_url and HAS_POSTGRES else 'sqlite'
        
        if self.dialect == 'sqlite':
            # Ensure data directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
        self._initialize_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        if self.dialect == 'postgres':
            conn = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
            
    def execute_query(self, cursor, query: str, params: tuple = ()):
        """Execute query handling dialect differences."""
        if self.dialect == 'postgres':
            # Convert ? to %s for Postgres
            query = query.replace('?', '%s')
        cursor.execute(query, params)
        return cursor
    
    def _initialize_database(self):
        """Create tables and indexes if they don't exist."""
        schema = DatabaseSchema.get_schema(self.dialect)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create tables
            self.execute_query(cursor, schema['users'])
            self.execute_query(cursor, schema['conversations'])
            self.execute_query(cursor, schema['memory'])
            self.execute_query(cursor, schema['tasks'])
            
            # Create indexes
            for index_sql in schema['indexes']:
                self.execute_query(cursor, index_sql)

    
    # ==================== User Operations ====================
    
    def create_user(self, username: str, password_hash: Optional[str] = None, preferences: Optional[Dict] = None) -> User:
        """Create a new user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            prefs_json = json.dumps(preferences) if preferences else None
            
            if self.dialect == 'postgres':
                self.execute_query(
                    cursor,
                    "INSERT INTO users (username, password_hash, preferences) VALUES (?, ?, ?) RETURNING user_id",
                    (username, password_hash, prefs_json)
                )
                user_id = cursor.fetchone()['user_id']
            else:
                self.execute_query(
                    cursor,
                    "INSERT INTO users (username, password_hash, preferences) VALUES (?, ?, ?)",
                    (username, password_hash, prefs_json)
                )
                user_id = cursor.lastrowid
            
            self.execute_query(cursor, "SELECT * FROM users WHERE user_id = ?", (user_id,))
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
            self.execute_query(cursor, "SELECT * FROM users WHERE username = ?", (username,))
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
        """Add a conversation entry."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            metadata_json = json.dumps(metadata) if metadata else None
            
            if self.dialect == 'postgres':
                self.execute_query(
                    cursor,
                    """INSERT INTO conversations 
                       (user_id, agent_type, message, response, metadata)
                       VALUES (?, ?, ?, ?, ?) RETURNING conversation_id""",
                    (user_id, agent_type, message, response, metadata_json)
                )
                conv_id = cursor.fetchone()['conversation_id']
            else:
                self.execute_query(
                    cursor,
                    """INSERT INTO conversations 
                       (user_id, agent_type, message, response, metadata)
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, agent_type, message, response, metadata_json)
                )
                conv_id = cursor.lastrowid
            
            self.execute_query(cursor, "SELECT * FROM conversations WHERE conversation_id = ?", (conv_id,))
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
        """Get conversation history for a user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if agent_type:
                self.execute_query(
                    cursor,
                    """SELECT * FROM conversations 
                       WHERE user_id = ? AND agent_type = ?
                       ORDER BY timestamp DESC LIMIT ?""",
                    (user_id, agent_type, limit)
                )
            else:
                self.execute_query(
                    cursor,
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
        """Set or update a memory entry."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.dialect == 'postgres':
                self.execute_query(
                    cursor,
                    """INSERT INTO memory (user_id, key, value, context)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(user_id, key)
                       DO UPDATE SET value=EXCLUDED.value, context=EXCLUDED.context, last_updated=CURRENT_TIMESTAMP""",
                    (user_id, key, value, context)
                )
            else:
                self.execute_query(
                    cursor,
                    """INSERT INTO memory (user_id, key, value, context)
                       VALUES (?, ?, ?, ?)
                       ON CONFLICT(user_id, key)
                       DO UPDATE SET value=?, context=?, last_updated=CURRENT_TIMESTAMP""",
                    (user_id, key, value, context, value, context)
                )
                
            self.execute_query(
                cursor,
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

    # ---------------------------------------------------------------------
    # Game state persistence helpers (used by CreativeAgent)
    # ---------------------------------------------------------------------
    def set_game_state(self, user_id: int, state: dict) -> bool:
        """Store a JSON‑serialised game state for a user.

        The state is saved in the generic ``memory`` table under a reserved
        key ``__creative_game_state``. Returns ``True`` if the operation
        succeeded.
        """
        import json
        state_json = json.dumps(state)
        # Use the existing ``set_memory`` logic – context indicates purpose
        self.set_memory(user_id, "__creative_game_state", state_json, context="game_state")
        return True

    def get_game_state(self, user_id: int) -> dict | None:
        """Retrieve the persisted game state for a user.

        Returns the deserialised ``dict`` or ``None`` if no state is stored.
        """
        import json
        mem = self.get_memory(user_id, "__creative_game_state")
        if mem and mem.value:
            try:
                return json.loads(mem.value)
            except json.JSONDecodeError:
                return None
        return None
    
    def get_memory(self, user_id: int, key: str) -> Optional[Memory]:
        """Get a specific memory entry."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            self.execute_query(
                cursor,
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
            self.execute_query(
                cursor,
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
        """Create a new task."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if self.dialect == 'postgres':
                self.execute_query(
                    cursor,
                    """INSERT INTO tasks (user_id, title, description, priority, due_date)
                       VALUES (?, ?, ?, ?, ?) RETURNING task_id""",
                    (user_id, title, description, priority, due_date)
                )
                task_id = cursor.fetchone()['task_id']
            else:
                self.execute_query(
                    cursor,
                    """INSERT INTO tasks (user_id, title, description, priority, due_date)
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, title, description, priority, due_date)
                )
                task_id = cursor.lastrowid
            
            self.execute_query(cursor, "SELECT * FROM tasks WHERE task_id = ?", (task_id,))
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
            
            self.execute_query(
                cursor,
                "UPDATE tasks SET status = ?, completed_at = ? WHERE task_id = ?",
                (status, completed_at, task_id)
            )
            
            self.execute_query(cursor, "SELECT * FROM tasks WHERE task_id = ?", (task_id,))
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
        """Get tasks for a user with optional filters."""
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
            
            self.execute_query(cursor, query, tuple(params))
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
            self.execute_query(cursor, "DELETE FROM tasks WHERE task_id = ?", (task_id,))
            return cursor.rowcount > 0
