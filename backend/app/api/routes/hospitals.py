from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.hospital import HospitalOut, SpecialistOut, BloodInventoryOut
from backend.app.services.hospital_service import HospitalService

router = APIRouter(tags=["hospitals"])


def serialize_hospital(h) -> HospitalOut:
    return HospitalOut(
        id=h.id,
        name=h.name,
        is_demo=h.is_demo,
        x=h.x,
        y=h.y,
        accepting_status=h.accepting_status,
        icu_capacity=h.icu_capacity,
        icu_available=h.icu_available,
        er_load=h.er_load,
        source=h.source,
        updated_at=h.updated_at,
        last_verified_at=h.last_verified_at,
        specialists=[
            SpecialistOut(
                specialty=s.specialty,
                status=s.status,
                doctor_name=s.doctor_name,
                expected_free_mins=s.expected_free_mins,
                source=s.source,
                updated_at=s.updated_at
            ) for s in h.specialists
        ],
        blood_inventory=[
            BloodInventoryOut(
                blood_group=b.blood_group,
                units_available=b.units_available,
                units_reserved=b.units_reserved,
                source=b.source,
                updated_at=b.updated_at
            ) for b in h.blood_inventories
        ]
    )


@router.get("/hospitals", response_model=List[HospitalOut])
def list_hospitals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    hospitals = HospitalService.get_all_hospitals(db)
    return [serialize_hospital(h) for h in hospitals]


@router.get("/hospitals/{hospital_id}", response_model=HospitalOut)
def get_hospital(
    hospital_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    h = HospitalService.get_hospital_by_id(db, hospital_id)
    if not h:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hospital with id '{hospital_id}' not found."
        )
    return serialize_hospital(h)


@router.get("/resources/snapshot")
def get_resource_snapshot(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    hospitals = HospitalService.get_all_hospitals(db)
    return {
        "is_demo": True,
        "hospitals": [serialize_hospital(h) for h in hospitals]
    }
