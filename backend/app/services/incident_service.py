from typing import Optional
from sqlalchemy.orm import Session
from backend.app.models.incident import Incident
from backend.app.schemas.incident import IncidentCreate
from backend.app.repositories.incident_repo import IncidentRepository
from backend.app.repositories.hospital_repo import HospitalRepository
from backend.app.providers.routing.demo_router import DemoRoutingProvider
from backend.app.ranking.engine import DeterministicRankingEngine
from backend.app.realtime.notifier import notifier


class IncidentService:
    def __init__(self):
        self.router = DemoRoutingProvider()
        self.ranker = DeterministicRankingEngine(self.router)

    def create_incident(self, db: Session, data: IncidentCreate, user_id: str) -> Incident:
        incident = IncidentRepository.create_incident(db, data, user_id)
        return incident

    def get_incident(self, db: Session, incident_id: str) -> Optional[Incident]:
        return IncidentRepository.get_by_id(db, incident_id)

    def compute_ranking(self, db: Session, incident_id: str):
        incident = IncidentRepository.get_by_id(db, incident_id)
        if not incident:
            return None
        hospitals = HospitalRepository.get_all(db)
        return self.ranker.rank_hospitals(incident, hospitals)

    async def select_hospital(
        self,
        db: Session,
        incident_id: str,
        hospital_id: str,
        override_reason: Optional[str] = None
    ) -> Optional[Incident]:
        incident = IncidentRepository.select_hospital(db, incident_id, hospital_id, override_reason)
        if incident:
            # Broadcast destination selection to ambulance and targeted hospital
            await notifier.broadcast_event(
                event_type="incident.hospital_selected",
                payload={
                    "incident_id": incident.id,
                    "selected_hospital_id": hospital_id,
                    "override_reason": override_reason,
                    "status": incident.status,
                    "injury_category": incident.injury_category,
                    "reported_blood_group": incident.reported_blood_group,
                    "reported_priority": incident.reported_priority
                },
                entity_id=incident.id,
                hospital_id=hospital_id
            )
        return incident

    async def update_status(self, db: Session, incident_id: str, status: str) -> Optional[Incident]:
        incident = IncidentRepository.update_status(db, incident_id, status)
        if incident:
            await notifier.broadcast_event(
                event_type="incident.status_changed",
                payload={
                    "incident_id": incident.id,
                    "status": incident.status,
                    "selected_hospital_id": incident.selected_hospital_id
                },
                entity_id=incident.id,
                hospital_id=incident.selected_hospital_id
            )
        return incident


incident_service = IncidentService()
