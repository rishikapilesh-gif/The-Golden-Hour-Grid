import uuid
from datetime import datetime, timezone
from typing import Dict, Set, Any
from fastapi import WebSocket
from backend.app.models.user import User


class ConnectionManager:
    def __init__(self):
        # Maps user_id -> set of WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Maps websocket -> user
        self.socket_users: Dict[WebSocket, User] = {}

    async def connect(self, websocket: WebSocket, user: User):
        await websocket.accept()
        if user.id not in self.active_connections:
            self.active_connections[user.id] = set()
        self.active_connections[user.id].add(websocket)
        self.socket_users[websocket] = user

    def disconnect(self, websocket: WebSocket):
        user = self.socket_users.pop(websocket, None)
        if user and user.id in self.active_connections:
            self.active_connections[user.id].discard(websocket)
            if not self.active_connections[user.id]:
                del self.active_connections[user.id]

    async def broadcast_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        entity_id: str | None = None,
        hospital_id: str | None = None,
        source: str = "backend"
    ):
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "is_demo": True,
            "entity_id": entity_id,
            "payload": payload
        }

        # Send to appropriate recipients
        for ws, user in list(self.socket_users.items()):
            should_send = False

            if user.role == "ambulance":
                # Ambulance receives general system/resource/incident updates
                should_send = True
            elif user.role == "hospital":
                # Hospital receives updates relevant to its assigned hospital
                if hospital_id is None or user.hospital_id == hospital_id:
                    should_send = True

            if should_send:
                try:
                    await ws.send_json(event)
                except Exception:
                    self.disconnect(ws)


notifier = ConnectionManager()
