# Golden Hour Grid — Private Login and Minimal Operating UI

## Product operating model
## Visual direction and map

Follow `docs/UI_DESIGN_REFERENCE_TNEA.md` for a restrained public-sector portal style inspired by the screenshots: white institutional header, navy compact navigation, light content surfaces, thin borders, readable text and explicit status labels. Do not copy the TNEA logo/emblem or imply official government affiliation. Keep the actual UI much simpler than TNEA because only ambulance and hospital operators use it.

The ambulance workspace must use a real, detailed street-road map (not the current schematic SVG, not satellite imagery). Follow `docs/REAL_MAP_AND_ROUTING.md`: map should show real road geometry, street names where available, incident and verified hospital coordinates, route polyline, distance and route-provider ETA. Default to roadmap mode and hide satellite selectors. If routing credentials/provider are missing, show setup required and do not draw a made-up route or ETA.


Golden Hour Grid is a private operational tool for two kinds of authorized users: ambulance personnel and hospital personnel. It is not a public commercial website. Optimize for speed, clarity, low cognitive load and reliable handoff—not feature breadth, marketing, discovery or customization.

## Entry and authentication

- The first page is a compact login screen. No public landing page, marketing content, self-registration, role selector, social login, or extra onboarding.
- Login form contains only username, password, Sign in, an unobtrusive connection/error area, and “Authorized personnel only”.
- The user’s role comes from the authenticated database account. Do not trust a role sent by the browser, URL query string, localStorage or request body.
- On successful login, redirect according to the role returned by the backend:
  - `ambulance` → `/ambulance`
  - `hospital` → `/hospital`
- A hospital user who requests `/ambulance` is redirected to `/hospital` or receives a clear 403 page. An ambulance user who requests `/hospital` is redirected to `/ambulance` or receives 403. The backend must reject unauthorized API calls even if a user manually crafts a request.
- No registration page. An authorized administrator creates accounts outside the ordinary operational UI. For the local demo, seed two demo users from `.env` configuration or a CLI command. Never commit actual passwords or silently use public default credentials.
- Use password hashing (Argon2id or a well-maintained equivalent). Never store or log plaintext passwords.
- Use a server-validated session in an HttpOnly cookie, SameSite protection, expiry and server-side logout/revocation. Set `Secure` on HTTPS deployments; allow a development-only localhost setting. Validate Origin for state-changing browser requests. Apply basic login throttling and generic invalid-credentials errors.
- Expose `GET /api/auth/me`, `POST /api/auth/login`, `POST /api/auth/logout`. Only login and the minimum static assets are available before authentication. Do not expose incident, resource, or coordination endpoints to anonymous users.
- Keep session/audit logging minimal and avoid storing sensitive patient data in general logs.

## Ambulance workspace — fast incident-to-destination

This is the only workspace ambulance accounts can see.

- Keep a compact split view on desktop: incident intake on one side and ranked destination recommendations on the other. On narrow screens, stack with the most important action first.
- Put the high-frequency fields first: incident location, incident/injury category, dispatcher-entered severity, witness assessment, pulse/heart rate, SpO₂, reported blood group, and route hazards. Gender is optional context only. PaO₂ is optional/advanced and clearly labelled mmHg. Keep “reported/unverified” labels where needed.
- Avoid large forms, nested menus, graphs, elaborate analytics and multiple confirmation dialogs. Use sensible defaults, short labels, keyboard navigation, validation beside the relevant field and one obvious primary action: **Find and rank hospitals**.
- After submit, show ranked hospitals immediately with #1 first. Each row should make the decision usable at a glance: rank, hospital name, indicative ETA, required capability/specialist status, ICU readiness, ER load, reported blood support, data freshness and one short “why ranked here” reason.
- Put route caveats (railway gate, roadworks, roadblock/diversion, severe weather, flood/landslide and hill/ghat road) in compact selectable controls. Do not show hazards irrelevant to the current route as verified facts.
- A dispatcher can select the recommended destination or override it with a short reason. Show request state clearly. Do not put fake survival percentages or unverified clinical advice on this screen.
- Only show the few incident statuses needed to coordinate the journey. Do not add a general public map browser or unrelated dashboards.

