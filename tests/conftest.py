import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.config import settings
from backend.app.core.security import hash_password, generate_session_token, hash_session_token
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.models.user import User
from backend.app.models.session import SessionModel
from backend.app.models.hospital import Hospital, SpecialistAvailability, BloodInventory

# Create an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    expire_on_commit=False
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seed_test_data(db_session):
    now = datetime.now(timezone.utc)

    # 1. Seed test hospitals
    h1 = Hospital(
        id="demo-hospital-1",
        name="Apex Trauma Center",
        is_demo=True,
        x=430.0, y=90.0,
        latitude=13.0827, longitude=80.2707,
        accepting_status="accepting",
        icu_capacity=6,
        icu_available=5,
        er_load=0.45,
        source="demo_seed",
        updated_at=now
    )
    h2 = Hospital(
        id="demo-hospital-2",
        name="City Care Clinic",
        is_demo=True,
        x=120.0, y=100.0,
        latitude=13.0569, longitude=80.2425,
        accepting_status="accepting",
        icu_capacity=6,
        icu_available=1,
        er_load=0.80,
        source="demo_seed",
        updated_at=now
    )
    h_closed = Hospital(
        id="demo-hospital-closed",
        name="Closed Regional Center",
        is_demo=True,
        x=300.0, y=150.0,
        latitude=13.0600, longitude=80.2500,
        accepting_status="not_accepting",
        icu_capacity=6,
        icu_available=0,
        er_load=0.95,
        source="demo_seed",
        updated_at=now
    )
    db_session.add_all([h1, h2, h_closed])
    db_session.flush()

    # Add specialists
    for h in [h1, h2]:
        s_trauma = SpecialistAvailability(
            hospital_id=h.id,
            specialty="trauma",
            status="free" if h.id == "demo-hospital-1" else "none",
            doctor_name="Dr. Mehta" if h.id == "demo-hospital-1" else None,
            source="demo_seed",
            updated_at=now
        )
        s_cardiac = SpecialistAvailability(
            hospital_id=h.id,
            specialty="cardiac",
            status="free",
            doctor_name="Dr. Rao",
            source="demo_seed",
            updated_at=now
        )
        db_session.add_all([s_trauma, s_cardiac])

    # Add blood
    for h in [h1, h2]:
        for bg in ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]:
            b = BloodInventory(
                hospital_id=h.id,
                blood_group=bg,
                units_available=8 if h.id == "demo-hospital-1" else 1,
                source="demo_seed",
                updated_at=now
            )
            db_session.add(b)

    # 2. Seed test users
    amb_user = User(
        username="ambulance.demo",
        password_hash=hash_password("AmbSecret123!"),
        role="ambulance",
        hospital_id=None,
        is_active=True,
        created_at=now,
        updated_at=now
    )
    hosp_user = User(
        username="hospital.demo",
        password_hash=hash_password("HospSecret123!"),
        role="hospital",
        hospital_id="demo-hospital-1",
        is_active=True,
        created_at=now,
        updated_at=now
    )
    hosp2_user = User(
        username="hospital2.demo",
        password_hash=hash_password("Hosp2Secret123!"),
        role="hospital",
        hospital_id="demo-hospital-2",
        is_active=True,
        created_at=now,
        updated_at=now
    )
    db_session.add_all([amb_user, hosp_user, hosp2_user])
    db_session.commit()

    return {
        "ambulance_user": amb_user,
        "hospital_user": hosp_user,
        "hospital2_user": hosp2_user,
        "hospital_1": h1,
        "hospital_2": h2,
        "hospital_closed": h_closed
    }
