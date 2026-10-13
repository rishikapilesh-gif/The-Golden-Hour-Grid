from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SpecialistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    specialty: str
    status: str
    doctor_name: Optional[str] = None
    expected_free_mins: Optional[int] = None
    source: str
    updated_at: datetime


class BloodInventoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    blood_group: str
    units_available: int
    units_reserved: int
    source: str
    updated_at: datetime


class HospitalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    is_demo: bool
    x: float
    y: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accepting_status: str
    icu_capacity: int
    icu_available: int
    er_load: float
    source: str
    updated_at: datetime
    last_verified_at: Optional[datetime] = None
    specialists: list[SpecialistOut] = []
    blood_inventory: list[BloodInventoryOut] = []


class HospitalResourceUpdate(BaseModel):
    icu_available: Optional[int] = Field(None, ge=0, le=20)
    er_load: Optional[float] = Field(None, ge=0.0, le=1.0)
    accepting_status: Optional[str] = Field(None, pattern="^(accepting|not_accepting|unknown)$")
    specialists: Optional[dict[str, str]] = None  # specialty -> status (e.g. {"trauma": "free"})
    blood: Optional[dict[str, int]] = None  # blood_group -> units (e.g. {"O-": 4})
