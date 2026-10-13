from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class BloodRequestCreate(BaseModel):
    hospital_id: str
    reported_group: str
    requested_units: int = Field(2, ge=1, le=20)
    reason: Optional[str] = None


class SpecialistRequestCreate(BaseModel):
    hospital_id: str
    specialty: str
    reason: Optional[str] = None


class CaseAcknowledgeRequest(BaseModel):
    notes: Optional[str] = Field(None, max_length=500)


class CaseDeclineRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


class DoctorDispatchRequest(BaseModel):
    specialist_doctor: Optional[str] = None
    bay_number: Optional[str] = "Trauma Bay 1"
    prep_notes: Optional[str] = None


class HandoverCompleteRequest(BaseModel):
    handover_notes: Optional[str] = None


class CoordinationRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    hospital_id: str
    request_type: str
    requested_details: Dict[str, Any]
    status: str
    reason: Optional[str] = None
    actor_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class IncomingCaseOut(BaseModel):
    incident_id: str
    location_label: str
    injury_category: str
    incident_source: str
    reported_priority: str
    witness_assessment: str
    reported_blood_group: str
    vitals: Dict[str, Any]
    route_hazards: list[str]
    status: str
    selected_at: datetime
    eta_minutes: Optional[float] = None
    coordination_requests: list[CoordinationRequestOut] = []
