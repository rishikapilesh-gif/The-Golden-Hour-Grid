from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from backend.app.models.incident import Incident
from backend.app.models.coordination import CoordinationRequest
from backend.app.schemas.incident import IncidentCreate


class IncidentRepository:
    @staticmethod
    def create_incident(
        db: Session,
        data: IncidentCreate,
        user_id: Optional[str] = None
    ) -> Incident:
        now = datetime.now(timezone.utc)
        incident = Incident(
            location_label=data.location.label,
            latitude=data.location.latitude,
            longitude=data.location.longitude,
            injury_category=data.injury_category,
            incident_source=data.incident_source,
            gender=data.gender,
            reported_priority=data.reported_priority,
            witness_assessment=data.witness_assessment,
            heart_rate_bpm=data.vitals.heart_rate_bpm if data.vitals else None,
            spo2_percent=data.vitals.spo2_percent if data.vitals else None,
            pao2_mmhg=data.vitals.pao2_mmhg if data.vitals else None,
            vitals_observed_at=data.vitals.observed_at if data.vitals else None,
            reported_blood_group=data.reported_blood_group,
            blood_group_verified=data.blood_group_verified,
            route_hazards=data.route_hazards,
            status="created",
            is_demo=True,
            created_by_user_id=user_id,
            created_at=now,
            updated_at=now
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def get_by_id(db: Session, incident_id: str) -> Optional[Incident]:
        return db.query(Incident).options(
            joinedload(Incident.coordination_requests)
        ).filter(Incident.id == incident_id).first()

    @staticmethod
    def select_hospital(
        db: Session,
        incident_id: str,
        hospital_id: str,
        override_reason: Optional[str] = None
    ) -> Optional[Incident]:
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            return None
        incident.selected_hospital_id = hospital_id
        incident.override_reason = override_reason
        incident.status = "hospital_selected"
        incident.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def update_status(db: Session, incident_id: str, status: str) -> Optional[Incident]:
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            return None
        incident.status = status
        incident.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def get_incoming_for_hospital(db: Session, hospital_id: str) -> List[Incident]:
        """Fetch incoming cases assigned or selected for this specific hospital."""
        return db.query(Incident).options(
            joinedload(Incident.coordination_requests)
        ).filter(
            Incident.selected_hospital_id == hospital_id,
            Incident.status.notin_(["cancelled", "handover_complete"])
        ).order_by(Incident.updated_at.desc()).all()
