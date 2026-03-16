from fastapi import APIRouter, WebSocket

from app.logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)


connection_manager = ConnectionManager()

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        connection_manager.disconnect(websocket)
