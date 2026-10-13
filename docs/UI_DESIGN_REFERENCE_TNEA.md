# TNEA-Inspired Public-Sector UI Direction for Golden Hour Grid

## Purpose and source analysis

This is a design interpretation of the user-supplied TNEA 2026 screenshots and the publicly accessible TNEA portal at https://www.tneaonline.org/. It is not a pixel-perfect reproduction and does not authorize use of TNEA branding.

The screenshots show these visual patterns:

1. **Institutional header:** white horizontal band; emblem/identity on the left; a highly visible, centered institutional title hierarchy; one small login action aligned right.
2. **Persistent navigation:** dark navy left column with compact labels, simple document-style icons, consistent row spacing, and independent vertical scrolling.
3. **Reading-first content:** white content surface on very light gray/blue background; dark text; thin cool-gray separators/borders; muted slate explanatory text; generous enough line height for longer notices.
4. **Strong typography hierarchy:** bold page/section headings, ordinary body text, clear secondary descriptions; bilingual Tamil/English appears when needed rather than as decorative copy.
5. **Explicit status vocabulary:** green completed, amber in progress, muted gray not started. In the emergency tool, adapt this to confirmed/ready, pending, stale/unknown, unavailable, and failed—with text labels, not color alone.
6. **Conventional actions:** clear text links and simple buttons; limited animation and no marketing hero.
7. **Moderate component styling:** panels have clear borders and restrained rounding; shadows are subtle. Information is presented as operational content, not promotional feature cards.

## Golden Hour Grid design translation

Golden Hour Grid is a private two-role emergency operations tool. Borrow the *public-sector clarity* but not the TNEA-specific navigation density. The user has only a few time-critical tasks, so the application must be even simpler than the admissions portal.

### Shared shell

- Login is the first route. Use a clean white header with the original project identity: **GOLDEN HOUR GRID** and subtitle **EMERGENCY RESPONSE COORDINATION**.
- Use dark navy for compact top-level identity/navigation, white for content surfaces, very light cool-gray page background, government-service-style green for successful/ready states, blue for primary navigation/action, amber for pending/caution, and red only for critical/failed states.
- Use a standard readable sans-serif/system font stack. Do not add large display fonts, neon gradients, glassmorphism, animated backgrounds, giant numbers, or decorative illustrations.
- Do **not** copy the Tamil Nadu state emblem, TNEA logo, exact government heading, or text implying official government affiliation. Do not describe the product as a Government of Tamil Nadu service unless formally authorized.
- No public signup, marketing home page, testimonials, pricing, social links, profile customization, general analytics or large settings area.
- Keep borders consistent and thin, corners modest (about 4–10px), and spacing predictable. Show a visible text label with every important status; never rely only on color.

### Login screen

- Minimal centered panel on a light background.
- Project wordmark and subtitle; short text “Authorized personnel only”.
- Username, password, one primary **Sign in** button, and a compact error/connection message.
- No role selector; server-side user role determines the destination. No public registration link.

### Ambulance workspace

- Show only incident intake, ranked hospitals, and the live road map/selected route.
- Use a compact header and a two-column desktop layout: left = short intake form; right = a clearly prioritized #1 hospital summary, detailed road map/route, and a compact list of alternatives. Collapse to one column on narrower displays without hiding the primary action.
- The single primary action is **Find best hospital**. After selection, primary action becomes the appropriate next coordination action, e.g. **Confirm destination**.
- Keep input labels short. Show numeric units beside heart rate, SpO₂ and optional PaO₂. Clearly label witness assessment and reported/unverified blood group.
- Keep route hazard warnings short and visible; do not claim a condition was detected by live data unless a configured source confirms it.

### Hospital workspace

- Show incoming cases assigned to the signed-in hospital first.
- Header identifies the authorized hospital account using its configured facility name; no generic mega-dashboard.
- Each case row should reveal priority, reported injury/category, incident location, reported observations, ETA, source/freshness, and the next action.
- Keep a compact readiness strip for ICU/ER/specialist/blood status. Update controls are limited to the account's assigned hospital.
- Keep pending blood requests and specialist pre-alerts as small task queues.
- A compact route/location map can appear for a selected incoming case, using the same real road-map provider as the ambulance workspace.

### Performance

- The app is an operational tool, not a public showcase. Avoid unnecessary animation, auto-rotating content, multi-step wizards, charts, hidden menus and full reloads.
- Load the road map only after authenticated workspace entry (or when a case is selected) so login remains fast. Keep map controls minimal.
- Keep current confirmed data visible if a live connection disconnects, but mark its age clearly.

## Acceptance criteria

- The result looks institutional, restrained, readable and modern—not like a consumer healthcare startup.
- TNEA's design language informs hierarchy and restraint, but Golden Hour Grid retains its own identity.
- No fake Tamil Nadu government branding/emblem.
- Only the two operational roles and their required tasks are visible.
- A dispatcher can enter a case, inspect the #1 choice, see its real road route, and confirm/override a destination with minimal actions.
