@echo off
echo ========================================================
echo Golden Hour Grid - Local Development Server
echo ========================================================

REM Run demo user and data seeding if database does not exist
python scripts/seed_demo_data.py
python scripts/seed_demo_users.py --ambulance-password "AmbDemoPass2026!" --hospital-password "HospDemoPass2026!"

echo Starting FastAPI server at http://127.0.0.1:8000 ...
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
