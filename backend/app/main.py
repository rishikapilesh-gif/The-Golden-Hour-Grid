import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.base import Base
from backend.app.db.session import engine, get_db, SessionLocal
from backend.app.services.auth_service import AuthService
from backend.app.realtime.notifier import notifier
from backend.app.providers.resources.demo_feed import demo_feed

# Import models to ensure they are registered with metadata
import backend.app.models  # noqa

# Import routers
from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.hospitals import router as hospitals_router
from backend.app.api.routes.hospital_command import router as hospital_command_router
from backend.app.api.routes.incidents import router as incidents_router
from backend.app.api.routes.demo import router as demo_router
from backend.app.api.routes.assistant import router as assistant_router
from backend.app.api.routes.routing import router as routing_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist
    Base.metadata.create_all(bind=engine)

    # Auto-seed initial demo dataset if empty and DEMO_MODE is true
    if settings.DEMO_MODE:
        try:
            with SessionLocal() as db:
                from backend.app.models.hospital import Hospital
                from backend.app.models.user import User
                if db.query(Hospital).count() == 0:
                    from scripts.seed_demo_data import seed_hospitals
                    seed_hospitals()
                if db.query(User).count() == 0:
                    from scripts.seed_demo_users import seed_users
                    amb_pw = (
                        settings.DEMO_AMBULANCE_PASSWORD
                        if settings.DEMO_AMBULANCE_PASSWORD != "CHANGE_ME_BEFORE_LOCAL_DEMO"
                        else "AmbDemoPass2026!"
                    )
                    hosp_pw = (
                        settings.DEMO_HOSPITAL_PASSWORD
                        if settings.DEMO_HOSPITAL_PASSWORD != "CHANGE_ME_BEFORE_LOCAL_DEMO"
                        else "HospDemoPass2026!"
                    )
                    seed_users(ambulance_pw=amb_pw, hospital_password=hosp_pw)
        except Exception as e:
            print(f"Notice: Initial auto-seed skipped or completed: {e}")

    # Start synthetic demo feed if enabled
    demo_feed.start()
    yield
    # Shutdown: stop feed
    demo_feed.stop()


app = FastAPI(
    title="Golden Hour Grid API",
    description="Emergency Response Hospital & Resource Coordination Engine (Research/Prototype)",
    version="2.0.0",
    lifespan=lifespan
)

# Register API routers
app.include_router(auth_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(hospitals_router, prefix="/api")
app.include_router(hospital_command_router, prefix="/api")
app.include_router(incidents_router, prefix="/api")
app.include_router(demo_router, prefix="/api")
app.include_router(assistant_router, prefix="/api")
app.include_router(routing_router, prefix="/api")


# WebSocket updates endpoint
@app.websocket("/ws/updates")
async def websocket_updates(
    websocket: WebSocket,
    token: str | None = Query(None)
):
    # Check session cookie or query token
    cookie_token = websocket.cookies.get(settings.SESSION_COOKIE_NAME)
    auth_token = cookie_token or token

    db = SessionLocal()
    user = None
    try:
        if auth_token:
            user = AuthService.get_user_from_token(db, auth_token)
    finally:
        db.close()

    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await notifier.connect(websocket, user)
    try:
        while True:
            # Keep-alive loop; receive incoming pings from client
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        notifier.disconnect(websocket)
    except Exception:
        notifier.disconnect(websocket)


# Frontend static files and SPA route handling
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR)), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/login")
    async def serve_login():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/ambulance")
    async def serve_ambulance():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/hospital")
    async def serve_hospital():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/styles.css")
    async def serve_css():
        return FileResponse(FRONTEND_DIR / "styles.css")

    @app.get("/app.js")
    async def serve_js():
        return FileResponse(FRONTEND_DIR / "app.js")
