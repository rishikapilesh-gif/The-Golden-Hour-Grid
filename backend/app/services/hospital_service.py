from typing import Optional, List
from sqlalchemy.orm import Session
from backend.app.models.hospital import Hospital
from backend.app.schemas.hospital import HospitalResourceUpdate
from backend.app.repositories.hospital_repo import HospitalRepository
from backend.app.repositories.incident_repo import IncidentRepository
from backend.app.realtime.notifier import notifier


class HospitalService:
    @staticmethod
    def get_all_hospitals(db: Session) -> List[Hospital]:
        return HospitalRepository.get_all(db)

    @staticmethod
    def get_hospital_by_id(db: Session, hospital_id: str) -> Optional[Hospital]:
        return HospitalRepository.get_by_id(db, hospital_id)

    @staticmethod
    async def update_resources(
        db: Session,
        hospital_id: str,
        update_data: HospitalResourceUpdate,
        source: str = "hospital_command"
    ) -> Optional[Hospital]:
        hospital = HospitalRepository.update_resources(
            db=db,
            hospital_id=hospital_id,
            icu_available=update_data.icu_available,
            er_load=update_data.er_load,
            accepting_status=update_data.accepting_status,
            specialists_update=update_data.specialists,
            blood_update=update_data.blood,
            source=source
        )
        if hospital:
            # Broadcast resource update event
            await notifier.broadcast_event(
                event_type="hospital.resource_changed",
                payload={
                    "hospital_id": hospital.id,
                    "hospital_name": hospital.name,
                    "icu_available": hospital.icu_available,
                    "er_load": hospital.er_load,
                    "accepting_status": hospital.accepting_status,
                    "source": source
                },
                entity_id=hospital.id,
                hospital_id=hospital.id,
                source=source
            )
        return hospital

    @staticmethod
    def get_incoming_cases(db: Session, hospital_id: str):
        incidents = IncidentRepository.get_incoming_for_hospital(db, hospital_id)
        result = []
        for inc in incidents:
            vitals_dict = {
                "heart_rate_bpm": inc.heart_rate_bpm,
                "spo2_percent": inc.spo2_percent,
                "pao2_mmhg": inc.pao2_mmhg
            }
            coord_reqs = [
                {
                    "id": r.id,
                    "incident_id": r.incident_id,
                    "hospital_id": r.hospital_id,
                    "request_type": r.request_type,
                    "requested_details": r.requested_details,
                    "status": r.status,
                    "reason": r.reason,
                    "actor_user_id": r.actor_user_id,
                    "created_at": r.created_at,
                    "updated_at": r.updated_at
                }
                for r in inc.coordination_requests
            ]
            result.append({
                "incident_id": inc.id,
                "location_label": inc.location_label,
                "injury_category": inc.injury_category,
                "incident_source": inc.incident_source,
                "reported_priority": inc.reported_priority,
                "witness_assessment": inc.witness_assessment,
                "reported_blood_group": inc.reported_blood_group,
                "vitals": vitals_dict,
                "route_hazards": inc.route_hazards or [],
                "status": inc.status,
                "selected_at": inc.updated_at,
                "eta_minutes": None,
                "coordination_requests": coord_reqs
            })
        return result
