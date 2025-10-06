# backend/app/api/routers/websocket.py
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from app.core.security import UserAuth  # Import UserAuth for type hinting
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# A temporary connection manager


class ConnectionManager:
    async def connect(self, websocket: WebSocket):
        await websocket.accept()

    def disconnect(self, websocket: WebSocket):
        pass


manager = ConnectionManager()

# This is our new, corrected dependency that works specifically for WebSockets


async def get_current_user_from_ws(websocket: WebSocket) -> dict | None:
    """Dependency to get user from cookie for WebSockets."""
    token = websocket.cookies.get("auth_token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    # CORRECT WAY TO GET THE SERVICE: from the shared app state
    auth_service: UserAuth = websocket.app.state.user_auth
    if not auth_service:
        logger.error("UserAuth service not initialized.")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return None

    payload = auth_service.verify_token(token)
    if not payload:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    return payload


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user: dict = Depends(get_current_user_from_ws)  # Use our new dependency
):
    if not user:
        return

    username = user.get("sub", "unknown")
    await manager.connect(websocket)
    logger.info(f"WebSocket connected for user: {username}")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket disconnected for user: {username}")
