import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, Float, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class HospitalRecommendation(Base):
    __tablename__ = "hospital_recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), index=True, nullable=False)
    hospital_id: Mapped[str] = mapped_column(String(100), ForeignKey("hospitals.id", ondelete="CASCADE"), index=True, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    score_components: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    eta_minutes: Mapped[float] = mapped_column(Float, nullable=False)
    eta_source: Mapped[str] = mapped_column(String(50), default="demo_router", nullable=False)
    eta_is_live: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    reasons: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    warnings: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    data_freshness: Mapped[str] = mapped_column(String(30), default="fresh", nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    ranking_version: Mapped[str] = mapped_column(String(20), default="v1", nullable=False)

    incident = relationship("Incident", back_populates="recommendations")


class CoordinationRequest(Base):
    __tablename__ = "coordination_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), index=True, nullable=False)
    hospital_id: Mapped[str] = mapped_column(String(100), ForeignKey("hospitals.id", ondelete="CASCADE"), index=True, nullable=False)
    request_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'blood', 'specialist', 'hospital_prealert'
    requested_details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending_approval", nullable=False)  # draft, pending_approval, acknowledged, accepted, declined, cancelled
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    incident = relationship("Incident", back_populates="coordination_requests")


class ResourceEvent(Base):
    __tablename__ = "resource_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    incident_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    before_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="demo_seed", nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
