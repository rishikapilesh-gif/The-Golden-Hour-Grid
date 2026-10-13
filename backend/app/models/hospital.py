import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    x: Mapped[float] = mapped_column(Float, nullable=False)  # Map coordinate X
    y: Mapped[float] = mapped_column(Float, nullable=False)  # Map coordinate Y
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    accepting_status: Mapped[str] = mapped_column(String(30), default="accepting", nullable=False)
    icu_capacity: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    icu_available: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    er_load: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)  # 0.0 to 1.0
    source: Mapped[str] = mapped_column(String(100), default="demo_seed", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    specialists = relationship("SpecialistAvailability", back_populates="hospital", cascade="all, delete-orphan")
    blood_inventories = relationship("BloodInventory", back_populates="hospital", cascade="all, delete-orphan")


class SpecialistAvailability(Base):
    __tablename__ = "specialist_availabilities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id: Mapped[str] = mapped_column(String(100), ForeignKey("hospitals.id", ondelete="CASCADE"), index=True, nullable=False)
    specialty: Mapped[str] = mapped_column(String(50), nullable=False)  # trauma, neuro, cardiac, ortho, burns
    status: Mapped[str] = mapped_column(String(30), default="unknown", nullable=False)  # free/available, surgery/busy, none/unavailable, unknown
    doctor_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    expected_free_mins: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="demo_seed", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    hospital = relationship("Hospital", back_populates="specialists")


class BloodInventory(Base):
    __tablename__ = "blood_inventories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id: Mapped[str] = mapped_column(String(100), ForeignKey("hospitals.id", ondelete="CASCADE"), index=True, nullable=False)
    blood_group: Mapped[str] = mapped_column(String(10), nullable=False)  # O-, O+, A-, A+, B-, B+, AB-, AB+
    units_available: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    units_reserved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source: Mapped[str] = mapped_column(String(100), default="demo_seed", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    hospital = relationship("Hospital", back_populates="blood_inventories")
