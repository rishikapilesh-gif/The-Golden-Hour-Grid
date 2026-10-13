from backend.app.providers.routing.demo_router import DemoRoutingProvider


def test_demo_router_baseline():
    router = DemoRoutingProvider()
    origin = (300.0, 150.0)
    dest = (430.0, 90.0)

    res = router.estimate_route(origin, dest, [])
    assert res.provider == "demo_router"
    assert res.is_live is False
    assert res.primary.eta_minutes > 0
    assert res.primary.distance_km > 0
    assert len(res.primary.tags) == 0


def test_demo_router_hazards():
    router = DemoRoutingProvider()
    origin = (300.0, 150.0)
    dest = (430.0, 90.0)

    res_normal = router.estimate_route(origin, dest, [])
    res_rain = router.estimate_route(origin, dest, ["rain", "storm"])

    # Rain and storm should increase estimated travel time
    assert res_rain.primary.eta_minutes > res_normal.primary.eta_minutes
    assert "rain" in res_rain.primary.tags
    assert "severe weather" in res_rain.primary.tags


def test_demo_router_railgate_wait():
    router = DemoRoutingProvider()
    # Route that crosses railway line at x = 275 (e.g. from x=200 to x=350)
    origin = (200.0, 100.0)
    dest = (350.0, 100.0)

    res_no_gate = router.estimate_route(origin, dest, [])
    res_gate = router.estimate_route(origin, dest, ["railgate"])

    # Must add railgate wait when path crosses x=275
    assert res_gate.primary.eta_minutes >= res_no_gate.primary.eta_minutes + 6.0
    assert "railway gate wait" in res_gate.primary.tags