## Hospital workspace — incoming cases and readiness

This is the only workspace hospital accounts can see.

- Show incoming selected-hospital pre-alerts/cases first, newest/highest operational priority first, with a concise summary, reported vitals, injury category, reported blood group, ETA and data freshness.
- Put the hospital’s operational readiness in a compact strip: ICU beds available, ER load, required specialist status, and reported blood inventory. Make stale/unknown values obvious.
- Allow the authorized hospital user to acknowledge/decline an incoming case with a reason and update the resources they are authorized to manage. Persist every change and broadcast it so the ambulance recommendation can refresh.
- Blood requests appear in a short pending queue with status and timestamps. A shortage can auto-create a **demo draft/pending-approval request**, but it is not a real order. Keep real blood-bank confirmation, compatibility/cross-match and authorization outside the prototype.
- Specialist notification is a pre-alert state unless a real configured provider confirms a communication. Do not claim a call was connected when none occurred.
- Do not show ambulance intake editing controls to hospital users. Do not add public-facing hospital marketing pages, charts, settings, profile customization or other features not needed for this workflow.

## Realtime and speed expectations

- The same backend is the source of truth. Ambulance and hospital screens must see consistent incident/coordination state.
- Use WebSocket events with polling fallback; reconnect gracefully. Authenticate WebSocket connections and filter events by role: ambulance users receive dispatch-relevant resource/ranking events; hospital users receive only their own facility resource events and cases assigned to them. Show a small connection indicator and the source/freshness of resources.
- Do not block a user from continuing to see the last valid snapshot when an update channel drops. Mark it stale/disconnected rather than silently showing it as current.
- Avoid unnecessary full-page refreshes, animations, multi-step wizards, large libraries and blocking AI calls. Core login, incident creation, hospital ranking and resource display must work with the local AI disabled.
- Keep API requests lean, use loading states, prevent duplicate submission, and return concise actionable errors.

## Authorization matrix

| Action | Ambulance role | Hospital role |
|---|---:|---:|
| Create an incident | Yes | No |
| Read active incidents needed for dispatch | Yes | Only cases routed to/associated with the assigned hospital |
| Read ranked hospital recommendations | Yes | No, except a minimal display for a case sent to that hospital if needed |
| Select/override destination | Yes, with audit reason | No |
| Read assigned hospital readiness | Yes, read-only for routing | Yes |
| Update hospital ICU/ER/specialist/blood resources | No | Yes, assigned hospital only |
| Acknowledge/decline incoming case | No | Yes, assigned hospital only |
| Stage a demo blood request | Yes, for the selected destination | Hospital can review/acknowledge; no real order |
| Change user roles or create accounts | No | No |
| Access demo-only mutation endpoints | Only if separately enabled for local demo/test | Only if separately enabled for local demo/test |

Apply authorization on the backend to every endpoint and resource ID, not just by hiding buttons. A hospital user must not alter another hospital’s resources by changing an ID in the URL/body.

## Demo-account setup

Provide a documented CLI or seed script that creates exactly two easy-to-understand local test accounts (one `ambulance`, one `hospital`) using `DEMO_AMBULANCE_USERNAME`, `DEMO_AMBULANCE_PASSWORD`, `DEMO_HOSPITAL_USERNAME`, `DEMO_HOSPITAL_PASSWORD`, and `DEMO_HOSPITAL_ID` from `.env`. Show the usernames in local setup instructions only if seeded. Do not commit passwords. When not in explicit local demo mode, disable demo account seeding and require an administrator-created account. A real deployment must use individually assigned institutional accounts, not shared role-wide credentials.

## Definition of the simplified product

The first successful login should reach the role’s task screen directly. Within a few seconds, an authorized user should be able to identify the next important action. Implement the incident, ranked destination, hospital readiness, blood-request and specialist-prealert workflow first. Anything beyond those two workflows is out of scope unless required for security, accessibility, reliability or auditability.
