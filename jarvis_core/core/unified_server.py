import asyncio
import json
import logging
import sqlite3
import os
import sys
from contextlib import asynccontextmanager
from typing import List
from pydantic import BaseModel

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from jarvis_core.config import Config
from jarvis_core.core.event_bus import EventBus
from jarvis_core.core.autonomy_loop import AutonomyLoop

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JARVIS_UNIFIED")

# DB Config
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "jarvis_memory.db")

# Global instances
event_bus = None
autonomy = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global event_bus, autonomy
    logger.info("Starting JARVIS Unified Server...")
    
    # Initialize Core Components
    config = Config()
    event_bus = EventBus()
    autonomy = AutonomyLoop(event_bus)
    
    # Start Autonomy Loop in Background
    # We use asyncio.create_task to let it run concurrently with the API
    loop_task = asyncio.create_task(autonomy.start())
    
    logger.info(f"Connecting to database at: {DB_PATH}")
    asyncio.create_task(database_poller())
    
    yield
    # Shutdown logic if needed

app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- WebSocket & Database Logic (from api_server.py) ---

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
        # Initial sync logic
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(id) FROM events')
        res = cursor.fetchone()
        max_id = res[0] if res and res[0] else 0
        conn.close()
        
        await websocket.send_json({"type": "init", "max_id": max_id})

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def database_poller():
    last_id = 0
    try:
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT MAX(id) FROM events")
            row = c.fetchone()
            if row and row[0]:
                last_id = max(0, row[0] - 50) # Rewind 50
            conn.close()
    except Exception:
        pass
        
    logger.info(f"Starting poller from ID: {last_id}")

    # Immediate push
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
        
        await asyncio.sleep(0.5)

# --- New Interaction Logic ---

class InteractRequest(BaseModel):
    text: str
    source: str = "web_interface"

@app.post("/api/interact")
async def interact(request: InteractRequest):
    """
    Injects user input directly into JARVIS's Event Bus,
    emulating a voice command but from text.
    """
    if not event_bus:
        raise HTTPException(status_code=503, detail="JARVIS Core not initialized yet")
        
    logger.info(f"Web Interaction: {request.text}")
    
    # Publish to 'user_speech' just like the microphone would
    await event_bus.publish("user_speech", {
        "text": request.text,
        "source": request.source,
        "cycle_start_time": asyncio.get_event_loop().time()
    })
    
    return {"status": "ok", "message": "Input processed"}

if __name__ == "__main__":
    import uvicorn
    # Important: Run single process to share memory space with AutonomyLoop
    uvicorn.run(app, host="0.0.0.0", port=8000)
