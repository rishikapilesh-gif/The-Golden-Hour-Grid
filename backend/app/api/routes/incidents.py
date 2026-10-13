from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.api.deps import get_current_user, require_ambulance_user
from backend.app.models.user import User
from backend.app.schemas.incident import (
    IncidentCreate,
    IncidentOut,
    SelectHospitalRequest,
    StatusUpdateRequest,
    LocationInput,
    VitalsInput
)
from backend.app.schemas.ranking import RankingResponse
from backend.app.schemas.coordination import (
    BloodRequestCreate,
    SpecialistRequestCreate,
    CoordinationRequestOut
)
from backend.app.services.incident_service import incident_service
from backend.app.services.coordination_service import CoordinationService

router = APIRouter(prefix="/incidents", tags=["incidents"])


def serialize_incident(inc) -> IncidentOut:
    return IncidentOut(
        id=inc.id,
        location_label=inc.location_label,
        latitude=inc.latitude,
        longitude=inc.longitude,
        injury_category=inc.injury_category,
        incident_source=inc.incident_source,
        gender=inc.gender,
        reported_priority=inc.reported_priority,
        witness_assessment=inc.witness_assessment,
        vitals=VitalsInput(
            heart_rate_bpm=inc.heart_rate_bpm,
            spo2_percent=inc.spo2_percent,
            pao2_mmhg=inc.pao2_mmhg,
            observed_at=inc.vitals_observed_at
        ),
        reported_blood_group=inc.reported_blood_group,
        blood_group_verified=inc.blood_group_verified,
        route_hazards=inc.route_hazards or [],
        status=inc.status,
        selected_hospital_id=inc.selected_hospital_id,
        override_reason=inc.override_reason,
        is_demo=inc.is_demo,
        created_at=inc.created_at,
        updated_at=inc.updated_at
    )


@router.post("", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
def create_incident(
    data: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_ambulance_user)
):
    incident = incident_service.create_incident(db, data, current_user.id)
    return serialize_incident(incident)


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inc = incident_service.get_incident(db, incident_id)
    if not inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with id '{incident_id}' not found."
        )
    return serialize_incident(inc)


@router.get("/{incident_id}/recommendations", response_model=RankingResponse)
def get_recommendations(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ranking = incident_service.compute_ranking(db, incident_id)
    if not ranking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with id '{incident_id}' not found."
        )
    return ranking


@router.post("/{incident_id}/recompute", response_model=RankingResponse)
def recompute_recommendations(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ranking = incident_service.compute_ranking(db, incident_id)
    if not ranking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with id '{incident_id}' not found."
        )
    return ranking


@router.post("/{incident_id}/select-hospital", response_model=IncidentOut)
async def select_hospital(
    incident_id: str,
    req: SelectHospitalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_ambulance_user)
):
    inc = await incident_service.select_hospital(
        db=db,
        incident_id=incident_id,
        hospital_id=req.hospital_id,
        override_reason=req.override_reason
    )
    if not inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with id '{incident_id}' not found."
        )
    return serialize_incident(inc)


@router.post("/{incident_id}/blood-requests", response_model=CoordinationRequestOut)
async def create_blood_request(
    incident_id: str,
    req: BloodRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_ambulance_user)
):
    coord_req = await CoordinationService.stage_blood_request(
        db=db,
        incident_id=incident_id,
        hospital_id=req.hospital_id,
        reported_group=req.reported_group,
        requested_units=req.requested_units,
        reason=req.reason,
        actor_user_id=current_user.id
    )
    return coord_req


@router.post("/{incident_id}/specialist-requests", response_model=CoordinationRequestOut)
async def create_specialist_request(
    incident_id: str,
    req: SpecialistRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_ambulance_user)
):
    coord_req = await CoordinationService.stage_specialist_request(
        db=db,
        incident_id=incident_id,
        hospital_id=req.hospital_id,
        specialty=req.specialty,
        reason=req.reason,
        actor_user_id=current_user.id
    )
    return coord_req


@router.get("/{incident_id}/coordination-requests", response_model=List[CoordinationRequestOut])
def get_coordination_requests(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return CoordinationService.get_incident_requests(db, incident_id)


@router.patch("/{incident_id}/status", response_model=IncidentOut)
async def update_incident_status(
    incident_id: str,
    req: StatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_ambulance_user)
):
    inc = await incident_service.update_status(db, incident_id, req.status)
    if not inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with id '{incident_id}' not found."
        )
    return serialize_incident(inc)
