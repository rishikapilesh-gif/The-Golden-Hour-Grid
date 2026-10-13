from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from backend.app.models.incident import Incident
from backend.app.models.hospital import Hospital
from backend.app.schemas.routing import (
    MapStatusOut,
    RouteMatrixRequest,
    RouteMatrixResponse,
    DetailedRouteOut
)
from backend.app.providers.routing.google_routes import google_routes_provider
from backend.app.providers.routing.geo_router import geo_router

router = APIRouter(tags=["Map & Routing"])

# Default coordinates for named locations if lat/lon not supplied directly
LOCATION_GEO_COORDINATES = {
    "Central Junction": (13.0827, 80.2707),
    "Tech Park": (12.9863, 80.2432),
    "Old Bazaar": (13.0878, 80.2785),
    "Highway Toll": (13.0067, 80.0526),
    "University Gate": (13.0113, 80.2354),
    "Port Junction": (13.0970, 80.2925),
    "North Market": (13.1143, 80.2872),
    "Railway Colony": (13.0833, 80.2348),
    "Riverside Road": (13.0732, 80.2609),
    "East Flyover": (13.0405, 80.2505),
    "South Industrial": (12.9915, 80.1693),
    "Hill Station / Ghat Road": (12.9516, 79.9410)
}


@router.get("/map/status", response_model=MapStatusOut)
def get_map_status(
    current_user: Optional[User] = Depends(get_current_user)
) -> MapStatusOut:
    """
    Returns public/client-safe map configuration.
    Exposes only the client-safe browser key when present; never exposes the secret server key.
    """
    browser_key = settings.GOOGLE_MAPS_BROWSER_API_KEY
    has_browser_key = bool(browser_key and browser_key.strip() and not browser_key.startswith("CHANGE_ME"))
    routes_configured = google_routes_provider.is_configured()

    map_provider = "google" if has_browser_key else "osm"
    routing_provider = "google" if routes_configured else "geo_road_network"

    return MapStatusOut(
        status="ready",
        map_provider=map_provider,
        google_browser_api_key=browser_key if has_browser_key else None,
        routing_provider=routing_provider,
        traffic_aware=routes_configured,
        center={"latitude": 13.06, "longitude": 80.24},
        zoom=13,
        disclaimer="Synthetic demo facilities and routing estimates. Not a certified emergency dispatch system."
    )


@router.post("/routes/matrix", response_model=RouteMatrixResponse)
async def compute_route_matrix(
    request: RouteMatrixRequest,
    current_user: User = Depends(get_current_user)
) -> RouteMatrixResponse:
    """
    Computes a route matrix comparing travel times and distances from an origin to candidate hospitals.
    Uses Google Routes API when configured; otherwise uses real road network Haversine calculations.
    """
    return await google_routes_provider.compute_matrix_async(request)


@router.get("/incidents/{incident_id}/route", response_model=DetailedRouteOut)
async def get_incident_route(
    incident_id: str,
    hospital_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DetailedRouteOut:
    """
    Returns high-detail road geometry, turn-by-turn guidance, and ETA for the incident to a specific hospital.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found"
        )

    # Determine target hospital
    target_hosp_id = hospital_id or incident.selected_hospital_id
    if not target_hosp_id:
        # Default to first accepting hospital
        h_candidate = db.query(Hospital).filter(Hospital.accepting_status == "accepting").first()
        if not h_candidate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No accepting hospital available to route"
            )
        target_hosp_id = h_candidate.id

    hospital = db.query(Hospital).filter(Hospital.id == target_hosp_id).first()
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital '{target_hosp_id}' not found"
        )

    # Resolve origin coords
    if incident.latitude is not None and incident.longitude is not None and -90 <= incident.latitude <= 90:
        origin = (incident.latitude, incident.longitude)
    else:
        origin = LOCATION_GEO_COORDINATES.get(incident.location_label, (13.0827, 80.2707))

    # Resolve destination coords
    if hospital.latitude is not None and hospital.longitude is not None:
        destination = (hospital.latitude, hospital.longitude)
    else:
        destination = (13.0827, 80.2707)

    hazards = list(incident.route_hazards or [])

    return await google_routes_provider.compute_detailed_route_async(
        origin=origin,
        destination=destination,
        hospital_id=hospital.id,
        hospital_name=hospital.name,
        hazards=hazards,
        incident_id=incident.id
    )
