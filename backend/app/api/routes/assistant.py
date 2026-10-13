from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from backend.app.providers.assistant.local_ai import local_assistant
from backend.app.services.incident_service import incident_service
from backend.app.services.hospital_service import HospitalService

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.get("/health")
def get_assistant_health(current_user: User = Depends(get_current_user)):
    return {
        "enabled": settings.LOCAL_ASSISTANT_ENABLED,
        "provider": settings.LOCAL_ASSISTANT_PROVIDER,
        "base_url": settings.LOCAL_ASSISTANT_BASE_URL,
        "model": settings.LOCAL_ASSISTANT_MODEL or "(not configured)",
        "status": "ready" if settings.LOCAL_ASSISTANT_ENABLED else "disabled",
        "notes": "Local assistant is optional and non-authoritative. Hospital ranking remains strictly deterministic."
    }


@router.post("/note/{incident_id}")
async def generate_assistant_note(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not settings.LOCAL_ASSISTANT_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Local assistant is disabled in configuration."
        )

    inc = incident_service.get_incident(db, incident_id)
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    hospitals = HospitalService.get_all_hospitals(db)
    summary = [{"name": h.name, "icu": h.icu_available, "er": h.er_load} for h in hospitals[:5]]

    note = await local_assistant.generate_coordination_note(
        incident_data={
            "injury": inc.injury_category,
            "severity": inc.reported_priority,
            "location": inc.location_label,
            "blood_group": inc.reported_blood_group
        },
        hospitals_summary=summary
    )

    return {
        "incident_id": incident_id,
        "note": note,
        "is_authoritative": False,
        "disclaimer": "Non-clinical operational coordination checklist only. Does not override deterministic hospital ranking."
    }
