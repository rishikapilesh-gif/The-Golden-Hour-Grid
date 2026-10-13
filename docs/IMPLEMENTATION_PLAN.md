# Golden Hour Grid — Implementation Plan

## Stage 0 — Asset and behavior audit
- Read the entire current V2 HTML and inspect its screenshot.
- Inventory all fields, buttons, scenarios, timers, data arrays, demo feed intervals, route calculations, rank weights and browser-local AI code.
- Record what works, what is simulated, what needs backend authority, and any misleading legacy output to remove (especially survival percentages or claims of actual confirmation).
- Preserve an unchanged copy under `docs/legacy/`.

## Stage 1 — Skeleton, login and baseline
- Create a FastAPI project with settings, health route, auth routes, session persistence, server-side role guards, logging, static frontend serving, and local startup instructions.
- Add the compact login-first view plus separate `/ambulance` and `/hospital` workspaces. Do not add public registration or unrelated features.
- Create `User` and `Session` models; seed exactly two local demo accounts only when demo mode and environment-configured passwords are present.
- Move/refactor existing UI to HTML/CSS/JS without changing its visual identity. Keep ambulance intake/ranking compact; keep hospital incoming cases/resources separate.
- Establish `.env.example`, `.gitignore`, dependencies, and smoke/authz tests.

Acceptance: app launches locally; login works; correct role redirects; logout revokes session; anonymous requests are denied; hospital cannot access ambulance-only mutations and cannot edit another hospital; UI loads from backend origin; `/api/health` responds; no secret or live-data claim.

## Stage 2 — Operational data persistence and synthetic seed data
- SQLAlchemy models/repositories for hospitals, resources, specialists, blood inventory, incidents, recommendations, coordination requests and audit events. Keep `User` and `Session` models from Stage 1.
- SQLite development database plus deterministic demo seed script.
- Record `is_demo`, source, updated timestamps and freshness.

Acceptance: seeded data persists after restart; seed is repeatable; fixture sources clearly identify synthetic data.

## Stage 3 — Incident intake API
- Validate and persist all UI inputs and units.
- Store the incident state and return stable IDs; implement read/status endpoints.
- Keep observed vitals separate; never silently diagnose or infer treatment.

Acceptance: invalid inputs are rejected with understandable errors; valid incident can be created/read.

## Stage 4 — Routing adapter and ranker
- Implement demo route estimate and route alternative model with hazard reasons.
- Implement deterministic ranking and explainable components/reasons.
- Make ranking use backend resource snapshots, not browser fixture constants.
- Add human override and audit reason.

Acceptance: rank #1 is highest-scoring eligible hospital; scores are repeatable; ranking updates as route/hospital inputs change.

## Stage 5 — Blood and specialist coordination state machines
- Detect a low/missing reported stock in the selected hospital and create one staged request in a demo queue, pending human approval and blood-bank verification/cross-match.
- Stage specialist pre-alert, with honest accepted/declined/unavailable demo status.
- Add status/history views and audit events.

Acceptance: no real message/call/order is claimed; duplicate requests are prevented; all states can be inspected.

## Stage 6 — Resource events and live-style updates
- Add WebSocket event gateway and polling fallback.
- Add demo-only seeded resource updater for ICU, ER load, blood stock, specialists.
- Recompute active rankings when a relevant resource changes and refresh both UI panes.

Acceptance: UI shows source/time/demo state; a controlled test update causes a new ranking/version; demo feed is disabled outside demo mode.

## Stage 7 — Optional local AI adapter
- Add disabled-by-default server-side Ollama/LM Studio integration.
- AI returns a bounded non-clinical operational checklist only.
- Add timeouts, safe output handling and fallback.

Acceptance: AI off or unavailable does not affect main operations; no ranking changes from AI output.

## Stage 8 — Validation and delivery
- Unit/integration/E2E tests; responsive browser inspection; API docs; architecture, data dictionary, limitations and troubleshooting docs.
- Report real command output and remaining blockers; do not report an integration as live if it has only a stub.

Acceptance: README can be followed from a clean local checkout and the end-to-end demo workflow is repeatable.


## Real road-map acceptance

Before declaring routing complete, finish the requirements in `docs/REAL_MAP_AND_ROUTING.md`: render a detailed actual road map in roadmap mode, use provider-returned route geometry, integrate traffic-aware ETA where configured, and never show the current schematic SVG in an operational role workspace. Verify missing-key and provider-error behavior.

## TNEA-inspired UI acceptance

Follow `docs/UI_DESIGN_REFERENCE_TNEA.md`. The result should have an official public-sector visual tone—restrained navy, white, cool-gray borders, green/amber/gray status labels and clear headings—but retain Golden Hour Grid identity and avoid unauthorized government seals or affiliation claims.
