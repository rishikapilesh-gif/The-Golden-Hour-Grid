from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class WebSocketEvent(BaseModel):
    event_id: str
    event_type: str
    timestamp: datetime
    source: str = "backend"
    is_demo: bool = True
    entity_id: Optional[str] = None
    payload: Dict[str, Any] = {}
