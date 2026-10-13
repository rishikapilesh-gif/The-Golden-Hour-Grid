from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any
from backend.app.models.hospital import Hospital
from backend.app.models.incident import Incident
from backend.app.schemas.ranking import RecommendationOut, ScoreComponents, EtaInfo, RankingResponse
from backend.app.providers.routing.base import RoutingProvider

SEVERITY_BLOOD_NEED = {
    "Critical": 4,
    "High": 3,
    "Moderate": 1,
    "Low": 0
}

SPECIALIST_NAME_MAP = {
    "trauma": "Trauma surgeon",
    "neuro": "Neurosurgeon",
    "cardiac": "Cardiologist",
    "ortho": "Orthopaedic surgeon",
    "burns": "Burns specialist"
}

LOCATION_COORDINATES: Dict[str, Tuple[float, float]] = {
    "Central Junction": (300.0, 150.0),
    "Tech Park": (160.0, 160.0),
    "Old Bazaar": (380.0, 170.0),
    "Highway Toll": (480.0, 120.0),
    "University Gate": (130.0, 240.0),
    "Port Junction": (560.0, 240.0),
    "North Market": (220.0, 50.0),
    "Railway Colony": (90.0, 200.0),
    "Riverside Road": (540.0, 180.0),
    "East Flyover": (400.0, 260.0),
    "South Industrial": (250.0, 330.0),
    "Hill Station / Ghat Road": (565.0, 35.0)
}


