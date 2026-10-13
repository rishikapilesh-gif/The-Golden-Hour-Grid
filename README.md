# 🚑 Golden Hour Grid

**Emergency Response Hospital & Resource Coordination Engine**  
*A modular, full-stack operational decision-support prototype for acute golden-hour emergency transit.*

> [!IMPORTANT]
> **RESEARCH & HACKATHON PROTOTYPE NOTICE:**  
> Golden Hour Grid is an experimental decision-support prototype. It is **NOT** a live dispatch service and does **NOT** communicate with real hospitals, emergency dispatchers, 911/112/108 services, or blood banks. All facility names, locations, bed counts, blood inventories, specialist rosters, and transit routes are synthetic demonstration fixtures.

---

## 🌟 Key Capabilities & Features

1. **Unified Single-Origin Architecture (Zero-Conflict Hosting):**
   - FastAPI serves both the secure backend REST/WebSocket APIs and the responsive web client directly from the same port and domain.
   - **No separate Node.js / npm build step required.**
   - Zero CORS complications, zero cookie domain mismatches, zero reverse-proxy overhead.

2. **Role-Scoped Operations Workspaces (Strict Private Access):**
   - **Ambulance Workspace (`/ambulance`):** Incident triage intake (trauma, neuro, cardiac, burns, vitals PaO₂/SpO₂/HR, weather/railway hazards), explainable deterministic hospital ranking, and interactive transit navigation.
   - **Hospital Command Workspace (`/hospital`):** Incoming transit queue, one-click accept/decline, active bay dossier, live approaching ambulance map, attending doctor paging/dispatch, bay readiness checklist, and clinical handover completion.

3. **Interactive Real Road Map & Moving Ambulance Simulation:**
   - Real street-level road network tiles (OpenStreetMap / Google Maps Platform adapter).
   - Smooth animated ambulance marker with flashing emergency beacon light that rotates along genuine road curves.
   - Live Telemetry HUD: Real-time countdown ETA, distance remaining, transit speed, and corridor green-wave signal status.
   - Playback speed controls (`1x`, `2x`, `4x`, pause, and reset).

4. **Safety-First Deterministic Ranking Engine:**
   - Score calculated purely from clinical specialty match, verified blood bank readiness, ER load, ICU beds, and live transit ETA.
   - **Zero AI hallucinations in patient routing:** Language models never select or override hospital rankings.
   - Gender-invariant; no diagnostic survival percentages.

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.11 or higher
- Git

### Option A: Windows 1-Click Launch
Double-click `scripts/run_dev.bat` or run in PowerShell:
```powershell
.\scripts\run_dev.ps1
```
The server will automatically seed the database and launch at `http://127.0.0.1:8000`.

### Option B: Cross-Platform (Mac / Linux / Windows Manual)
```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Seed demonstration data & accounts
python scripts/seed_demo_data.py
python scripts/seed_demo_users.py --ambulance-password "AmbDemoPass2026!" --hospital-password "HospDemoPass2026!"

# 4. Launch FastAPI server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open **`http://127.0.0.1:8000`** in your browser.

---

## 🔑 Demonstration Accounts

| Role | Username | Password | Default Assigned Facility |
| :--- | :--- | :--- | :--- |
| **Ambulance Operator** | `ambulance.demo` | `AmbDemoPass2026!` | Field Unit (Apex Sector) |
| **Hospital ER Command** | `hospital.demo` | `HospDemoPass2026!` | Apex Trauma Center (`demo-hospital-1`) |

---

## 📦 How to Upload to GitHub

Follow these steps to push this folder to your GitHub account:

```bash
# 1. Initialize git inside this folder
git init

# 2. Add all files
git add .

# 3. Commit
git commit -m "feat: complete Golden Hour Grid with unified backend, interactive road map, and hospital clinical dossier"

# 4. Create a new repository on GitHub (e.g. 'golden-hour-grid') and link it:
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPOSITORY_NAME>.git

# 5. Push to GitHub
git push -u origin main
```

