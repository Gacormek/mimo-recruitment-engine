"""WebSocket handler for real-time dashboard updates."""
import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set

_connections: Set[WebSocket] = set()


async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for the dashboard."""
    await websocket.accept()
    _connections.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data) if data else {}
            
            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg.get("type") == "status":
                from .routes import kernel
                status = kernel.get_status() if kernel else {}
                await websocket.send_json({"type": "status", "data": status})
    except WebSocketDisconnect:
        _connections.discard(websocket)
    except Exception:
        _connections.discard(websocket)


async def broadcast(event_type: str, data: dict):
    """Broadcast an event to all connected WebSocket clients."""
    if not _connections:
        return
    message = json.dumps({"type": event_type, "data": data})
    dead = set()
    for ws in _connections:
        try:
            await ws.send_text(message)
        except Exception:
            dead.add(ws)
    _connections.difference_update(dead)
