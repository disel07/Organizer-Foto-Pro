import sqlite3
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any

class SessionDatabase:
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._local = threading.local()
        self._init_db()

    def _get_conn(self):
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        # Enable WAL (Write-Ahead Logging) for concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        
        # Table for files found during scan
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_path TEXT UNIQUE,
                file_name TEXT,
                file_size INTEGER,
                file_hash TEXT,
                mime_type TEXT,
                date_taken TEXT,
                date_source TEXT,
                dest_path TEXT,
                status TEXT DEFAULT 'pending', -- pending, skipped, copied, verified, error
                error_msg TEXT
            )
        """)
        
        # Table for summary stats
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                key TEXT PRIMARY KEY,
                value INTEGER
            )
        """)
        
        conn.commit()
        conn.close()

    def add_file(self, path: str, name: str, size: int, mime: str = "unknown"):
        conn = self._get_conn()
        retries = 5
        while retries > 0:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO files (source_path, file_name, file_size, mime_type)
                    VALUES (?, ?, ?, ?)
                """, (path, name, size, mime))
                conn.commit()
                return
            except sqlite3.OperationalError as e:
                if "locked" in str(e):
                    retries -= 1
                    import time
                    time.sleep(0.1)
                else:
                    print(f"DB Error add_file: {e}")
                    break
            except sqlite3.Error as e:
                print(f"DB Error add_file: {e}")
                break

    def update_metadata(self, source_path: str, date_taken: str, date_source: str, file_hash: str = None):
        conn = self._get_conn()
        updates = ["date_taken = ?", "date_source = ?"]
        params = [date_taken, date_source]
        
        if file_hash:
            updates.append("file_hash = ?")
            params.append(file_hash)
            
        params.append(source_path)
        
        sql = f"UPDATE files SET {', '.join(updates)} WHERE source_path = ?"
        conn.execute(sql, params)
        conn.commit()

    def set_destination(self, source_path: str, dest_path: str):
        conn = self._get_conn()
        conn.execute("UPDATE files SET dest_path = ? WHERE source_path = ?", (dest_path, source_path))
        conn.commit()

    def update_status(self, source_path: str, status: str, error_msg: str = None):
        conn = self._get_conn()
        conn.execute("UPDATE files SET status = ?, error_msg = ? WHERE source_path = ?", 
                     (status, error_msg, source_path))
        conn.commit()

    def get_all_files(self) -> List[sqlite3.Row]:
        conn = self._get_conn()
        return conn.execute("SELECT * FROM files").fetchall()

    def get_pending_files(self) -> List[sqlite3.Row]:
        conn = self._get_conn()
        return conn.execute("SELECT * FROM files WHERE status = 'pending'").fetchall()
        
    def get_stats(self) -> Dict[str, int]:
        conn = self._get_conn()
        total = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        processed = conn.execute("SELECT COUNT(*) FROM files WHERE status IN ('copied', 'verified')").fetchone()[0]
        errors = conn.execute("SELECT COUNT(*) FROM files WHERE status = 'error'").fetchone()[0]
        size = conn.execute("SELECT SUM(file_size) FROM files").fetchone()[0] or 0
        return {
            "total_files": total,
            "processed": processed,
            "errors": errors,
            "total_size_bytes": size
        }

    def close(self):
        if hasattr(self._local, "conn"):
            self._local.conn.close()
