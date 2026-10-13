# API Contract (initial target)

All times are ISO 8601 UTC. All demo responses should include `is_demo: true` and a source/timestamp where applicable. FastAPI should generate the OpenAPI schema and Swagger UI from actual Pydantic models.

## Example: create incident

`POST /api/incidents`

```json
{
  "location": {"label": "Railway Colony", "latitude": null, "longitude": null},
  "injury_category": "trauma",
  "incident_source": "railway_crossing_incident",
  "gender": "unknown",
  "reported_priority": "critical",
  "witness_assessment": "unknown",
  "vitals": {
    "heart_rate_bpm": 118,
    "spo2_percent": 92,
    "pao2_mmhg": null,
    "observed_at": null
  },
  "reported_blood_group": "O-",
  "blood_group_verified": false,
  "route_hazards": ["railgate", "rain"]
}
```

`201 Created` should return the persistent incident ID, normalized values, `status`, `created_at`, `is_demo`, and validation/status notes. Do not persist patient name or identifier.

## Example: recommendations

`GET /api/incidents/{incident_id}/recommendations`

Return `incident_id`, `ranking_version`, `computed_at`, `is_demo`, `route_provider`, and an ordered `recommendations` array. Each item should include rank, hospital ID/name, total score, ETA/distance if justified, `eta_source`, `eta_is_live`, score components, reasons, warnings, resource timestamp/freshness and eligibility state.

## Example: stage blood request

`POST /api/incidents/{incident_id}/blood-requests`

```json
{
  "hospital_id": "demo-hospital-2",
  "reported_group": "O-",
  "requested_units": 2,
  "reason": "reported inventory below configured demo threshold"
}
```

The UI must show this as a demo draft/pending-approval request. Backend should not send it to an external system. Require idempotency or a uniqueness rule so repeated updates do not create duplicate active requests. The response must mention blood bank verification, compatibility/cross-match and authorization requirements.

## Example: manually choose a lower-ranked hospital

`POST /api/incidents/{incident_id}/select-hospital`

```json
{
  "hospital_id": "demo-hospital-4",
  "override_reason": "Dispatcher demo override: confirmed resource data from phone simulation"
}
```

A demo can simulate a role, but production must validate authenticated dispatcher permissions. Save the actor/reason and broadcast an incident selection event.

## Event types

- `hospital.resource_changed`
- `hospital.ranking_updated`
- `incident.status_changed`
- `incident.hospital_selected`
- `coordination.blood_request_updated`
- `coordination.specialist_request_updated`
- `assistant.note_ready`
- `system.connection_state`

Each event includes a unique ID, occurred-at time, source, demo/live marker, entity ID and schema-versioned payload.

## Errors

Use predictable JSON such as:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "spo2_percent must be between 0 and 100 when supplied",
    "details": {"field": "vitals.spo2_percent"}
  },
  "request_id": "uuid"
}
```

Never include stack traces, secrets, full environment data or sensitive patient text in public error responses.


## Real map and route endpoints

### `GET /api/map/status`

Returns only safe map configuration status (provider name, configured/not configured, provider availability, and short user-facing setup message). Do not return the server-side Routes API key or secrets. The browser-restricted Maps JavaScript key may be injected into page configuration only if it is restricted to the app's allowed origins and Maps JavaScript API; never expose `GOOGLE_MAPS_ROUTES_API_KEY`.

### `POST /api/routes/matrix`

Authenticated ambulance-only endpoint. Input includes a valid origin coordinate and a bounded list of eligible hospital IDs/coordinates. Return provider-derived travel duration/distance and provenance for each destination. Apply a hard maximum for candidate count and provider timeout. Do not return fabricated ETAs for failed elements.

### `GET /api/incidents/{incident_id}/route?hospital_id={id}`

Authenticated ambulance or assigned receiving-hospital user only. Return detailed provider route geometry for the chosen/previewed facility, distance, duration, optional traffic duration, provider, traffic mode, `computed_at`, `is_demo`, and warnings. This endpoint must not expose another hospital's private resource details.

Route metadata contract:

```json
{
  "status": "ok",
  "provider": "google_routes",
  "is_demo": false,
  "computed_at": "2026-10-13T00:00:00Z",
  "traffic_mode": "TRAFFIC_AWARE",
  "duration_seconds": 780,
  "static_duration_seconds": 660,
  "distance_meters": 8400,
  "geometry": { "format": "encoded_polyline", "value": "provider-returned-value" },
  "warnings": []
}
```

The values above are schema examples only, not live routing results. If a provider is unconfigured, use an explicit status such as `map_unconfigured` or `route_unavailable`; do not return zeroes or sample values as if the route succeeded. Respect the map/routing provider's terms and retention/caching restrictions.
