import json
import logging
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any, Optional
import httpx

from backend.app.core.config import settings
from backend.app.schemas.routing import (
    RouteMatrixRequest,
    RouteMatrixResponse,
    RouteMatrixItem,
    DetailedRouteOut,
    TurnStep
)
from backend.app.providers.routing.geo_router import geo_router

logger = logging.getLogger(__name__)


def decode_polyline(polyline_str: str) -> List[Tuple[float, float]]:
    """
    Decodes an encoded polyline that Google Routes API returns into a list of (lat, lon) tuples.
    """
    index, lat, lng = 0, 0, 0
    coordinates = []
    length = len(polyline_str)

    while index < length:
        # Latitude
        shift, result = 0, 0
        while True:
            byte = ord(polyline_str[index]) - 63
            index += 1
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break
        delta_lat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += delta_lat

        # Longitude
        shift, result = 0, 0
        while True:
            byte = ord(polyline_str[index]) - 63
            index += 1
            result |= (byte & 0x1F) << shift
            shift += 5
            if byte < 0x20:
                break
        delta_lng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += delta_lng

        coordinates.append((round(lat / 1e5, 6), round(lng / 1e5, 6)))

    return coordinates


class GoogleRoutesProvider:
    """
    Official Google Routes API integration.
    Uses computeRoutes and computeRouteMatrix with TRAFFIC_AWARE preference.
    Falls back gracefully to GeoRoutingProvider when key is missing or on network timeout.
    """

    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_ROUTES_API_KEY
        self.timeout = settings.GOOGLE_MAPS_TIMEOUT_SECONDS
        self.routing_pref = settings.GOOGLE_MAPS_ROUTING_PREFERENCE or "TRAFFIC_AWARE"

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("CHANGE_ME"))

    async def compute_matrix_async(self, request: RouteMatrixRequest) -> RouteMatrixResponse:
        if not self.is_configured():
            return geo_router.compute_matrix(request)

        url = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "originIndex,destinationIndex,status,condition,distanceMeters,duration,staticDuration"
        }
        body = {
            "origins": [{
                "waypoint": {
                    "location": {
                        "latLng": {
                            "latitude": request.origin_latitude,
                            "longitude": request.origin_longitude
                        }
                    }
                }
            }],
            "destinations": [{
                "waypoint": {
                    "location": {
                        "latLng": {
                            "latitude": dst.latitude,
                            "longitude": dst.longitude
                        }
                    }
                }
            } for dst in request.destinations],
            "travelMode": "DRIVE",
            "routingPreference": self.routing_pref
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, headers=headers, json=body)
                if res.status_code == 200:
                    data = res.json()
                    results = []
                    # Data is a list of matrix elements
                    for item in data:
                        dst_idx = item.get("destinationIndex", 0)
                        if dst_idx < len(request.destinations):
                            dst = request.destinations[dst_idx]
                            dist_meters = item.get("distanceMeters", 0)
                            # duration is string like "1240s"
                            dur_str = item.get("duration", "0s").replace("s", "")
                            dur_secs = float(dur_str) if dur_str else 0.0
                            mins = round(dur_secs / 60.0, 1)

                            results.append(RouteMatrixItem(
                                hospital_id=dst.hospital_id,
                                distance_km=round(dist_meters / 1000.0, 1),
                                duration_minutes=mins,
                                status=item.get("status", {}).get("code", "OK") if isinstance(item.get("status"), dict) else "OK",
                                condition=item.get("condition", "ROUTABLE")
                            ))

                    return RouteMatrixResponse(
                        provider="google_routes_api",
                        computed_at=datetime.now(timezone.utc),
                        traffic_mode="traffic_aware" if self.routing_pref == "TRAFFIC_AWARE" else "traffic_unaware",
                        is_live=True,
                        results=results,
                        warnings=["Live Google Routes matrix computed with traffic awareness."]
                    )
                else:
                    logger.warning(f"Google Routes Matrix returned status {res.status_code}: {res.text}")
                    fallback = geo_router.compute_matrix(request)
                    fallback.warnings.append(f"Google Routes API unavailable (HTTP {res.status_code}); using local road network.")
                    return fallback
        except Exception as e:
            logger.warning(f"Google Routes API matrix request error: {e}")
            fallback = geo_router.compute_matrix(request)
            fallback.warnings.append(f"Google Routes API request error ({str(e)}); using local road network fallback.")
            return fallback

    async def compute_detailed_route_async(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        hospital_id: str,
        hospital_name: str,
        hazards: List[str],
        incident_id: Optional[str] = None
    ) -> DetailedRouteOut:
        if not self.is_configured():
            return geo_router.compute_detailed_route(
                origin, destination, hospital_id, hospital_name, hazards, incident_id
            )

        url = "https://routes.googleapis.com/directions/v2:computeRoutes"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "routes.duration,routes.staticDuration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.description,routes.warnings,routes.legs.steps"
        }
        body = {
            "origin": {
                "location": {
                    "latLng": {
                        "latitude": origin[0],
                        "longitude": origin[1]
                    }
                }
            },
            "destination": {
                "location": {
                    "latLng": {
                        "latitude": destination[0],
                        "longitude": destination[1]
                    }
                }
            },
            "travelMode": "DRIVE",
            "routingPreference": self.routing_pref,
            "computeAlternativeRoutes": True
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, headers=headers, json=body)
                if res.status_code == 200:
                    data = res.json()
                    routes = data.get("routes", [])
                    if not routes:
                        return geo_router.compute_detailed_route(
                            origin, destination, hospital_id, hospital_name, hazards, incident_id
                        )

                    primary_r = routes[0]
                    alt_r = routes[1] if len(routes) > 1 else None

                    dist_meters = primary_r.get("distanceMeters", 0)
                    dur_str = primary_r.get("duration", "0s").replace("s", "")
                    static_str = primary_r.get("staticDuration", "0s").replace("s", "")
                    dur_secs = float(dur_str) if dur_str else 0.0
                    static_secs = float(static_str) if static_str else 0.0

                    poly_enc = primary_r.get("polyline", {}).get("encodedPolyline", "")
                    primary_geom = decode_polyline(poly_enc) if poly_enc else []
                    
                    alt_geom = None
                    if alt_r:
                        alt_poly = alt_r.get("polyline", {}).get("encodedPolyline", "")
                        alt_geom = decode_polyline(alt_poly) if alt_poly else None

                    # Extract steps
                    turn_steps = []
                    legs = primary_r.get("legs", [])
                    if legs:
                        for step in legs[0].get("steps", []):
                            instr = step.get("navigationInstruction", {}).get("instructions", "Proceed along route")
                            s_dist = step.get("distanceMeters", 0)
                            s_dur = float(step.get("staticDuration", "0s").replace("s", "") or 0)
                            turn_steps.append(TurnStep(
                                instruction=instr,
                                distance_meters=s_dist,
                                duration_seconds=s_dur
                            ))

                    warnings = list(primary_r.get("warnings", []))
                    if hazards:
                        warnings.append(f"Operator reported hazards: {', '.join(hazards)}")

                    return DetailedRouteOut(
                        incident_id=incident_id,
                        hospital_id=hospital_id,
                        hospital_name=hospital_name,
                        provider="google_routes_api",
                        computed_at=datetime.now(timezone.utc),
                        traffic_mode="traffic_aware" if self.routing_pref == "TRAFFIC_AWARE" else "traffic_unaware",
                        is_live=True,
                        distance_km=round(dist_meters / 1000.0, 1),
                        duration_minutes=round(dur_secs / 60.0, 1),
                        static_duration_minutes=round(static_secs / 60.0, 1) if static_secs else None,
                        primary_geometry=primary_geom,
                        alternate_geometry=alt_geom,
                        encoded_polyline=poly_enc,
                        turn_by_turn=turn_steps,
                        warnings=warnings,
                        notes=["Live Google Routes API calculation with traffic awareness."]
                    )
                else:
                    logger.warning(f"Google Routes API returned {res.status_code}: {res.text}")
                    fallback = geo_router.compute_detailed_route(
                        origin, destination, hospital_id, hospital_name, hazards, incident_id
                    )
                    fallback.warnings.append(f"Google Routes API unavailable ({res.status_code}); using local road network fallback.")
                    return fallback
        except Exception as e:
            logger.warning(f"Google Routes computeRoutes error: {e}")
            fallback = geo_router.compute_detailed_route(
                origin, destination, hospital_id, hospital_name, hazards, incident_id
            )
            fallback.warnings.append(f"Google Routes API error ({str(e)}); using local road network fallback.")
            return fallback


google_routes_provider = GoogleRoutesProvider()
