from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from backend.app.models.hospital import Hospital, SpecialistAvailability, BloodInventory
from backend.app.models.coordination import ResourceEvent


class HospitalRepository:
    @staticmethod
    def get_all(db: Session) -> List[Hospital]:
        return db.query(Hospital).options(
            joinedload(Hospital.specialists),
            joinedload(Hospital.blood_inventories)
        ).all()

    @staticmethod
    def get_by_id(db: Session, hospital_id: str) -> Optional[Hospital]:
        return db.query(Hospital).options(
            joinedload(Hospital.specialists),
            joinedload(Hospital.blood_inventories)
        ).filter(Hospital.id == hospital_id).first()

    @staticmethod
    def update_resources(
        db: Session,
        hospital_id: str,
        icu_available: Optional[int] = None,
        er_load: Optional[float] = None,
        accepting_status: Optional[str] = None,
        specialists_update: Optional[dict[str, str]] = None,
        blood_update: Optional[dict[str, int]] = None,
        source: str = "hospital_command"
    ) -> Optional[Hospital]:
        hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hospital:
            return None

        now = datetime.now(timezone.utc)
        before_state = {
            "icu_available": hospital.icu_available,
            "er_load": hospital.er_load,
            "accepting_status": hospital.accepting_status,
        }

        if icu_available is not None:
            hospital.icu_available = icu_available
        if er_load is not None:
            hospital.er_load = er_load
        if accepting_status is not None:
            hospital.accepting_status = accepting_status
        hospital.updated_at = now
        hospital.source = source

        # Update specialists
        if specialists_update:
            for spec_key, status in specialists_update.items():
                spec = db.query(SpecialistAvailability).filter(
                    SpecialistAvailability.hospital_id == hospital_id,
                    SpecialistAvailability.specialty == spec_key
                ).first()
                if spec:
                    spec.status = status
                    spec.updated_at = now
                    spec.source = source
                else:
                    new_spec = SpecialistAvailability(
                        hospital_id=hospital_id,
                        specialty=spec_key,
                        status=status,
                        source=source,
                        updated_at=now
                    )
                    db.add(new_spec)

        # Update blood inventory
        if blood_update:
            for group, units in blood_update.items():
                b = db.query(BloodInventory).filter(
                    BloodInventory.hospital_id == hospital_id,
                    BloodInventory.blood_group == group
                ).first()
                if b:
                    b.units_available = units
                    b.updated_at = now
                    b.source = source
                else:
                    new_b = BloodInventory(
                        hospital_id=hospital_id,
                        blood_group=group,
                        units_available=units,
                        source=source,
                        updated_at=now
                    )
                    db.add(new_b)

        # Record audit event
        after_state = {
            "icu_available": hospital.icu_available,
            "er_load": hospital.er_load,
            "accepting_status": hospital.accepting_status,
        }
        event = ResourceEvent(
            hospital_id=hospital_id,
            event_type="hospital.resource_changed",
            before_state=before_state,
            after_state=after_state,
            source=source,
            is_demo=hospital.is_demo,
            created_at=now
        )
        db.add(event)

        db.commit()
        db.refresh(hospital)
        return hospital
