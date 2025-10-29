import sqlite3
from typing import List, Tuple
import time

DB_FILE = "phoebe_memory.db"
MEMORY_LIMIT = 8  # số tin nhắn gần nhất lưu lại

class StateManager:
    def __init__(self, db_file: str = DB_FILE):
        self.conn = sqlite3.connect(db_file)
        self._create_table()

    def _create_table(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS user_memory (
                    user_id TEXT,
                    timestamp INTEGER,
                    role TEXT,
                    content TEXT
                )
            """)

    def add_message(self, user_id: str, role: str, content: str):
        timestamp = int(time.time())
        with self.conn:
            self.conn.execute(
                "INSERT INTO user_memory (user_id, timestamp, role, content) VALUES (?, ?, ?, ?)",
                (user_id, timestamp, role, content)
            )
            self._trim_memory(user_id)

    def _trim_memory(self, user_id: str):
        with self.conn:
            cur = self.conn.execute(
                "SELECT COUNT(*) FROM user_memory WHERE user_id = ?", (user_id,)
            )
            count = cur.fetchone()[0]
            if count > MEMORY_LIMIT:
                to_delete = count - MEMORY_LIMIT
                self.conn.execute(
                    "DELETE FROM user_memory WHERE rowid IN (SELECT rowid FROM user_memory WHERE user_id = ? ORDER BY timestamp ASC LIMIT ?)",
                    (user_id, to_delete)
                )

    def get_memory(self, user_id: str) -> List[Tuple[str, str]]:
        cur = self.conn.execute(
            "SELECT role, content FROM user_memory WHERE user_id = ? ORDER BY timestamp ASC",
            (user_id,)
        )
        return cur.fetchall()

    def clear_memory(self, user_id: str):
        with self.conn:
            self.conn.execute("DELETE FROM user_memory WHERE user_id = ?", (user_id,))
