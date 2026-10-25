import os
import sqlite3
from typing import Dict, Any, List, Optional

class DatabaseManager:
    """Manages the SQLite database for storing settings, reminders, and sticky notes."""

    def __init__(self, db_path: str = "kitty_ai.db"):
        self.db_path = db_path
        self._initialize_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Helper to create and return a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _initialize_db(self) -> None:
        """Create tables if they do not exist."""
        # Ensure the parent directory of the database file exists
        parent_dir = os.path.dirname(self.db_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Reminders Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    due_time TEXT NOT NULL,
                    completed INTEGER DEFAULT 0
                )
            """)

            # 2. Sticky Notes Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sticky_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT,
                    x INTEGER DEFAULT 100,
                    y INTEGER DEFAULT 100,
                    color TEXT DEFAULT '#ffeb3b'
                )
            """)

            # 3. Settings Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            # Default settings
            defaults = {
                "user_name": "human",
                "pet_skin": "black",
                "pet_scale": "100",
                "custom_fur_enabled": "false",
                "body_color": "#111111",
                "belly_color": "#222222",
                "eye_color": "#ffeb3b",
                "pattern_type": "none",
                "pattern_color": "#444444",
                "sound_enabled": "true",
                "volume": "80",
                "personality_style": "default",
                "ai_api_enabled": "false",
                "ai_provider": "openai",
                "ai_api_key": "",
                "ai_base_url": "https://api.openai.com/v1",
                "ai_model": "gpt-4o-mini",
                "ai_temperature": "0.7",
                "click_action": "hud"
            }
            for k, v in defaults.items():
                cursor.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)", (k, v))
            
            conn.commit()

    def get_setting(self, key: str, default: str = "") -> str:
        """Retrieve a specific setting."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            val = row[0] if row else default
            return val if val is not None else default

    def set_setting(self, key: str, value: str) -> None:
        """Update or insert a setting key-value pair."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO app_settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, value))
            conn.commit()

    def get_all_reminders(self) -> List[Dict[str, Any]]:
        """Retrieve all registered reminders."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reminders")
            return [dict(row) for row in cursor.fetchall()]

    def add_reminder(self, title: str, due_time: str) -> int:
        """Insert a new reminder."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO reminders (title, due_time, completed) VALUES (?, ?, 0)",
                (title, due_time)
            )
            conn.commit()
            return cursor.lastrowid or 0

    def delete_reminder(self, reminder_id: int) -> None:
        """Delete a reminder by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
            conn.commit()

    def get_all_notes(self) -> List[Dict[str, Any]]:
        """Retrieve all sticky notes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sticky_notes")
            return [dict(row) for row in cursor.fetchall()]

    def add_note(self, content: str, x: int, y: int, color: str) -> int:
        """Insert a new sticky note."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sticky_notes (content, x, y, color) VALUES (?, ?, ?, ?)",
                (content, x, y, color)
            )
            conn.commit()
            return cursor.lastrowid or 0

    def update_note(self, note_id: int, content: str, x: int, y: int) -> None:
        """Update coordinates and content of an existing note."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sticky_notes SET content = ?, x = ?, y = ? WHERE id = ?",
                (content, x, y, note_id)
            )
            conn.commit()

    def delete_note(self, note_id: int) -> None:
        """Delete a sticky note by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sticky_notes WHERE id = ?", (note_id,))
            conn.commit()
