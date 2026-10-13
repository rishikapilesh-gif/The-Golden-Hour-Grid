Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Golden Hour Grid - Local Development Server" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# Run synthetic seed data and demo users
python scripts/seed_demo_data.py
python scripts/seed_demo_users.py --ambulance-password "AmbDemoPass2026!" --hospital-password "HospDemoPass2026!"

Write-Host "Starting FastAPI server on http://127.0.0.1:8000 ..." -ForegroundColor Green
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
