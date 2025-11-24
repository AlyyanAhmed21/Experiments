import sqlite3
import json
import os
from datetime import datetime

class Memory:
    def __init__(self, db_path="memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for storing session history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT,
                end_time TEXT,
                theme_used TEXT,
                avg_cpu REAL
            )
        ''')
        
        # Table for storing generated content (poems, themes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS creative_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                content_type TEXT,
                content_data TEXT,
                context_snapshot TEXT
            )
        ''')

        # Table for learned preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT,
                confidence REAL
            )
        ''')
        
        conn.commit()
        conn.close()

    def log_session_start(self):
        """Logs the start of a screensaver session."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        start_time = datetime.now().isoformat()
        cursor.execute('INSERT INTO sessions (start_time) VALUES (?)', (start_time,))
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id

    def update_session_end(self, session_id, theme, avg_cpu):
        """Updates the session entry with end time and stats."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        end_time = datetime.now().isoformat()
        cursor.execute('''
            UPDATE sessions 
            SET end_time = ?, theme_used = ?, avg_cpu = ?
            WHERE id = ?
        ''', (end_time, theme, avg_cpu, session_id))
        conn.commit()
        conn.close()

    def save_creative_output(self, content_type, content_data, context):
        """Saves generated art/poetry params."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO creative_history (timestamp, content_type, content_data, context_snapshot)
            VALUES (?, ?, ?, ?)
        ''', (timestamp, content_type, json.dumps(content_data), json.dumps(context)))
        conn.commit()
        conn.close()

    def get_recent_history(self, limit=5):
        """Retrieves recent creative outputs to avoid repetition."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT content_type, content_data FROM creative_history 
            ORDER BY id DESC LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows
