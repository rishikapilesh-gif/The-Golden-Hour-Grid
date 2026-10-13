import asyncio
import random
import logging
from datetime import datetime, timezone
from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.services.hospital_service import HospitalService
from backend.app.schemas.hospital import HospitalResourceUpdate

logger = logging.getLogger("demo_feed")

BLOOD_GROUPS = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]
SPECIALTY_KEYS = ["trauma", "neuro", "cardiac", "ortho", "burns"]


class DemoFeedWorker:
    def __init__(self):
        self.running = False
        self._task: asyncio.Task | None = None

    def start(self):
        if not settings.DEMO_MODE or not settings.DEMO_FEED_ENABLED:
            logger.info("Demo resource feed is disabled.")
            return
        self.running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Demo resource feed started with {settings.DEMO_FEED_INTERVAL_SECONDS}s interval.")

    def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Demo resource feed stopped.")

    async def _run_loop(self):
        while self.running:
            try:
                await asyncio.sleep(settings.DEMO_FEED_INTERVAL_SECONDS)
                await self.step_mutation()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in demo feed step: {e}")

    async def step_mutation(self):
        db = SessionLocal()
        try:
            hospitals = HospitalService.get_all_hospitals(db)
            if not hospitals:
                return

            h = random.choice(hospitals)
            mutation_type = random.random()

            if mutation_type < 0.28:
                # Mutate ICU
                old_icu = h.icu_available
                new_icu = max(0, min(6, old_icu + (1 if random.random() < 0.55 else -1)))
                await HospitalService.update_resources(
                    db, h.id,
                    HospitalResourceUpdate(icu_available=new_icu),
                    source="demo_feed"
                )
            elif mutation_type < 0.55:
                # Mutate ER load
                old_er = h.er_load
                delta = 0.08 if random.random() < 0.5 else -0.08
                new_er = round(max(0.1, min(0.98, old_er + delta)), 2)
                await HospitalService.update_resources(
                    db, h.id,
                    HospitalResourceUpdate(er_load=new_er),
                    source="demo_feed"
                )
            elif mutation_type < 0.78:
                # Mutate Blood
                bg = random.choice(BLOOD_GROUPS)
                b_rec = next((b for b in h.blood_inventories if b.blood_group == bg), None)
                old_u = b_rec.units_available if b_rec else 2
                new_u = max(0, min(16, old_u + (1 if random.random() < 0.55 else -1)))
                await HospitalService.update_resources(
                    db, h.id,
                    HospitalResourceUpdate(blood={bg: new_u}),
                    source="demo_feed"
                )
            else:
                # Mutate Specialist
                sp = random.choice(SPECIALTY_KEYS)
                s_rec = next((s for s in h.specialists if s.specialty == sp), None)
                old_s = s_rec.status if s_rec else "unknown"
                new_s = "surgery" if old_s in ("free", "available") else "free"
                await HospitalService.update_resources(
                    db, h.id,
                    HospitalResourceUpdate(specialists={sp: new_s}),
                    source="demo_feed"
                )
        finally:
            db.close()


demo_feed = DemoFeedWorker()
