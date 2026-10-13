from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel


class EtaInfo(BaseModel):
    minutes: float
    source: str
    is_live: bool


class ScoreComponents(BaseModel):
    travel: int
    specialist: int
    icu: int
    er_load: int
    blood_support: int
    freshness: int


class RecommendationOut(BaseModel):
    rank: int
    hospital_id: str
    hospital_name: str
    score: int
    eta: EtaInfo
    distance_km: Optional[float] = None
    components: ScoreComponents
    reasons: List[str]
    warnings: List[str]
    data_freshness: str
    icu_available: int
    er_load: float
    specialist_status: str
    specialist_doctor: Optional[str] = None
    blood_units: int
    eligible: bool = True


class RankingResponse(BaseModel):
    incident_id: str
    ranking_version: str
    computed_at: datetime
    is_demo: bool
    route_provider: str
    recommendations: List[RecommendationOut]
