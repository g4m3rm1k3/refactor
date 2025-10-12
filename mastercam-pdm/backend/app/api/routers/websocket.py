"""
WebSocket router for real-time updates.

This module provides:
1. Persistent connections for real-time communication
2. Broadcasting file changes to all connected users
3. Targeted messages to specific users
4. Connection management and cleanup

Architecture:
- ConnectionManager tracks all active WebSocket connections
- Each connection is authenticated via JWT cookie
- When files change, other routers call manager.broadcast()
- All connected clients receive instant updates
"""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from typing import Dict, List
from app.core.security import UserAuth
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.

    Responsibilities:
    - Track all active connections
    - Broadcast messages to all users
    - Send messages to specific users
    - Clean up disconnected clients

    Thread safety: Not currently thread-safe. If using workers > 1,
    you'd need Redis or similar for cross-process communication.
    """

    def __init__(self):
        # Store active connections: {username: websocket}
        # Using dict (not list) so we can identify users by name
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, username: str, websocket: WebSocket):
        """
        Accept a new WebSocket connection and track it.

        Args:
            username: The authenticated user's username
            websocket: The WebSocket connection object

        Note: If user already connected, this replaces their old connection.
        This handles cases where user refreshes page without proper disconnect.
        """
        # Accept the WebSocket handshake
        await websocket.accept()

        # If user already connected (e.g., opened app in two tabs), close old connection
        if username in self.active_connections:
            old_ws = self.active_connections[username]
            try:
                await old_ws.close(code=status.WS_1000_NORMAL_CLOSURE)
            except Exception:
                pass  # Old connection might already be dead

        # Track the new connection
        self.active_connections[username] = websocket
        logger.info(
            f"WebSocket connected: {username} (total: {len(self.active_connections)})")

        # Notify all users that someone connected
        await self.broadcast({
            "type": "user_connected",
            "username": username,
            "timestamp": datetime.utcnow().isoformat()
        })

    def disconnect(self, username: str):
        """
        Remove a user's connection from tracking.

        Args:
            username: The user who disconnected

        Note: This doesn't close the connection (that's already happened),
        it just removes it from our tracking dict.
        """
        if username in self.active_connections:
            del self.active_connections[username]
            logger.info(
                f"WebSocket disconnected: {username} (remaining: {len(self.active_connections)})")

    async def send_personal_message(self, username: str, message: dict):
        """
        Send a message to a specific user.

        Args:
            username: Target user
            message: Dict that will be JSON-serialized

        Use cases:
        - Admin sends a message to one user
        - Notify user their checkout succeeded
        - User-specific notifications
        """
        if username in self.active_connections:
            websocket = self.active_connections[username]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to {username}: {e}")
                # Connection might be dead, remove it
                self.disconnect(username)

    async def broadcast(self, message: dict, exclude: List[str] = None):
        """
        Send a message to all connected users.

        Args:
            message: Dict that will be JSON-serialized
            exclude: List of usernames to NOT send to (optional)

        Use cases:
        - File was checked out -> notify everyone
        - File was checked in -> notify everyone
        - New file added -> notify everyone

        Note: If sending fails to a user, we remove their connection.
        This handles "zombie" connections that appear alive but aren't.
        """
        exclude = exclude or []

        # Build list of users to notify
        recipients = [
            username for username in self.active_connections.keys()
            if username not in exclude
        ]

        # Send to each recipient
        # We iterate over a copy of the keys because we might remove dead connections
        dead_connections = []
        for username in recipients:
            websocket = self.active_connections[username]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to {username}: {e}")
                dead_connections.append(username)

        # Clean up dead connections
        for username in dead_connections:
            self.disconnect(username)

        logger.debug(
            f"Broadcast to {len(recipients)} users: {message.get('type', 'unknown')}")

    def get_connected_users(self) -> List[str]:
        """
        Get list of currently connected usernames.

        Returns:
            List of usernames

        Useful for:
        - Dashboard showing who's online
        - Admin features
        - Debugging
        """
        return list(self.active_connections.keys())


# Create a single instance of the manager
# All WebSocket connections share this manager
manager = ConnectionManager()


async def get_current_user_from_ws(websocket: WebSocket) -> dict | None:
    """
    Dependency to authenticate WebSocket connections.

    Reads JWT from cookie, validates it, and returns user payload.
    If anything fails, closes the WebSocket with appropriate error code.

    Args:
        websocket: The WebSocket connection being authenticated

    Returns:
        User payload dict (with 'sub' for username) or None if auth failed

    WebSocket close codes used:
        1008 (Policy Violation): Authentication failed
        1011 (Internal Error): Server not properly configured
    """
    # 1. Extract JWT from cookie
    token = websocket.cookies.get("auth_token")
    if not token:
        logger.warning("WebSocket connection attempt without auth token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    # 2. Get the auth service from app state
    auth_service: UserAuth = websocket.app.state.user_auth
    if not auth_service:
        # This means GitLab isn't configured or service failed to initialize
        logger.error("UserAuth service not initialized - WebSocket rejected")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return None

    # 3. Verify the token
    payload = auth_service.verify_token(token)
    if not payload:
        logger.warning("Invalid token in WebSocket connection attempt")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None

    return payload


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user: dict = Depends(get_current_user_from_ws)
):
    """
    WebSocket endpoint for real-time updates.

    Flow:
    1. Client connects with JWT cookie
    2. Auth dependency validates token
    3. Connection accepted and tracked
    4. Client can send/receive messages
    5. On disconnect, cleanup happens

    Message types FROM client:
        - ping: Keep-alive
        - request_update: Request fresh file list

    Message types TO client:
        - file_locked: Someone checked out a file
        - file_unlocked: Someone checked in a file
        - file_deleted: Admin deleted a file
        - user_connected: Someone connected
        - user_disconnected: Someone disconnected
        - pong: Response to ping
    """
    # If auth failed, dependency returns None and closes connection
    if not user:
        return

    username = user.get("sub", "unknown")

    # Connect and track this user
    await manager.connect(username, websocket)

    try:
        # Main message loop - wait for messages from client
        while True:
            # Receive message from client (as JSON)
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                message_type = message.get("type", "unknown")

                # Handle different message types
                if message_type == "ping":
                    # Client is checking if we're alive
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })

                elif message_type == "request_update":
                    # Client wants a fresh file list
                    # We could fetch and send it here, or just acknowledge
                    await websocket.send_json({
                        "type": "update_requested",
                        "message": "Refresh your file list via API"
                    })

                else:
                    logger.warning(
                        f"Unknown message type from {username}: {message_type}")

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from {username}: {data}")

    except WebSocketDisconnect:
        # Client disconnected (normal or abnormal)
        manager.disconnect(username)

        # Notify other users
        await manager.broadcast({
            "type": "user_disconnected",
            "username": username,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        # Unexpected error - log it and clean up
        logger.error(f"WebSocket error for {username}: {e}", exc_info=True)
        manager.disconnect(username)


# Helper function for other routers to broadcast updates
async def broadcast_file_update(event_type: str, file_data: dict):
    """
    Broadcast a file update to all connected users.

    This function is called by other routers (files.py, admin.py)
    when something changes.

    Args:
        event_type: Type of event (file_locked, file_unlocked, etc.)
        file_data: Information about the file that changed

    Example usage in files.py:
        from app.api.routers.websocket import broadcast_file_update

        # After checking out a file:
        await broadcast_file_update("file_locked", {
            "filename": filename,
            "locked_by": username,
            "timestamp": datetime.utcnow().isoformat()
        })
    """
    await manager.broadcast({
        "type": event_type,
        "data": file_data,
        "timestamp": datetime.utcnow().isoformat()
    })
