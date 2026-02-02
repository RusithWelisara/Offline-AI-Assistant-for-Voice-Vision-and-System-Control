import asyncio
import json
import logging
import sqlite3
import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JARVIS_API")

# DB Config
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "jarvis_memory.db")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Connecting to database at: {DB_PATH}")
    yield
    # Shutdown

app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")

manager = ConnectionManager()

def get_latest_events(last_id=0, limit=50):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get events newer than last_known_id
        cursor.execute('''
            SELECT * FROM events 
            WHERE id > ? 
            ORDER BY id ASC 
            LIMIT ?
        ''', (last_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        events = []
        for row in rows:
            events.append({
                "id": row["id"],
                "timestamp": row["timestamp"],
                "type": row["type"],
                "content": row["content"],
                "meta": json.loads(row["meta"]) if row["meta"] else {}
            })
        return events
    except Exception as e:
        logger.error(f"DB Read Error: {e}")
        return []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial state (last 50 logs)
        initial_events = get_latest_events(last_id=0, limit=50) # In reality we might want the LAST 50, but for 'log everything' start fresh or implement fetch history.
        # Actually for a visualizer, we usually want "Recent History".
        # Let's grab the last 50 IDs by descending then reverse them
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM events ORDER BY id DESC LIMIT 1')
        res = cursor.fetchone()
        current_max_id = res[0] if res else 0
        conn.close()

        # initial sync:
        await websocket.send_json({"type": "init", "max_id": current_max_id})

        while True:
            # wait for messages from client (e.g. ping)
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background Poller
async def database_poller():
    last_id = 0
    
    # Initialize last_id to current max to avoid spamming old logs, 
    # OR start from 0 to replay history.
    # For a "Log Everything" visualizer, replaying the last 24h is cool, but let's default to "Live" behavior.
    # We will fetch the max ID at startup.
    try:
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT MAX(id) FROM events")
            row = c.fetchone()
            if row and row[0]:
                # Load last 50 events for context
                last_id = max(0, row[0] - 50)
            conn.close()
    except Exception:
        pass
        
    logger.info(f"Starting poller from ID: {last_id}")

    # Immediately fetch these initial events
    initial_events = get_latest_events(last_id=last_id)
    if initial_events:
        last_id = initial_events[-1]["id"]
        await manager.broadcast(json.dumps({
            "type": "new_events",
            "events": initial_events
        }))

    while True:
        events = get_latest_events(last_id=last_id)
        if events:
            last_id = events[-1]["id"]
            await manager.broadcast(json.dumps({
                "type": "new_events",
                "events": events
            }))
        
        await asyncio.sleep(0.5) # Poll every 500ms

# Startup event to run poller
@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(database_poller())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
