from fastapi import WebSocket, APIRouter, WebSocketDisconnect
from app.utils.sockets.broadcast import register_client, unregister_client

router = APIRouter()

@router.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    await register_client(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        unregister_client(websocket)