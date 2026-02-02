# JARVIS Visual Interface

This directory contains a **Three.js powered 3D Visualizer** for JARVIS's memory and activity logs.

## 🚀 How to Run

Simply run the startup script in the root directory:

```
start_visualizer.bat
```

This will:
1. Start the **FastAPI Bridge** (`jarvis_core/core/api_server.py`) which exposes `jarvis_memory.db` over WebSockets.
2. Start the **Vite/React Frontend** (`web_interface/`).
3. Open your browser to `http://localhost:5173`.

## 🛠 Architecture

- **Backend**: Python/FastAPI (`port 8000`)
  - Polls `jarvis_memory.db` for changes.
  - Broadcasts new events via WebSocket.
  
- **Frontend**: React + Three.js + Fiber (`port 5173`)
  - **Sci-Fi HUD**: Pure HTML/CSS overlay.
  - **3D Stream**: A timeline of nodes representing User inputs, AI responses, and Tool usage.
  - **Visuals**: Bloom effects, dark mode aesthetics.

## 🎨 Controls

- **Left Click + Drag**: Rotate View
- **Right Click + Drag**: Pan View
- **Scroll**: Zoom
- **Click Event Node**: Open Details Panel
