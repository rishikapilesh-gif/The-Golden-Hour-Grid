Here is the complete, professional, non-AI-slop `README.md` written in standard engineering documentation style. You can copy and paste the code block below directly into your repository:

```markdown
# Golden Hour Grid

**Deterministic emergency response & clinical destination coordination engine for acute medical transit.**

[![Build & Tests](https://img.shields.io/badge/tests-23%20passed-2ea44f?style=flat-square)](./tests)
[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue?style=flat-square)](https://python.org)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI%20%2F%20SQLAlchemy%202.x-009688?style=flat-square)](https://fastapi.tiangolo.com)
[![Architecture](https://img.shields.io/badge/architecture-single--origin%20%2F%20zero--build-4682b4?style=flat-square)](#architecture)
[![License](https://img.shields.io/badge/license-MIT-informational?style=flat-square)](./LICENSE)

---

> ### ⚠️ Operational Scope & Clinical Research Notice
> Golden Hour Grid is an open-source technical prototype and logistical demonstration. It is **not** an operational emergency dispatch service, does **not** integrate with municipal emergency lines (911 / 112 / 108), and does **not** provide medical diagnosis or survival probability calculations. 
> 
> All facility registries, bed capacities, blood bank counts, physician schedules, and road geometries bundled in this repository are **synthetic demonstration data**. Real-world deployment requires integration with authorized local healthcare APIs and institutional clinical governance review.

---

## Overview

In acute trauma, neurovascular crises, and cardiovascular emergencies, patient outcomes depend directly on transit time to a facility with matching active capabilities—not merely the geographically closest building.

**Golden Hour Grid** provides a low-latency, role-segregated operational coordination platform for ambulance crews and hospital emergency departments:

- **Ambulance Workstation (`/ambulance`):** Rapid incident intake, vital metric logging (PaO₂, SpO₂, Heart Rate), route hazard identification, and deterministic multi-criteria hospital ranking.
- **Hospital Command Console (`/hospital`):** Real-time incoming case queue, one-click bay acceptance/decline, approaching vehicle road telemetry, attending physician paging, and formal clinical handover signoff.

The platform eliminates black-box AI from life-critical routing decisions: ranking is **100% deterministic, explainable, and mathematically auditable**.

---

## System Architecture

The project runs as a unified **single-origin service**: FastAPI simultaneously manages authenticated REST/WebSocket endpoints and directly delivers the frontend client.

```
                          [ Client Browser ]
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
         HTTP / Static Assets            WebSocket (/ws/updates)
        (HTML / CSS / Leaflet)          (State Synchronization)
                  │                               │
                  └───────────────┬───────────────┘
                                  ▼
                     [ FastAPI Application ]
                      ├── Role Authorization (Argon2id)
                      ├── Deterministic Ranking Engine
                      ├── Routing & Hazard Adapters
                      └── Clinical Handover Service
                                  │
                                  ▼
                     [ SQLAlchemy ORM 2.x ]
                      ├── SQLite (Local Dev / Demo)
                      └── PostgreSQL (Production Ready)
```

### Key Technical Decisions
* **Zero-Build Frontend Pipeline:** The web client uses modern vanilla ES6 modules, CSS variables, and Leaflet CDN maps. No Node.js runtime, Webpack/Vite bundlers, or `node_modules` overhead required.
* **Zero CORS / Domain Mismatch:** Frontend assets and API routes share the exact same host and port, ensuring strict `HttpOnly`, `SameSite` session cookies operate seamlessly.
* **Deterministic Scoring Model:** Facilities are ranked via an explainable score weighted by specialty readiness, ER saturation, available ICU capacity, blood unit compatibility, and road transit ETA. Patient gender and demographic attributes are strictly invariant in ranking.

---

## Operational Workspaces

### 1. Ambulance Triage & Transit
- Real-time road map displaying actual road-network geometry.
- Animated vehicle marker with directional heading rotation and active hazard indicators (floods, railway crossings, roadblocks).
- Live telemetry HUD reporting countdown ETA, distance remaining, velocity, and traffic corridor green-wave status.
- Playback controls (`1x`, `2x`, `4x`, pause) for drill rehearsals and scenario simulations.

### 2. Hospital Emergency Department Command
- Incoming transit list filtered strictly by facility scope (no cross-hospital data leakage).
- Detailed Clinical Dossier for accepted cases:
  - Approaching vehicle position and live arrival clock.
  - Reported triage vitals with automated clinical review triggers for abnormal ranges (e.g., PaO₂ < 60 mmHg, SpO₂ < 90%).
  - Staged blood bank reservation checks.
  - Attending specialist dispatch and paging (Trauma, Neuro, Cardiac, Ortho, Burns).
  - Bay readiness checklist and structured handover signoff.

---

## Quick Start

### Prerequisites
- Python 3.11 or higher
- Git

### 1. Local Setup

```bash
# Clone the repository
git clone https://github.com/<YOUR_ORGANIZATION>/golden-hour-grid.git
cd golden-hour-grid

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the automated seed script (provisions 15 hospitals and demo accounts)
python scripts/seed_demo_data.py
python scripts/seed_demo_users.py --ambulance-password "AmbDemoPass2026!" --hospital-password "HospDemoPass2026!"

# Start the application server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open **`http://127.0.0.1:8000`** in your browser.