class DeterministicRankingEngine:
    def __init__(self, router: RoutingProvider):
        self.router = router

    def get_origin_coords(self, incident: Incident) -> Tuple[float, float]:
        if incident.latitude is not None and incident.longitude is not None:
            return (incident.latitude, incident.longitude)
        return LOCATION_COORDINATES.get(incident.location_label, (300.0, 150.0))

    def compute_effective_severity(self, incident: Incident) -> int:
        sev_val = SEVERITY_BLOOD_NEED.get(incident.reported_priority, 1)
        witness_val = 0
        if incident.witness_assessment == "Critical":
            witness_val = 4
        elif incident.witness_assessment == "Moderate":
            witness_val = 1
        return max(sev_val, witness_val)

    def rank_hospitals(
        self,
        incident: Incident,
        hospitals: List[Hospital]
    ) -> RankingResponse:
        origin = self.get_origin_coords(incident)
        eff_sev = self.compute_effective_severity(incident)
        needed_units = max(eff_sev, 1)
        injury = incident.injury_category.lower()
        blood_group = incident.reported_blood_group
        hazards = list(incident.route_hazards or [])

        # Vitals warning check
        vital_warning = False
        spo2 = incident.spo2_percent
        hr = incident.heart_rate_bpm
        if (spo2 is not None and 0 < spo2 <= 90.0) or (hr is not None and 0 < hr and (hr >= 130 or hr < 50)):
            vital_warning = True

        recommendations: List[RecommendationOut] = []

        # Standard weights (normalized to 100)
        # Travel: 25, Specialist: 25, ICU: 20, ER load: 10, Blood support: 10, Freshness: 10
        w_travel = 25.0
        w_spec = 25.0
        w_icu = 20.0
        w_er = 10.0
        w_blood = 10.0
        w_fresh = 10.0

        # When severity is high/critical, increase weights for travel, specialist, and ICU
        if eff_sev >= 3:
            w_travel += 5.0
            w_spec += 5.0
            w_icu += 5.0
        if vital_warning:
            w_spec += 5.0
            w_icu += 5.0

        total_weight = w_travel + w_spec + w_icu + w_er + w_blood + w_fresh

        for h in hospitals:
            reasons: List[str] = []
            warnings: List[str] = []

            # 1. Hard feasibility check
            if h.accepting_status == "not_accepting":
                recommendations.append(RecommendationOut(
                    rank=999,
                    hospital_id=h.id,
                    hospital_name=h.name,
                    score=0,
                    eta=EtaInfo(minutes=999.0, source="demo_router", is_live=False),
                    distance_km=None,
                    components=ScoreComponents(travel=0, specialist=0, icu=0, er_load=0, blood_support=0, freshness=0),
                    reasons=[],
                    warnings=["Hospital is currently marked NOT ACCEPTING incoming emergency patients"],
                    data_freshness="stale" if h.source == "demo_feed" else "demo",
                    icu_available=h.icu_available,
                    er_load=h.er_load,
                    specialist_status="unavailable",
                    specialist_doctor=None,
                    blood_units=0,
                    eligible=False
                ))
                continue

            # 2. Route calculation
            dest_coords = (h.x, h.y)
            route = self.router.estimate_route(origin, dest_coords, hazards, origin_label=incident.location_label)
            eta_min = route.primary.eta_minutes
            dist_km = route.primary.distance_km

            # Travel score factor: 1 - min(eta/45, 1)
            travel_factor = max(0.0, 1.0 - (eta_min / 45.0))
            travel_comp = round((travel_factor * w_travel / total_weight) * 100)
            if eta_min <= 15:
                reasons.append(f"Short estimated travel time ({eta_min} min)")
            elif eta_min >= 30:
                warnings.append(f"Long travel ETA ({eta_min} min)")

            # 3. Specialist availability
            # Find matching specialist
            spec_obj = next((s for s in h.specialists if s.specialty.lower() == injury), None)
            spec_status = spec_obj.status.lower() if spec_obj else "unavailable"
            spec_dr = spec_obj.doctor_name if spec_obj else None

            spec_factor = 0.0
            spec_display = SPECIALIST_NAME_MAP.get(injury, "Specialist")
            if spec_status in ("free", "available"):
                spec_factor = 1.0
                reasons.append(f"{spec_display} is listed available")
            elif spec_status in ("surgery", "busy"):
                spec_factor = 0.4
                warnings.append(f"{spec_display} is in surgery (estimated free shortly)")
            elif spec_status == "unknown":
                spec_factor = 0.2
                warnings.append(f"{spec_display} availability is unknown/unverified")
            else:
                spec_factor = 0.0
                warnings.append(f"No {spec_display.lower()} listed on duty")

            spec_comp = round((spec_factor * w_spec / total_weight) * 100)

            # 4. ICU capacity
            # Capacity 0-6 beds
            icu_factor = min(h.icu_available / 6.0, 1.0)
            icu_comp = round((icu_factor * w_icu / total_weight) * 100)
            if h.icu_available >= 3:
                reasons.append(f"{h.icu_available} ICU beds available")
            elif h.icu_available == 0:
                warnings.append("0 ICU beds available")
            else:
                warnings.append(f"Only {h.icu_available} ICU bed(s) available")

            # 5. ER load (lower is better: 1 - er_load)
            er_factor = max(0.0, 1.0 - h.er_load)
            er_comp = round((er_factor * w_er / total_weight) * 100)
            if h.er_load <= 0.4:
                reasons.append(f"Low ER load ({round(h.er_load * 100)}%)")
            elif h.er_load >= 0.75:
                warnings.append(f"High ER load ({round(h.er_load * 100)}%)")

            # 6. Blood support readiness
            # Find reported stock for requested blood group
            blood_obj = next((b for b in h.blood_inventories if b.blood_group == blood_group), None)
            stock_units = blood_obj.units_available if blood_obj else 0

            blood_factor = min(stock_units / max(needed_units, 1), 1.0)
            blood_comp = round((blood_factor * w_blood / total_weight) * 100)
            if stock_units >= needed_units:
                reasons.append(f"Reported {stock_units} units of {blood_group} available")
            else:
                warnings.append(f"Reported blood stock ({stock_units} units of {blood_group}) is below demo threshold ({needed_units} units)")

            # 7. Data freshness
            # Check hospital.updated_at
            data_freshness = "fresh"
            fresh_factor = 1.0
            if h.updated_at:
                upd_time = h.updated_at if h.updated_at.tzinfo else h.updated_at.replace(tzinfo=timezone.utc)
                age_mins = (datetime.now(timezone.utc) - upd_time).total_seconds() / 60.0
                if age_mins > 60:
                    data_freshness = "stale"
                    fresh_factor = 0.5
                    warnings.append("Hospital resource data is older than 60 minutes")
            fresh_comp = round((fresh_factor * w_fresh / total_weight) * 100)

            # Route caveats
            if route.primary.tags:
                tag_str = ", ".join(route.primary.tags)
                warnings.append(f"Route hazard penalties applied: {tag_str}")

            if vital_warning:
                warnings.append("Reported vitals trigger demo clinician review requirement; not a clinical diagnosis.")

            total_score = min(100, max(0, travel_comp + spec_comp + icu_comp + er_comp + blood_comp + fresh_comp))

            components = ScoreComponents(
                travel=travel_comp,
                specialist=spec_comp,
                icu=icu_comp,
                er_load=er_comp,
                blood_support=blood_comp,
                freshness=fresh_comp
            )

            recommendations.append(RecommendationOut(
                rank=0,  # will be assigned after sort
                hospital_id=h.id,
                hospital_name=h.name,
                score=total_score,
                eta=EtaInfo(minutes=eta_min, source="demo_router", is_live=False),
                distance_km=dist_km,
                components=components,
                reasons=reasons,
                warnings=warnings,
                data_freshness=data_freshness,
                icu_available=h.icu_available,
                er_load=h.er_load,
                specialist_status=spec_status,
                specialist_doctor=spec_dr,
                blood_units=stock_units,
                eligible=True
            ))

        # Sort: eligible first, score desc, eta asc, name asc
        recommendations.sort(key=lambda r: (not r.eligible, -r.score, r.eta.minutes, r.hospital_name))

        # Assign ranks 1..N
        for idx, rec in enumerate(recommendations):
            rec.rank = idx + 1

        return RankingResponse(
            incident_id=incident.id,
            ranking_version="v1",
            computed_at=datetime.now(timezone.utc),
            is_demo=True,
            route_provider="demo_router",
            recommendations=recommendations
        )
