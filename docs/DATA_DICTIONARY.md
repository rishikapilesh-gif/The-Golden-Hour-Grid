# Golden Hour Grid — Data Dictionary

All times are ISO-8601 UTC in persisted records. UI can localize display time. All synthetic fixtures must carry `is_demo=true`.

## Incident

- `id`: stable unique incident ID.
- `created_at`, `updated_at`: server timestamps.
- `created_by_user_id`: authenticated ambulance user.
- `status`: `new`, `ranked`, `destination_selected`, `prealert_sent`, `accepted`, `declined`, `en_route`, `arrived`, `closed`, or `cancelled` as implemented.
- `incident_location_text`: operator-provided address/landmark.
- `latitude`, `longitude`: optional valid coordinates from trusted geocoding, map selection, or permitted geolocation; do not fabricate.
- `injury_category`: `trauma`, `neuro`, `cardiac`, `orthopaedic`, `burns`, `other`, or `unknown`.
- `priority`: operator-assessed `critical`, `high`, `moderate`, `low`, or `unknown`; not a validated medical triage score.
- `witness_assessment`: `critical`, `moderate`, `stable_normal`, or `unknown`.
- `gender_context`: optional demographic context; must not influence ranking.
- `reported_blood_group`: ABO/Rh string among `O-`, `O+`, `A-`, `A+`, `B-`, `B+`, `AB-`, `AB+`; always marked reported/unverified until confirmed by qualified personnel.
- `heart_rate_bpm`: optional integer beats per minute.
- `spo2_percent`: optional saturation percent, distinct from PaO2.
- `pao2_mmhg`: optional partial pressure of oxygen in mmHg, distinct from SpO2.
- `incident_source`: road collision, multi-vehicle collision, fall/workplace, fire/burns, cardiac emergency, railway crossing, flood/natural hazard, hill-road/landslide, other, or unknown.
- `operator_reported_hazards`: list of conditions such as heavy rain, severe weather, roadworks, roadblock, diversion, railway gate, hill/ghat road, landslide risk, flooded road. Each item includes `reported_by`, `reported_at`, optional `expires_at`, and `verification_status`.

## Hospital and resource status

- `hospital.id`, `name`, `latitude`, `longitude`: stable facility identity and verified map coordinates; demo fixtures must say DEMO FACILITY — NOT REAL.
- `accepting_cases`: boolean or explicit `unknown` state.
- `icu_beds_available`: non-negative integer or unknown, with source and observation time.
- `er_load_percent`: 0–100 or unknown, with source and observation time.
- `specialist_type`, `availability_status`: availability `available`, `busy`, `unavailable`, or `unknown`; include `observed_at`, `source`, `is_demo`.
- `blood_group`, `units_available`: ABO/Rh and non-negative integer or unknown; include source/time and demo marker.
- `observed_at`: time the source observed the state.
- `received_at`: time the app received the state.
- `source`: provider/system/operator that supplied the value.
- `freshness_status`: `fresh`, `stale`, `unknown` or `unavailable`, derived from documented thresholds.

## Route result

- `provider`: exact configured provider identifier.
- `computed_at`: time the route was calculated.
- `distance_meters`: provider result; absent when unavailable.
- `duration_seconds`: ETA returned by provider.
- `static_duration_seconds`: optional non-live/historical estimate when provided.
- `traffic_mode`: e.g. `TRAFFIC_AWARE`, `TRAFFIC_UNAWARE`, or provider-specific value.
- `geometry`: actual provider route geometry; absent when routing fails.
- `warnings`: explicit limits, unknown hazards or provider errors.
- `is_demo`: true only for synthetic/deterministic demo routing.

## Ranking result

- `rank`: one-based order.
- `score`: deterministic, configurable demonstrator score; never described as survival probability or clinical outcome.
- `component_scores`: criterion scores used by the configured ranking function.
- `reasons`, `warnings`: concise, explainable reasons and data gaps.
- `computed_at`, `resource_snapshot_at`, `route_provider`, `is_demo`: reproducibility/provenance metadata.

## Coordination request

- `id`, `incident_id`, `hospital_id`, `request_type`: stable identifiers and request kind (`blood`, `specialist_prealert`).
- `status`: `draft`, `pending_approval`, `sent_to_configured_provider`, `acknowledged`, `declined`, `cancelled`, `failed`; never jump to “delivered”/“connected” without confirmed external-provider event.
- `created_by_user_id`, `created_at`, `updated_at`, `audit_events`: actor and status history.
- Blood request must state that it is a coordination request, not a transfusion order; clinical confirmation, compatibility/cross-match, and authorization are external requirements.