> **Windows Users:** You can launch the environment directly by executing `scripts/run_dev.bat` or `scripts/run_dev.ps1`.

---

## Demonstration Credentials

Pre-configured accounts for verification and technical review:

| Role | Workspace Route | Username | Password | Default Scope |
| :--- | :--- | :--- | :--- | :--- |
| **Ambulance Operator** | `/ambulance` | `ambulance.demo` | `AmbDemoPass2026!` | Field Unit (Metropolitan Sector) |
| **Hospital ED Command** | `/hospital` | `hospital.demo` | `HospDemoPass2026!` | Apex Trauma Center (`demo-hospital-1`) |

---

## Production & Container Deployment

### Running with Docker Compose

A production-ready `Dockerfile` and `docker-compose.yml` are included in the repository root:

```bash
docker compose up --build -d
```
The service will auto-seed the demo database on startup and expose the application on `http://localhost:8000`.

### Deploying to Cloud Platforms (Render, Railway, Fly.io)

Because the project runs as a single service, it deploys to cloud hosts without requiring multiple services or reverse-proxy configuration:

#### Render (Web Service)
1. Link your GitHub repository in the [Render Dashboard](https://render.com).
2. Choose **Python** runtime.
3. Set **Build Command:** `pip install -r requirements.txt`
4. Set **Start Command:** `bash scripts/start.sh`
5. Configure environment variables:
   * `DEMO_MODE` = `true`
   * `DEMO_AMBULANCE_PASSWORD` = `AmbDemoPass2026!`
   * `DEMO_HOSPITAL_PASSWORD` = `HospDemoPass2026!`
   * `SESSION_COOKIE_SECURE` = `true`
6. Click **Deploy**.

#### Railway
Select **Deploy from GitHub repo**. Railway detects the root `Dockerfile` and `railway.json` and provisions the instance automatically.

---

## Testing & Quality Assurance

The test suite covers cryptographic session hashing, role authorization boundaries, routing heuristics, vital sign safeguards, and end-to-end incident lifecycles:

```bash
python -m pytest -v
```

Test coverage includes:
- Role escalation prevention (ambulance tokens cannot query hospital bay endpoints).
- Scope enforcement (hospital accounts cannot inspect or mutate neighboring hospital queues).
- Gender invariance verification in the ranking engine.
- Session invalidation upon explicit logout.

---

## Environment Configuration

Configuration is managed via environment variables (or a root `.env` file). Reference template:

```ini
APP_ENV=production
DEMO_MODE=true
DATABASE_URL=sqlite:///./golden_hour_grid.db

# Authentication & Session
SESSION_COOKIE_NAME=ghg_session
SESSION_COOKIE_SECURE=false      # Set to 'true' when deployed behind HTTPS
SESSION_TTL_MINUTES=480

# Demo Accounts
DEMO_AMBULANCE_USERNAME=ambulance.demo
DEMO_AMBULANCE_PASSWORD=AmbDemoPass2026!
DEMO_HOSPITAL_USERNAME=hospital.demo
DEMO_HOSPITAL_PASSWORD=HospDemoPass2026!
DEMO_HOSPITAL_ID=demo-hospital-1

# Mapping & Routing (Optional)
MAP_PROVIDER=auto                # 'osm', 'google', or 'auto'
ROUTING_PROVIDER=auto            # 'osrm', 'google', 'demo', or 'auto'
GOOGLE_MAPS_BROWSER_API_KEY=
GOOGLE_MAPS_ROUTES_API_KEY=
```

---

## Repository Structure

```text
├── Dockerfile                  # Container build instructions
├── docker-compose.yml          # Container service definition
├── Procfile                    # PaaS process execution entrypoint
├── render.yaml                 # Render Blueprint specification
├── railway.json                # Railway deployment configuration
├── requirements.txt            # Python dependencies
├── .env.example                # Configuration template
├── .gitignore                  # Git ignore rules
│
├── backend/app/
│   ├── main.py                 # FastAPI application, static mounting & WebSocket router
│   ├── api/routes/             # Auth, incident triage, hospital command, routing APIs
│   ├── core/                   # Security, Argon2id crypto, application settings
│   ├── db/                     # Database sessions and base models
│   ├── models/                 # User, Session, Hospital, Incident schema models
│   ├── providers/              # Road routing providers (OSRM, Google Routes, Demo)
│   ├── realtime/               # WebSocket connection manager and event broadcaster
│   ├── schemas/                # Pydantic validation schemas
│   └── services/               # Deterministic ranking engine and auth services
│
├── frontend/
│   ├── index.html              # Clean institutional two-role user interface
│   ├── styles.css              # Minimalist design system (inspired by public-sector portals)
│   └── app.js                  # Map rendering, telemetry HUD, state synchronization
│
├── scripts/
│   ├── seed_demo_data.py       # Seeds 15 synthetic facilities, blood inventory, staff
│   ├── seed_demo_users.py      # Provisions demonstration user accounts
│   ├── start.sh                # Container and cloud production entrypoint
│   └── run_dev.bat / .ps1      # Local Windows convenience launchers
│
├── docs/                       # Technical specifications, API contracts, safety docs
└── tests/                      # Automated unit, integration, and E2E test suites
```

---

## License

This project is distributed under the terms of the **MIT License**. See [LICENSE](./LICENSE) for details.
```
