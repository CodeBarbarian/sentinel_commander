from fastapi import WebSocket
from typing import List
import json

# Store connected WebSocket clients
connected_clients: List[WebSocket] = []

async def register_client(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)

def unregister_client(websocket: WebSocket):
    if websocket in connected_clients:
        connected_clients.remove(websocket)

async def broadcast_dashboard_event(data: dict):
    message = json.dumps(data)
    dead_clients = []
    for client in connected_clients:
        try:
            await client.send_text(message)
        except Exception:
            dead_clients.append(client)
    for dc in dead_clients:
        unregister_client(dc)
