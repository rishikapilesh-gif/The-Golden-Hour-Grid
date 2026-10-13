from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class MapStatusOut(BaseModel):
    status: str = "ready"
    map_provider: str  # "google" | "osm"
    google_browser_api_key: Optional[str] = None
    routing_provider: str  # "google" | "osrm" | "geo_router" | "demo_router"
    traffic_aware: bool = False
    center: Dict[str, float] = Field(default_factory=lambda: {"latitude": 13.06, "longitude": 80.24})
    zoom: int = 13
    disclaimer: str = "Synthetic demo facilities and routing estimates. Not a certified emergency dispatch system."


class RouteMatrixDestination(BaseModel):
    hospital_id: str
    latitude: float
    longitude: float


class RouteMatrixRequest(BaseModel):
    origin_latitude: float
    origin_longitude: float
    destinations: List[RouteMatrixDestination]
    hazards: List[str] = Field(default_factory=list)


class RouteMatrixItem(BaseModel):
    hospital_id: str
    distance_km: float
    duration_minutes: float
    status: str = "OK"  # "OK" | "NOT_FOUND" | "ZERO_RESULTS"
    condition: str = "ROUTABLE"  # "ROUTABLE" | "HAZARD_PENALTY"


class RouteMatrixResponse(BaseModel):
    provider: str
    computed_at: datetime
    traffic_mode: str  # "traffic_aware" | "traffic_unaware"
    is_live: bool = False
    results: List[RouteMatrixItem]
    warnings: List[str] = Field(default_factory=list)


class TurnStep(BaseModel):
    instruction: str
    distance_meters: float
    duration_seconds: float


class DetailedRouteOut(BaseModel):
    incident_id: Optional[str] = None
    hospital_id: str
    hospital_name: str
    provider: str
    computed_at: datetime
    traffic_mode: str
    is_live: bool = False
    distance_km: float
    duration_minutes: float
    static_duration_minutes: Optional[float] = None
    primary_geometry: List[Tuple[float, float]]  # List of (latitude, longitude)
    alternate_geometry: Optional[List[Tuple[float, float]]] = None
    encoded_polyline: Optional[str] = None
    turn_by_turn: List[TurnStep] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
