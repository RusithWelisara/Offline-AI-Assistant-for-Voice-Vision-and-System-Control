from collections import deque
import time
import logging
import sqlite3
import json
import os

logger = logging.getLogger(__name__)

class WorkingMemory:
    def __init__(self, max_events=30, db_path="jarvis_memory.db"):
        self.events = deque(maxlen=max_events)
        self.db_path = db_path
        self.max_events = max_events
        
        self._init_db()
        self._load_from_db()
        
        logger.info(f"WorkingMemory initialized with size {max_events}. Loaded from {db_path}.")

    def _init_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    type TEXT,
                    content TEXT,
                    meta TEXT
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to initialize memory DB: {e}")

    def _load_from_db(self):
        """Load recent events from DB into deque."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get last N events. We need to order by timestamp desc limit N, then reverse for deque
            cursor.execute(f'''
                SELECT * FROM events 
                ORDER BY timestamp DESC 
                LIMIT {self.max_events}
            ''')
            rows = cursor.fetchall()
            conn.close()
            
            # Rows are newest first. We need to insert oldest first into deque.
            for row in reversed(rows):
                event = {
                    "timestamp": row["timestamp"],
                    "type": row["type"],
                    "content": row["content"],
                    "meta": json.loads(row["meta"]) if row["meta"] else {}
                }
                self.events.append(event)
                
        except Exception as e:
            logger.error(f"Failed to load memory from DB: {e}")

    def add(self, event_type, content, meta=None):
        """
        Add an event to memory and persist to DB.
        """
        timestamp = time.time()
        meta_dict = meta or {}
        
        event = {
            "timestamp": timestamp,
            "type": event_type,
            "content": content,
            "meta": meta_dict
        }
        
        self.events.append(event)
        
        # Persist
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO events (timestamp, type, content, meta)
                VALUES (?, ?, ?, ?)
            ''', (timestamp, event_type, content, json.dumps(meta_dict)))
            conn.commit()
            conn.close()
            logger.debug(f"MEMORY PERSIST: {event_type}")
        except Exception as e:
            logger.error(f"Failed to persist event to DB: {e}")

    def recent(self, n=5):
        """Return the n most recent events."""
        return list(self.events)[-n:]

    def get_context_string(self, n=10):
        """Returns a formatted string of recent events for LLM context."""
        context = []
        for event in self.recent(n):
            # Format: [Type] Content
            context.append(f"[{event['type']}] {event['content']}")
        return "\n".join(context)

    def clear(self):
        """Clear all events from memory (both in-memory and database)."""
        try:
            # Clear in-memory events
            self.events.clear()
            
            # Clear database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM events')
            conn.commit()
            conn.close()
            
            logger.info(f"Memory cleared: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")