import sys
import os
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.db.base import Base
from backend.app.db.session import engine, SessionLocal
from backend.app.models.hospital import Hospital, SpecialistAvailability, BloodInventory

BLOOD_GROUPS = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]

DOCTOR_NAMES = {
    "trauma": "Dr. Mehta",
    "neuro": "Dr. Iyer",
    "cardiac": "Dr. Rao",
    "ortho": "Dr. Khan",
    "burns": "Dr. Nair"
}

# The 15 synthetic hospitals with real geographic coordinates (Chennai metropolitan area for realism)
HOSPITALS_SPEC = [
    {
        "id": "demo-hospital-1",  # Maps to DEMO_HOSPITAL_ID
        "name": "Apex Trauma Center",
        "x": 430.0, "y": 90.0,
        "latitude": 13.0827, "longitude": 80.2707,
        "icu": 6, "er": 0.55,
        "specialists": {"trauma": "free", "neuro": "surgery", "ortho": "free"},
        "blood": [9, 14, 4, 10, 3, 8, 2, 5]
    },
    {
        "id": "demo-hospital-2",
        "name": "City Care Clinic",
        "x": 120.0, "y": 100.0,
        "latitude": 13.0569, "longitude": 80.2425,
        "icu": 1, "er": 0.40,
        "specialists": {"ortho": "free"},
        "blood": [1, 4, 0, 3, 0, 2, 0, 1]
    },
    {
        "id": "demo-hospital-3",
        "name": "Lifeline Heart & Neuro",
        "x": 180.0, "y": 290.0,
        "latitude": 13.0382, "longitude": 80.2458,
        "icu": 4, "er": 0.30,
        "specialists": {"cardiac": "free", "neuro": "free"},
        "blood": [6, 10, 3, 8, 2, 6, 1, 4]
    },
    {
        "id": "demo-hospital-4",
        "name": "Metro General",
        "x": 330.0, "y": 220.0,
        "latitude": 13.0498, "longitude": 80.2124,
        "icu": 3, "er": 0.85,
        "specialists": {"trauma": "surgery", "ortho": "free", "burns": "free"},
        "blood": [2, 6, 1, 3, 1, 2, 0, 1]
    },
    {
        "id": "demo-hospital-5",
        "name": "St. Mary Burns & Ortho",
        "x": 500.0, "y": 300.0,
        "latitude": 13.0067, "longitude": 80.2020,
        "icu": 2, "er": 0.20,
        "specialists": {"ortho": "free", "burns": "free"},
        "blood": [3, 7, 2, 5, 1, 4, 1, 2]
    },
    {
        "id": "demo-hospital-6",
        "name": "Sunrise Multispecialty",
        "x": 60.0, "y": 270.0,
        "latitude": 13.0837, "longitude": 80.1706,
        "icu": 5, "er": 0.45,
        "specialists": {"trauma": "free", "cardiac": "free", "neuro": "surgery", "ortho": "free"},
        "blood": [4, 8, 2, 6, 2, 5, 1, 3]
    },
    {
        "id": "demo-hospital-7",
        "name": "Green Valley Hospital",
        "x": 60.0, "y": 40.0,
        "latitude": 13.1187, "longitude": 80.2155,
        "icu": 3, "er": 0.30,
        "specialists": {"ortho": "free", "cardiac": "free"},
        "blood": [3, 5, 2, 4, 1, 3, 1, 2]
    },
    {
        "id": "demo-hospital-8",
        "name": "Riverside Medical",
        "x": 520.0, "y": 40.0,
        "latitude": 13.0765, "longitude": 80.2520,
        "icu": 4, "er": 0.60,
        "specialists": {"trauma": "free", "neuro": "free", "ortho": "surgery"},
        "blood": [5, 9, 3, 7, 2, 5, 1, 4]
    },
    {
        "id": "demo-hospital-9",
        "name": "Harbor Emergency Care",
        "x": 560.0, "y": 110.0,
        "latitude": 13.1022, "longitude": 80.2941,
        "icu": 2, "er": 0.35,
        "specialists": {"trauma": "surgery", "burns": "free"},
        "blood": [2, 5, 1, 4, 1, 3, 0, 2]
    },
    {
        "id": "demo-hospital-10",
        "name": "Sai Neuro Institute",
        "x": 330.0, "y": 60.0,
        "latitude": 13.0645, "longitude": 80.2281,
        "icu": 4, "er": 0.25,
        "specialists": {"neuro": "free", "trauma": "surgery"},
        "blood": [4, 7, 2, 5, 2, 4, 1, 3]
    },
    {
        "id": "demo-hospital-11",
        "name": "Civic Burns Centre",
        "x": 250.0, "y": 180.0,
        "latitude": 13.0334, "longitude": 80.2687,
        "icu": 3, "er": 0.50,
        "specialists": {"burns": "free", "ortho": "free"},
        "blood": [3, 6, 1, 4, 1, 3, 1, 2]
    },
    {
        "id": "demo-hospital-12",
        "name": "Northgate Cardiac",
        "x": 240.0, "y": 110.0,
        "latitude": 13.1256, "longitude": 80.2412,
        "icu": 4, "er": 0.40,
        "specialists": {"cardiac": "free"},
        "blood": [4, 8, 3, 6, 2, 5, 1, 3]
    },
    {
        "id": "demo-hospital-13",
        "name": "East End General",
        "x": 470.0, "y": 200.0,
        "latitude": 13.0211, "longitude": 80.2745,
        "icu": 3, "er": 0.70,
        "specialists": {"trauma": "free", "ortho": "free", "cardiac": "surgery"},
        "blood": [3, 7, 2, 5, 1, 4, 1, 2]
    },
    {
        "id": "demo-hospital-14",
        "name": "Southpoint Trauma",
        "x": 330.0, "y": 330.0,
        "latitude": 12.9784, "longitude": 80.2184,
        "icu": 5, "er": 0.30,
        "specialists": {"trauma": "free", "neuro": "free", "ortho": "free", "burns": "surgery"},
        "blood": [5, 11, 4, 8, 3, 6, 2, 4]
    },
    {
        "id": "demo-hospital-15",
        "name": "Lakeview Hospital",
        "x": 40.0, "y": 330.0,
        "latitude": 13.0621, "longitude": 80.1834,
        "icu": 2, "er": 0.45,
        "specialists": {"ortho": "free", "cardiac": "free"},
        "blood": [2, 4, 1, 3, 1, 3, 0, 1]
    }
]


