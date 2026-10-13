import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    location_label: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    injury_category: Mapped[str] = mapped_column(String(50), nullable=False)  # trauma, neuro, cardiac, ortho, burns
    incident_source: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[str] = mapped_column(String(30), default="Unknown", nullable=False)  # context only
    reported_priority: Mapped[str] = mapped_column(String(30), default="High", nullable=False)
    witness_assessment: Mapped[str] = mapped_column(String(30), default="Unknown", nullable=False)
    heart_rate_bpm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    spo2_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    pao2_mmhg: Mapped[float | None] = mapped_column(Float, nullable=True)
    vitals_observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reported_blood_group: Mapped[str] = mapped_column(String(10), default="O-", nullable=False)
    blood_group_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    route_hazards: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="created", nullable=False)
    selected_hospital_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    override_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    recommendations = relationship("HospitalRecommendation", back_populates="incident", cascade="all, delete-orphan")
    coordination_requests = relationship("CoordinationRequest", back_populates="incident", cascade="all, delete-orphan")
