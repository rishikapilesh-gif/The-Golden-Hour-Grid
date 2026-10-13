from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.coordination import CoordinationRequest, ResourceEvent


class CoordinationRepository:
    @staticmethod
    def create_or_get_blood_request(
        db: Session,
        incident_id: str,
        hospital_id: str,
        reported_group: str,
        requested_units: int,
        reason: Optional[str] = None,
        actor_user_id: Optional[str] = None
    ) -> CoordinationRequest:
        # Check if active request already exists for this incident and hospital
        existing = db.query(CoordinationRequest).filter(
            CoordinationRequest.incident_id == incident_id,
            CoordinationRequest.hospital_id == hospital_id,
            CoordinationRequest.request_type == "blood",
            CoordinationRequest.status.in_(["draft", "pending_approval", "acknowledged"])
        ).first()

        if existing:
            return existing

        now = datetime.now(timezone.utc)
        req = CoordinationRequest(
            incident_id=incident_id,
            hospital_id=hospital_id,
            request_type="blood",
            requested_details={
                "reported_group": reported_group,
                "requested_units": requested_units,
                "note": "blood bank verification and cross-match/authorization required"
            },
            status="pending_approval",
            reason=reason or "Reported inventory below configured demo threshold",
            actor_user_id=actor_user_id,
            created_at=now,
            updated_at=now
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        return req

    @staticmethod
    def create_or_get_specialist_request(
        db: Session,
        incident_id: str,
        hospital_id: str,
        specialty: str,
        reason: Optional[str] = None,
        actor_user_id: Optional[str] = None
    ) -> CoordinationRequest:
        existing = db.query(CoordinationRequest).filter(
            CoordinationRequest.incident_id == incident_id,
            CoordinationRequest.hospital_id == hospital_id,
            CoordinationRequest.request_type == "specialist",
            CoordinationRequest.status.in_(["draft", "pending_approval", "acknowledged"])
        ).first()

        if existing:
            return existing

        now = datetime.now(timezone.utc)
        req = CoordinationRequest(
            incident_id=incident_id,
            hospital_id=hospital_id,
            request_type="specialist",
            requested_details={
                "specialty": specialty,
                "note": "specialist pre-alert state; no external phone/video call claimed"
            },
            status="pending_approval",
            reason=reason or "Incoming emergency case requiring specialty pre-alert",
            actor_user_id=actor_user_id,
            created_at=now,
            updated_at=now
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        return req

    @staticmethod
    def get_requests_for_incident(db: Session, incident_id: str) -> List[CoordinationRequest]:
        return db.query(CoordinationRequest).filter(
            CoordinationRequest.incident_id == incident_id
        ).order_by(CoordinationRequest.created_at.desc()).all()

    @staticmethod
    def get_requests_for_hospital(db: Session, hospital_id: str) -> List[CoordinationRequest]:
        return db.query(CoordinationRequest).filter(
            CoordinationRequest.hospital_id == hospital_id
        ).order_by(CoordinationRequest.created_at.desc()).all()

    @staticmethod
    def update_status(
        db: Session,
        request_id: str,
        status: str,
        reason: Optional[str] = None
    ) -> Optional[CoordinationRequest]:
        req = db.query(CoordinationRequest).filter(CoordinationRequest.id == request_id).first()
        if not req:
            return None
        req.status = status
        if reason:
            req.reason = reason
        req.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(req)
        return req
