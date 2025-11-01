import sqlite3
from typing import List, Tuple
import time

# Tên file DB: Cần giữ nguyên để tránh lỗi
DB_FILE = "phoebe_memory.db" 
MEMORY_LIMIT = 8  # Số tin nhắn gần nhất lưu lại (không bao gồm prompt khởi tạo)

class StateManager:
    def __init__(self, db_file: str = DB_FILE):
        # Sử dụng isolation_level=None để tự động commit sau mỗi lệnh
        self.conn = sqlite3.connect(db_file, isolation_level=None) 
        self._create_table()
        print(f"✅ StateManager đã kết nối với SQLite: {db_file}")

    def _create_table(self):
        # Đảm bảo bảng tồn tại
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS user_memory (
                user_id TEXT,
                timestamp INTEGER,
                role TEXT,
                content TEXT
            )
        """)
        # Tạo index để tăng tốc độ truy vấn theo user_id
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON user_memory (user_id)")


    def add_message(self, user_id: str, role: str, content: str):
        timestamp = int(time.time())
        # Thêm tin nhắn
        self.conn.execute(
            "INSERT INTO user_memory (user_id, timestamp, role, content) VALUES (?, ?, ?, ?)",
            (user_id, timestamp, role, content)
        )
        self._trim_memory(user_id) # Cắt bớt lịch sử sau khi thêm

    def _trim_memory(self, user_id: str):
        # Đếm số lượng tin nhắn hiện tại
        cur = self.conn.execute(
            "SELECT COUNT(*) FROM user_memory WHERE user_id = ?", (user_id,)
        )
        count = cur.fetchone()[0]
        
        # Nếu vượt quá giới hạn, xóa các tin nhắn cũ nhất
        if count > MEMORY_LIMIT:
            to_delete = count - MEMORY_LIMIT
            self.conn.execute(
                "DELETE FROM user_memory WHERE rowid IN (SELECT rowid FROM user_memory WHERE user_id = ? ORDER BY timestamp ASC LIMIT ?)",
                (user_id, to_delete)
            )

    def get_memory(self, user_id: str) -> List[Tuple[str, str]]:
        # Trả về lịch sử tin nhắn gần nhất (đã được cắt bớt)
        cur = self.conn.execute(
            "SELECT role, content FROM user_memory WHERE user_id = ? ORDER BY timestamp ASC",
            (user_id,)
        )
        # Trả về format: [('user', 'content A'), ('model', 'content B'), ...]
        return cur.fetchall()

    def clear_memory(self, user_id: str):
        # Xóa toàn bộ lịch sử của người dùng
        self.conn.execute("DELETE FROM user_memory WHERE user_id = ?", (user_id,))