---

## ☁️ 1-Click Cloud Hosting (Backend + Frontend Together)

Because the project is packaged as a single-origin service, **the backend and frontend run together on a single cloud service** with no extra costs or moving parts.

### Option 1: Deploy on Render (Recommended · Free)
1. Log in to [Render.com](https://render.com).
2. Click **New +** -> **Web Service**.
3. Connect your new GitHub repository.
4. Render will auto-detect Python. Configure:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `bash scripts/start.sh`
5. In **Environment Variables**, add:
   - `DEMO_MODE` = `true`
   - `DEMO_AMBULANCE_PASSWORD` = `AmbDemoPass2026!`
   - `DEMO_HOSPITAL_PASSWORD` = `HospDemoPass2026!`
   - `SESSION_COOKIE_SECURE` = `true`
6. Click **Create Web Service**. Your live HTTPS URL will be ready in ~90 seconds!

*(Alternatively, connect the repository using Render Blueprint which will read `render.yaml` automatically).*

---

### Option 2: Deploy on Railway
1. Log in to [Railway.app](https://railway.app).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select your repository. Railway detects the `Dockerfile` / `railway.json` and builds automatically.
4. Add environment variables:
   - `DEMO_MODE` = `true`
   - `DEMO_AMBULANCE_PASSWORD` = `AmbDemoPass2026!`
   - `DEMO_HOSPITAL_PASSWORD` = `HospDemoPass2026!`
5. Click **Deploy**. Under service settings, generate a domain.

---

### Option 3: Run with Docker / Docker Compose
To run locally or on any Linux VPS with Docker:
```bash
docker compose up --build
```
Access at `http://localhost:8000`.

---

## 🧪 Testing & Verification

Run the automated test suite covering unit tests, integration routes, authorization boundaries, and full end-to-end scenarios:
```bash
python -m pytest
```
All 23 tests pass with zero failures.

---

## 📁 Project Structure

```text
├── Dockerfile                  # Container build specification
├── docker-compose.yml          # 1-command local container orchestration
├── Procfile                    # PaaS process manager configuration
├── render.yaml                 # Render Blueprint configuration
├── railway.json                # Railway deployment configuration
├── requirements.txt            # Pinned Python package dependencies
├── .env.example                # Safe environment variable template
├── .gitignore                  # Git ignore rules for secrets and databases
│
├── backend/
│   └── app/
│       ├── main.py             # FastAPI entrypoint, SPA routing & WebSocket gateway
│       ├── api/routes/         # Auth, incidents, hospitals, hospital command, routing
│       ├── core/               # App configuration, security, Argon2id crypto
│       ├── db/                 # SQLAlchemy sessions, models base
│       ├── models/             # Hospital, incident, session, user models
│       ├── providers/          # Road routing adapters (OSRM, Google Routes, Demo)
│       ├── realtime/           # WebSocket broadcast hub
│       ├── schemas/            # Pydantic request/response schemas
│       └── services/           # Deterministic ranking engine, auth service
│
├── frontend/
│   ├── index.html              # Two-role operational interface & map containers
│   ├── styles.css              # TNEA-inspired public-sector design system
│   └── app.js                  # Map animation, Leaflet renderer, state & telemetry
│
├── scripts/
│   ├── seed_demo_data.py       # Seeds 15 synthetic hospitals, blood & specialists
│   ├── seed_demo_users.py      # Seeds demo ambulance & hospital accounts
│   ├── run_dev.bat             # Windows batch startup script
│   ├── run_dev.ps1             # PowerShell startup script
│   └── start.sh                # Linux / Container / Cloud hosting entrypoint
│
├── docs/                       # Architecture, API contract, and safety specifications
└── tests/                      # Pytest unit, integration, and E2E suites
```

---

## ⚖️ License & Ethical Safeguards

Developed for hackathon demonstration and research into acute medical transit logistics. Protected under standard MIT open-source terms. Field deployments require integration with authorized municipal health APIs and clinical governance review.
