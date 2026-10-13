# Real Road Map and Routing Integration

## Required user experience

Golden Hour Grid must replace its schematic demo SVG/map with a **real, interactive road map** using actual geographic coordinates and road geometry. Default to a detailed standard roadmap—not satellite imagery, terrain, a decorative map, a hand-drawn grid, or fictitious streets.

- Use a high-detail street-level map view around the incident and selected hospital; start around zoom 15–16 where the provider's data permits, then fit the selected route bounds.
- Show actual streets, junctions, road names where supplied by the provider, incident marker, eligible hospital markers, selected hospital, recommended route polyline and (when available) an alternative route.
- No satellite toggle in the primary emergency interface. Hide map-type/imagery controls unless a future approved requirement says otherwise.
- Show an unobtrusive map attribution/license notice required by the provider.
- The ambulance workspace uses the map as part of decision-making. The hospital workspace may show a compact route/map for its assigned incoming case.
- Allow users to select an incident location by address/search or map click. Browser geolocation is optional and requires explicit permission; do not silently request it.
- Each real hospital must have verified coordinates and a trustworthy identity. Synthetic demo hospitals must be visibly identified as **DEMO FACILITY — NOT REAL** and must never be presented as actual care destinations. Do not place fictional hospitals in production mode.

## Recommended implementation

Use **Google Maps JavaScript API in `roadmap` mode plus the Google Routes API** when the operator configures valid credentials. This gives a straightforward path to a familiar, detailed road map and traffic-aware route/ETA requests.

- Client map uses `mapTypeId: "roadmap"`, a restrained control set, default focus on the incident/route, and no satellite UI.
- Backend calls Routes API for route calculation and a route matrix from the incident origin to candidate hospitals. Use `TRAFFIC_AWARE` as the normal speed/accuracy balance; make the tradeoff explicit in configuration. Avoid `TRAFFIC_AWARE_OPTIMAL` in the routine ranking path unless latency is acceptable and measured.
- The Google Routes API supports traffic-aware route calculations and a route matrix. Current Google documentation describes `TRAFFIC_AWARE` as considering live traffic with performance optimizations, and `TRAFFIC_AWARE_OPTIMAL` as higher latency and higher-cost. Check current documentation/pricing before deployment:
  - https://developers.google.com/maps/documentation/routes
  - https://developers.google.com/maps/documentation/routes/config_trade_offs
  - https://developers.google.com/maps/billing-and-pricing/pricing-india
- Keep two separate keys: `GOOGLE_MAPS_BROWSER_API_KEY` for Maps JavaScript API (restricted to the real allowed web origins and required APIs), and `GOOGLE_MAPS_ROUTES_API_KEY` for backend Routes API requests (server-side secret, never returned in frontend JSON). Enable API restrictions, billing alerts/quotas and key restrictions as appropriate. Never commit keys.
- Route Matrix compares origin-to-hospital ETAs; detailed route geometry is fetched for the chosen/previewed destination. Do not fetch route geometry for every hospital unless necessary.
- Make provider requests asynchronous with timeouts, request deduplication, bounded candidate count, safe retries, and an explicit error state. Never fabricate a route on provider failure.
- Provider output includes `provider`, `computed_at`, traffic mode/source, duration, static duration where returned, distance, route geometry, and warnings. Frontend must show ETA data provenance/freshness.

## No-key/local development behavior

The rest of the backend should still boot without map credentials, but the application must **not silently display a schematic or synthetic map as if it were real**. Display a concise configuration-required state on the map region and document exact setup steps. The developer may optionally configure a real OpenStreetMap-derived basemap through MapLibre using an appropriately licensed tile provider or self-hosted vector tiles; the chosen provider and attribution are mandatory.

For an open map stack, MapLibre GL JS supports vector tiles and style documents: https://maplibre.org/maplibre-gl-js/docs/. OpenStreetMap data is open, but the public OSM Foundation tile servers are capacity-limited and best-effort; their tile policy requires proper attribution and caching compliance and warns against using them as an unlimited production tile service: https://operations.osmfoundation.org/policies/tiles/. Choose a suitable provider or self-hosted tiles for sustained operation.

OSRM can calculate routes using an actual road network and return route geometry, alternatives (when available), and matrices: https://project-osrm.org/docs/. Do not rely on the public demo OSRM endpoint as a production SLA-backed service. Use a properly contracted hosted router or self-host it. Baseline OSM/OSRM routing does not, by itself, imply live traffic.

## Traffic and incident/hazard truthfulness

- Actual road geometry and an ETA are not the same as real-time road-condition awareness.
- Use live traffic only if the chosen configured provider returns it; identify that provider/mode in the response/UI.
- Railway-gate closures, road renewals, landslides, flooding, police roadblocks and diversions require a real feed, an authorized operator report, or an explicit demo/test fixture. A map provider's traffic-aware ETA must not be described as guaranteed awareness of each of these events.
- When an operator enters a hazard manually, record it as “operator reported” with observation time and optional expiry. Do not pretend it was auto-detected.
- Never apply random ETA multipliers and describe the result as real. Hazard-aware rerouting must affect route calculation only when the provider or a documented routing graph/constraint adapter supports that hazard; otherwise show a warning and state that the ETA may not reflect it.
- If no credible route exists or coordinates are invalid, show “Route unavailable” and ask for a corrected location; do not make up distance/time.
- Real routing data can help estimate travel, but this hackathon prototype is not a certified emergency navigation system. Dispatchers must retain authority to confirm the destination and route.

## Speed and operational acceptance criteria

- Lazy-load the map after login, not on the login screen.
- Do not block the intake form while the map initializes.
- Keep incident creation responsive; fetch ranking after the minimum location input passes validation.
- For ranking, use route-matrix response for candidate ETAs, then fetch detailed geometry only for the selected/expanded route.
- Show a subtle map/provider status: Connected, Setup required, or Temporarily unavailable; avoid noisy toast loops.
- Avoid polling the map/routing provider every second. Refresh only on a meaningful origin/resource/route change or configured operational refresh interval, respecting provider quotas/terms.
- Test with a known origin and destination, verify actual street geometry and route polyline, verify road-map-only mode, simulate missing/invalid keys, and verify route-provider errors do not produce fake ETAs.


## Operator setup for Google Maps

1. Create/select a Google Cloud project and configure billing before expecting Maps Platform APIs to return production results.
2. Enable the Maps JavaScript API and Routes API needed by the implementation.
3. Create a browser key restricted by HTTP referrer to the exact development/production origins and the Maps JavaScript API. This key is visible to the browser by design, so it must be restricted.
4. Create a separate server key restricted to the Routes API and keep it only in the server environment as `GOOGLE_MAPS_ROUTES_API_KEY`.
5. Copy `.env.example` to `.env`, add the values locally, keep `.env` out of Git, and set reasonable usage quotas/billing alerts. Never paste keys into Antigravity prompts or commit them.
6. Test both a known origin/destination and missing/invalid-key conditions. The map status should report the honest state.

Current Google Maps Platform pricing for India is SKU- and usage-dependent and may change; review the official [India pricing page](https://developers.google.com/maps/billing-and-pricing/pricing-india) before enabling paid usage. This handoff intentionally does not hardcode pricing assumptions.
