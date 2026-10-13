import random
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.db.session import get_db
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from backend.app.models.hospital import Hospital, SpecialistAvailability, BloodInventory
from backend.app.services.hospital_service import HospitalService
from backend.app.schemas.hospital import HospitalResourceUpdate

router = APIRouter(prefix="/demo", tags=["demo"])

BLOOD_GROUPS = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]
SPECIALTY_KEYS = ["trauma", "neuro", "cardiac", "ortho", "burns"]


@router.post("/resource-updates")
async def trigger_demo_resource_update(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo resource updates are disabled when DEMO_MODE is false."
        )

    hospitals = HospitalService.get_all_hospitals(db)
    if not hospitals:
        return {"message": "No hospitals seeded."}

    h = random.choice(hospitals)
    mutation_type = random.random()
    desc = ""

    if mutation_type < 0.3:
        # Mutate ICU beds
        old_icu = h.icu_available
        new_icu = max(0, min(6, old_icu + (1 if random.random() < 0.5 else -1)))
        await HospitalService.update_resources(
            db, h.id,
            HospitalResourceUpdate(icu_available=new_icu),
            source="demo_feed"
        )
        desc = f"{h.name}: ICU beds changed from {old_icu} to {new_icu}"
    elif mutation_type < 0.6:
        # Mutate ER load
        old_er = h.er_load
        delta = 0.1 if random.random() < 0.5 else -0.1
        new_er = round(max(0.1, min(0.95, old_er + delta)), 2)
        await HospitalService.update_resources(
            db, h.id,
            HospitalResourceUpdate(er_load=new_er),
            source="demo_feed"
        )
        desc = f"{h.name}: ER load changed from {round(old_er*100)}% to {round(new_er*100)}%"
    elif mutation_type < 0.8:
        # Mutate blood stock
        bg = random.choice(BLOOD_GROUPS)
        b_rec = next((b for b in h.blood_inventories if b.blood_group == bg), None)
        old_units = b_rec.units_available if b_rec else 2
        new_units = max(0, min(16, old_units + (1 if random.random() < 0.5 else -1)))
        await HospitalService.update_resources(
            db, h.id,
            HospitalResourceUpdate(blood={bg: new_units}),
            source="demo_feed"
        )
        desc = f"{h.name}: {bg} blood stock changed from {old_units} to {new_units} units"
    else:
        # Mutate specialist status
        sp = random.choice(SPECIALTY_KEYS)
        s_rec = next((s for s in h.specialists if s.specialty == sp), None)
        old_status = s_rec.status if s_rec else "unknown"
        new_status = "surgery" if old_status in ("free", "available") else "free"
        await HospitalService.update_resources(
            db, h.id,
            HospitalResourceUpdate(specialists={sp: new_status}),
            source="demo_feed"
        )
        desc = f"{h.name}: {sp} specialist status changed from {old_status} to {new_status}"

    return {
        "status": "success",
        "description": desc,
        "is_demo": True,
        "hospital_id": h.id
    }
