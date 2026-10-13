from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.api.deps import require_hospital_user
from backend.app.models.user import User
from backend.app.schemas.hospital import HospitalOut, HospitalResourceUpdate
from backend.app.schemas.coordination import (
    CaseAcknowledgeRequest,
    CaseDeclineRequest,
    IncomingCaseOut,
    DoctorDispatchRequest,
    HandoverCompleteRequest
)
from backend.app.services.hospital_service import HospitalService
from backend.app.services.coordination_service import CoordinationService
from backend.app.api.routes.hospitals import serialize_hospital

router = APIRouter(prefix="/hospital", tags=["hospital_command"])


@router.get("/me/resources", response_model=HospitalOut)
def get_own_resources(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hospital_user)
):
    hospital_id = current_user.hospital_id
    h = HospitalService.get_hospital_by_id(db, hospital_id)
    if not h:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assigned hospital '{hospital_id}' not found."
        )
    return serialize_hospital(h)


@router.patch("/me/resources", response_model=HospitalOut)
async def update_own_resources(
    update_data: HospitalResourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hospital_user)
):
    hospital_id = current_user.hospital_id
    updated = await HospitalService.update_resources(
        db=db,
        hospital_id=hospital_id,
        update_data=update_data,
        source=f"hospital_command:{current_user.username}"
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assigned hospital '{hospital_id}' not found."
        )
    return serialize_hospital(updated)


@router.get("/incoming-cases", response_model=List[IncomingCaseOut])
def get_incoming_cases(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hospital_user)
):
    hospital_id = current_user.hospital_id
    return HospitalService.get_incoming_cases(db, hospital_id)


@router.post("/incidents/{incident_id}/acknowledge")
async def acknowledge_case(
    incident_id: str,
    req: CaseAcknowledgeRequest = CaseAcknowledgeRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hospital_user)
):
    hospital_id = current_user.hospital_id
    result = await CoordinationService.acknowledge_case(
        db=db,
        incident_id=incident_id,
        hospital_id=hospital_id,
        notes=req.notes,
        actor_user_id=current_user.id
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or not assigned to your hospital."
        )
    return result


@router.post("/incidents/{incident_id}/decline")
async def decline_case(
    incident_id: str,
    req: CaseDeclineRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hospital_user)
):
    hospital_id = current_user.hospital_id
    result = await CoordinationService.decline_case(
        db=db,
        incident_id=incident_id,
        hospital_id=hospital_id,
        reason=req.reason,
        actor_user_id=current_user.id
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or not assigned to your hospital."
        )
    return result


@router.post("/incidents/{incident_id}/dispatch-doctor")
async def dispatch_doctor(
    incident_id: str,
    req: DoctorDispatchRequest = DoctorDispatchRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hospital_user)
):
    hospital_id = current_user.hospital_id
    result = await CoordinationService.dispatch_doctor(
        db=db,
        incident_id=incident_id,
        hospital_id=hospital_id,
        specialist_doctor=req.specialist_doctor,
        bay_number=req.bay_number,
        prep_notes=req.prep_notes,
        actor_user_id=current_user.id
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or not assigned to your hospital."
        )
    return result


@router.post("/incidents/{incident_id}/complete-handover")
async def complete_handover(
    incident_id: str,
    req: HandoverCompleteRequest = HandoverCompleteRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hospital_user)
):
    hospital_id = current_user.hospital_id
    result = await CoordinationService.complete_handover(
        db=db,
        incident_id=incident_id,
        hospital_id=hospital_id,
        handover_notes=req.handover_notes,
        actor_user_id=current_user.id
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found or not assigned to your hospital."
        )
    return result
