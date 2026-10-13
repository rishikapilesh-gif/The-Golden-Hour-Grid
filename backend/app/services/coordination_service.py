from typing import Optional, List
from sqlalchemy.orm import Session
from backend.app.models.coordination import CoordinationRequest
from backend.app.repositories.coordination_repo import CoordinationRepository
from backend.app.repositories.incident_repo import IncidentRepository
from backend.app.realtime.notifier import notifier


class CoordinationService:
    @staticmethod
    async def stage_blood_request(
        db: Session,
        incident_id: str,
        hospital_id: str,
        reported_group: str,
        requested_units: int,
        reason: Optional[str] = None,
        actor_user_id: Optional[str] = None
    ) -> CoordinationRequest:
        req = CoordinationRepository.create_or_get_blood_request(
            db=db,
            incident_id=incident_id,
            hospital_id=hospital_id,
            reported_group=reported_group,
            requested_units=requested_units,
            reason=reason,
            actor_user_id=actor_user_id
        )
        await notifier.broadcast_event(
            event_type="coordination.blood_request_updated",
            payload={
                "request_id": req.id,
                "incident_id": incident_id,
                "hospital_id": hospital_id,
                "blood_group": reported_group,
                "requested_units": requested_units,
                "status": req.status,
                "note": "blood bank verification and cross-match/authorization required"
            },
            entity_id=req.id,
            hospital_id=hospital_id
        )
        return req

    @staticmethod
    async def stage_specialist_request(
        db: Session,
        incident_id: str,
        hospital_id: str,
        specialty: str,
        reason: Optional[str] = None,
        actor_user_id: Optional[str] = None
    ) -> CoordinationRequest:
        req = CoordinationRepository.create_or_get_specialist_request(
            db=db,
            incident_id=incident_id,
            hospital_id=hospital_id,
            specialty=specialty,
            reason=reason,
            actor_user_id=actor_user_id
        )
        await notifier.broadcast_event(
            event_type="coordination.specialist_request_updated",
            payload={
                "request_id": req.id,
                "incident_id": incident_id,
                "hospital_id": hospital_id,
                "specialty": specialty,
                "status": req.status,
                "note": "specialist pre-alert state; no external phone/video call claimed"
            },
            entity_id=req.id,
            hospital_id=hospital_id
        )
        return req

    @staticmethod
    def get_incident_requests(db: Session, incident_id: str) -> List[CoordinationRequest]:
        return CoordinationRepository.get_requests_for_incident(db, incident_id)

    @staticmethod
    async def acknowledge_case(
        db: Session,
        incident_id: str,
        hospital_id: str,
        notes: Optional[str] = None,
        actor_user_id: Optional[str] = None
    ):
        incident = IncidentRepository.get_by_id(db, incident_id)
        if not incident or incident.selected_hospital_id != hospital_id:
            return None

        # Update or create pre-alert coordination request
        req = CoordinationRepository.create_or_get_specialist_request(
            db, incident_id, hospital_id, incident.injury_category,
            reason="Hospital acknowledgement", actor_user_id=actor_user_id
        )
        CoordinationRepository.update_status(db, req.id, "acknowledged", notes or "Hospital command acknowledged incoming case")

        await notifier.broadcast_event(
            event_type="hospital.case_acknowledged",
            payload={
                "incident_id": incident_id,
                "hospital_id": hospital_id,
                "notes": notes,
                "status": "acknowledged"
            },
            entity_id=incident_id,
            hospital_id=hospital_id
        )
        return {"status": "acknowledged", "incident_id": incident_id, "hospital_id": hospital_id}

    @staticmethod
    async def decline_case(
        db: Session,
        incident_id: str,
        hospital_id: str,
        reason: str,
        actor_user_id: Optional[str] = None
    ):
        incident = IncidentRepository.get_by_id(db, incident_id)
        if not incident or incident.selected_hospital_id != hospital_id:
            return None

        incident.status = "triaged_by_dispatch"  # return to dispatch queue
        db.commit()

        await notifier.broadcast_event(
            event_type="hospital.case_declined",
            payload={
                "incident_id": incident_id,
                "hospital_id": hospital_id,
                "reason": reason,
                "status": "declined"
            },
            entity_id=incident_id,
            hospital_id=hospital_id
        )
        return {"status": "declined", "incident_id": incident_id, "hospital_id": hospital_id, "reason": reason}

    @staticmethod
    async def dispatch_doctor(
        db: Session,
        incident_id: str,
        hospital_id: str,
        specialist_doctor: Optional[str] = None,
        bay_number: Optional[str] = "Trauma Bay 1",
        prep_notes: Optional[str] = None,
        actor_user_id: Optional[str] = None
    ):
        incident = IncidentRepository.get_by_id(db, incident_id)
        if not incident or incident.selected_hospital_id != hospital_id:
            return None

        req = CoordinationRepository.create_or_get_specialist_request(
            db, incident_id, hospital_id, incident.injury_category,
            reason=f"Doctor dispatched to {bay_number}", actor_user_id=actor_user_id
        )
        note_str = f"Attending doctor {specialist_doctor or 'on duty'} dispatched to {bay_number}. {prep_notes or ''}".strip()
        CoordinationRepository.update_status(db, req.id, "doctor_dispatched", note_str)

        await notifier.broadcast_event(
            event_type="hospital.doctor_dispatched",
            payload={
                "incident_id": incident_id,
                "hospital_id": hospital_id,
                "specialist_doctor": specialist_doctor,
                "bay_number": bay_number,
                "prep_notes": prep_notes,
                "status": "doctor_dispatched"
            },
            entity_id=incident_id,
            hospital_id=hospital_id
        )
        return {
            "status": "doctor_dispatched",
            "incident_id": incident_id,
            "hospital_id": hospital_id,
            "specialist_doctor": specialist_doctor,
            "bay_number": bay_number,
            "prep_notes": prep_notes
        }

    @staticmethod
    async def complete_handover(
        db: Session,
        incident_id: str,
        hospital_id: str,
        handover_notes: Optional[str] = None,
        actor_user_id: Optional[str] = None
    ):
        incident = IncidentRepository.get_by_id(db, incident_id)
        if not incident or incident.selected_hospital_id != hospital_id:
            return None

        incident.status = "handover_complete"
        db.commit()

        await notifier.broadcast_event(
            event_type="hospital.handover_completed",
            payload={
                "incident_id": incident_id,
                "hospital_id": hospital_id,
                "handover_notes": handover_notes,
                "status": "handover_complete"
            },
            entity_id=incident_id,
            hospital_id=hospital_id
        )
        return {
            "status": "handover_complete",
            "incident_id": incident_id,
            "hospital_id": hospital_id,
            "handover_notes": handover_notes
        }
