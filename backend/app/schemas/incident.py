from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict

VALID_BLOOD_GROUPS = {"O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"}
VALID_INJURIES = {"trauma", "neuro", "cardiac", "ortho", "burns"}


class LocationInput(BaseModel):
    label: str = Field(..., min_length=1, max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class VitalsInput(BaseModel):
    heart_rate_bpm: Optional[int] = Field(None, ge=0, le=300)
    spo2_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    pao2_mmhg: Optional[float] = Field(None, ge=0.0, le=700.0)
    observed_at: Optional[datetime] = None


class IncidentCreate(BaseModel):
    location: LocationInput
    injury_category: str = Field(..., min_length=1, max_length=50)
    incident_source: str = Field("Other / unknown", max_length=100)
    gender: str = Field("Unknown", max_length=30)
    reported_priority: str = Field("High", max_length=30)
    witness_assessment: str = Field("Unknown", max_length=30)
    vitals: Optional[VitalsInput] = None
    reported_blood_group: str = Field("O-", max_length=10)
    blood_group_verified: bool = False
    route_hazards: List[str] = Field(default_factory=list)

    @field_validator("reported_blood_group")
    @classmethod
    def validate_blood_group(cls, v: str) -> str:
        clean = v.strip().upper()
        if clean not in VALID_BLOOD_GROUPS:
            raise ValueError(f"Invalid reported blood group: {v}. Must be one of {sorted(VALID_BLOOD_GROUPS)}")
        return clean

    @field_validator("injury_category")
    @classmethod
    def validate_injury(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in VALID_INJURIES:
            raise ValueError(f"Invalid injury category: {v}. Must be one of {sorted(VALID_INJURIES)}")
        return clean


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    location_label: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    injury_category: str
    incident_source: str
    gender: str
    reported_priority: str
    witness_assessment: str
    vitals: VitalsInput
    reported_blood_group: str
    blood_group_verified: bool
    route_hazards: List[str]
    status: str
    selected_hospital_id: Optional[str] = None
    override_reason: Optional[str] = None
    is_demo: bool
    created_at: datetime
    updated_at: datetime


class SelectHospitalRequest(BaseModel):
    hospital_id: str = Field(..., min_length=1)
    override_reason: Optional[str] = Field(None, max_length=500)


class StatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(created|triaged_by_dispatch|hospital_selected|en_route|near_hospital|handover_complete|cancelled)$")
