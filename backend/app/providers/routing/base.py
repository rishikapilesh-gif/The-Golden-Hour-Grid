from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
from pydantic import BaseModel


class PathAlternative(BaseModel):
    path: List[Tuple[float, float]]
    eta_minutes: float
    distance_km: float
    tags: List[str]
    is_blocked: bool = False


class RouteResult(BaseModel):
    primary: PathAlternative
    alternate: PathAlternative
    provider: str
    is_live: bool = False
    notes: List[str] = []


class RoutingProvider(ABC):
    @abstractmethod
    def estimate_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        hazards: List[str],
        origin_label: str = ""
    ) -> RouteResult:
        pass
