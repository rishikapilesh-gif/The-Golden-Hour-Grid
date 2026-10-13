import sys
import os
import argparse
from datetime import datetime, timezone

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.core.security import hash_password
from backend.app.db.base import Base
from backend.app.db.session import engine, SessionLocal
from backend.app.models.user import User


def seed_users(ambulance_pw: str | None = None, hospital_password: str | None = None):
    if not settings.DEMO_MODE:
        print("ERROR: Demo account seeding is disabled when DEMO_MODE=false.")
        sys.exit(1)

    amb_username = settings.DEMO_AMBULANCE_USERNAME
    amb_password = ambulance_pw or settings.DEMO_AMBULANCE_PASSWORD
    hosp_username = settings.DEMO_HOSPITAL_USERNAME
    hosp_password = hospital_password or settings.DEMO_HOSPITAL_PASSWORD
    hosp_id = settings.DEMO_HOSPITAL_ID

    # Validation: refuse to seed with placeholder or empty password
    placeholder = "CHANGE_ME_BEFORE_LOCAL_DEMO"
    if not amb_password or amb_password == placeholder:
        print(f"ERROR: DEMO_AMBULANCE_PASSWORD is still set to placeholder '{placeholder}'.")
        print("Please set a real local password in .env or provide --ambulance-password.")
        sys.exit(1)

    if not hosp_password or hosp_password == placeholder:
        print(f"ERROR: DEMO_HOSPITAL_PASSWORD is still set to placeholder '{placeholder}'.")
        print("Please set a real local password in .env or provide --hospital-password.")
        sys.exit(1)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    now = datetime.now(timezone.utc)
    try:
        # 1. Seed or update ambulance user
        amb_user = db.query(User).filter(User.username == amb_username.lower()).first()
        amb_hash = hash_password(amb_password)
        if not amb_user:
            amb_user = User(
                username=amb_username.lower(),
                password_hash=amb_hash,
                role="ambulance",
                hospital_id=None,
                is_active=True,
                created_at=now,
                updated_at=now
            )
            db.add(amb_user)
            print(f"Created ambulance user: {amb_username}")
        else:
            amb_user.password_hash = amb_hash
            amb_user.role = "ambulance"
            amb_user.updated_at = now
            print(f"Updated ambulance user: {amb_username}")

        # 2. Seed or update hospital user
        hosp_user = db.query(User).filter(User.username == hosp_username.lower()).first()
        hosp_hash = hash_password(hosp_password)
        if not hosp_user:
            hosp_user = User(
                username=hosp_username.lower(),
                password_hash=hosp_hash,
                role="hospital",
                hospital_id=hosp_id,
                is_active=True,
                created_at=now,
                updated_at=now
            )
            db.add(hosp_user)
            print(f"Created hospital user: {hosp_username} bound to {hosp_id}")
        else:
            hosp_user.password_hash = hosp_hash
            hosp_user.role = "hospital"
            hosp_user.hospital_id = hosp_id
            hosp_user.updated_at = now
            print(f"Updated hospital user: {hosp_username} bound to {hosp_id}")

        db.commit()
        print("Demo user seeding completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed demo ambulance and hospital accounts.")
    parser.add_argument("--ambulance-password", type=str, help="Password for ambulance demo user")
    parser.add_argument("--hospital-password", type=str, help="Password for hospital demo user")
    args = parser.parse_args()

    seed_users(
        ambulance_pw=args.ambulance_password,
        hospital_password=args.hospital_password
    )
