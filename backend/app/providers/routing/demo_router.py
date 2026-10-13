import math
from typing import List, Tuple
from backend.app.providers.routing.base import RoutingProvider, RouteResult, PathAlternative

HOT_ZONES = [
    (160, 160, 40),
    (480, 120, 40),
    (300, 150, 60),
    (400, 260, 50),
    (540, 180, 45)
]


class DemoRoutingProvider(RoutingProvider):
    def __init__(self, traffic_mult: float = 1.0, green_wave: bool = True):
        self.traffic_mult = traffic_mult
        self.green_wave = green_wave

    def _frac_hot(self, p: List[Tuple[float, float]]) -> float:
        n = 0
        total_steps = 25
        for i in range(total_steps):
            t = i / (total_steps - 1)
            if t < 0.5:
                s_t = t * 2
                x = p[0][0] + (p[1][0] - p[0][0]) * s_t
                y = p[0][1] + (p[1][1] - p[0][1]) * s_t
            else:
                s_t = t * 2 - 1
                x = p[1][0] + (p[2][0] - p[1][0]) * s_t
                y = p[1][1] + (p[2][1] - p[1][1]) * s_t

            if any(math.hypot(x - cx, y - cy) < cr for cx, cy, cr in HOT_ZONES):
                n += 1
        return n / total_steps

    def estimate_route(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        hazards: List[str],
        origin_label: str = ""
    ) -> RouteResult:
        a = origin
        b = destination
        gw_factor = 0.8 if self.green_wave else 1.0
        manhattan_len = abs(a[0] - b[0]) + abs(a[1] - b[1])

        # Two schematic paths: via (b.x, a.y) and via (a.x, b.y)
        paths = [
            [a, (b[0], a[1]), b],
            [a, (a[0], b[1]), b]
        ]

        alternatives: List[PathAlternative] = []

        for idx, p in enumerate(paths):
            f = self._frac_hot(p)
            mult = 1.0
            wait = 0.0
            tags = []

            if "rain" in hazards:
                mult *= 1.18
                tags.append("rain")
            if "storm" in hazards:
                mult *= 1.32
                tags.append("severe weather")
            if "roadworks" in hazards:
                mult *= 1.28 if idx == 0 else 1.12
                tags.append("roadworks")
            if "roadblock" in hazards:
                mult *= 1.72 if idx == 0 else 1.16
                tags.append("roadblock detour" if idx > 0 else "roadblock on preferred path")
            if "diversion" in hazards:
                mult *= 1.18
                tags.append("diversion")
            if "flood" in hazards:
                mult *= 1.65 if idx == 0 else 1.28
                tags.append("flood risk")
            if "hills" in hazards or "hill" in origin_label.lower():
                mult *= 1.3
                tags.append("hill / ghat terrain")
            if "landslide" in hazards:
                mult *= 1.8 if idx == 0 else 1.25
                tags.append("landslide risk")

            # Railway line crossing check at x = 275
            crosses_rail = any(
                p[i - 1][0] != p[i][0] and
                min(p[i - 1][0], p[i][0]) <= 275 <= max(p[i - 1][0], p[i][0])
                for i in range(1, len(p))
            )

            if "railgate" in hazards and crosses_rail:
                wait += 7.0
                tags.append("railway gate wait")

            raw_eta = (manhattan_len * 0.075 * self.traffic_mult * gw_factor * (1.0 + 1.4 * f) * mult) + wait
            eta = round(raw_eta, 1)
            dist_km = round(manhattan_len * 0.06 * (1.12 if tags else 1.0), 1)

            is_blocked = ("roadblock" in hazards and idx == 0)

            alternatives.append(PathAlternative(
                path=p,
                eta_minutes=max(eta, 1.0),
                distance_km=max(dist_km, 0.5),
                tags=tags,
                is_blocked=is_blocked
            ))

        # Sort alternatives by eta
        alternatives.sort(key=lambda x: x.eta_minutes)

        return RouteResult(
            primary=alternatives[0],
            alternate=alternatives[1] if len(alternatives) > 1 else alternatives[0],
            provider="demo_router",
            is_live=False,
            notes=["Illustrative schematic routing; not a live GPS navigation system."]
        )