def seed_hospitals():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    now = datetime.now(timezone.utc)
    try:
        print(f"Seeding {len(HOSPITALS_SPEC)} synthetic hospitals...")
        for spec in HOSPITALS_SPEC:
            h = db.query(Hospital).filter(Hospital.id == spec["id"]).first()
            if not h:
                h = Hospital(
                    id=spec["id"],
                    name=spec["name"],
                    is_demo=True,
                    x=spec["x"],
                    y=spec["y"],
                    latitude=spec["latitude"],
                    longitude=spec["longitude"],
                    accepting_status="accepting",
                    icu_capacity=6,
                    icu_available=spec["icu"],
                    er_load=spec["er"],
                    source="demo_seed",
                    updated_at=now,
                    last_verified_at=now
                )
                db.add(h)
                db.flush()
            else:
                h.name = spec["name"]
                h.x = spec["x"]
                h.y = spec["y"]
                h.latitude = spec["latitude"]
                h.longitude = spec["longitude"]
                h.icu_available = spec["icu"]
                h.er_load = spec["er"]
                h.updated_at = now

            # Specialists
            all_specs = ["trauma", "neuro", "cardiac", "ortho", "burns"]
            for sp in all_specs:
                status = spec["specialists"].get(sp, "unavailable")
                s_rec = db.query(SpecialistAvailability).filter(
                    SpecialistAvailability.hospital_id == h.id,
                    SpecialistAvailability.specialty == sp
                ).first()
                if not s_rec:
                    s_rec = SpecialistAvailability(
                        hospital_id=h.id,
                        specialty=sp,
                        status=status,
                        doctor_name=DOCTOR_NAMES.get(sp),
                        expected_free_mins=12 if status == "surgery" else None,
                        source="demo_seed",
                        updated_at=now
                    )
                    db.add(s_rec)
                else:
                    s_rec.status = status
                    s_rec.updated_at = now

            # Blood inventory
            for i, bg in enumerate(BLOOD_GROUPS):
                units = spec["blood"][i] if i < len(spec["blood"]) else 2
                b_rec = db.query(BloodInventory).filter(
                    BloodInventory.hospital_id == h.id,
                    BloodInventory.blood_group == bg
                ).first()
                if not b_rec:
                    b_rec = BloodInventory(
                        hospital_id=h.id,
                        blood_group=bg,
                        units_available=units,
                        units_reserved=0,
                        source="demo_seed",
                        updated_at=now
                    )
                    db.add(b_rec)
                else:
                    b_rec.units_available = units
                    b_rec.updated_at = now

        db.commit()
        print("Synthetic hospital seed completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_hospitals()
