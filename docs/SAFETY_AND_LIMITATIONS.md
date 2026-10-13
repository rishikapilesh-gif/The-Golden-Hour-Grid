# Safety, Security and Limitations

Golden Hour Grid is a hackathon/research prototype, not a certified emergency dispatch, navigation, clinical triage, treatment, or transfusion system.

## Operations and medical boundaries

- No patient diagnosis, treatment recommendation, survival prediction, or unvalidated medical threshold calculations.
- Display vitals as reported observations with units and provenance. Keep SpO₂ (%) separate from PaO₂ (mmHg).
- Witness assessments and dispatcher priority are contextual inputs, not a validated triage protocol.
- Gender must not affect hospital ranking.
- Never display synthetic hospitals, ICU counts, specialist availability, blood stock, routes, or ETAs as real. Demo facilities must be clearly marked `DEMO FACILITY — NOT REAL`.
- Ranking weights are illustrative and require appropriate domain/clinical review before operational use.
- Destination selection remains a human decision. A route provider ETA is an estimate, not a guarantee.
- A blood shortage can create a staged pending request, but not an automatic transfusion order. Compatibility, cross-match, blood-group verification and authorization require the proper clinical workflow.
- Specialist notifications and phone/video connections must be represented honestly; do not claim a real call without an integrated provider confirmation.

## Map and traffic truthfulness

- Use a configured real map provider and actual geographic coordinates. The map must be a detailed standard road map, not a schematic SVG or satellite image.
- Do not invent a route, distance, or ETA when a provider fails or required coordinates are absent.
- Live traffic, rail-gate states, road closures, flooding, landslides and construction hazards are only available when a configured provider/operator feed actually supplies them. An operator-entered hazard must be labelled operator-reported and timestamped.
- Follow the map provider's license, attribution, API restrictions, caching and retention requirements. Review up-to-date provider terms and pricing before deployment.

## Security

- Use individually managed accounts, hashed passwords, revocable server-side sessions, HttpOnly SameSite cookies, HTTPS in deployments, Origin/CSRF safeguards, throttling, and server-side role enforcement.
- Hospital accounts can only access cases/resources assigned to their facility. Do not trust role or hospital IDs sent from the browser.
- Keep browser-restricted map keys and server-side routing keys separate. Never commit keys, credentials, or `.env` files. Configure API restrictions and usage/billing alerts.
- Use synthetic data only in local/demo tests. Avoid placing patient details or secrets in general logs.
- Keep audit events for destination overrides, resource updates, case acceptance/decline, and coordination request transitions.

## Deployment boundary

A production deployment needs authorized institutional users, verified facility/resource feeds, tested routing provider availability, privacy/security review, operational monitoring, defined fallback procedures, and relevant clinical/dispatch governance. This repository does not supply real hospital, ambulance, blood-bank, communications, traffic, or road-closure integrations.
