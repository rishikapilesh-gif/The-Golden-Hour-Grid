from backend.app.core.config import settings


def test_routing_anonymous_access_denied(client):
    res_matrix = client.post("/api/routes/matrix", json={
        "origin_latitude": 13.0827,
        "origin_longitude": 80.2707,
        "destinations": []
    })
    assert res_matrix.status_code == 401

    res_route = client.get("/api/incidents/some-inc-id/route")
    assert res_route.status_code == 401


def test_map_status_and_secret_leak_protection(client, seed_test_data):
    # Log in as ambulance
    client.post("/api/auth/login", json={
        "username": "ambulance.demo",
        "password": "AmbSecret123!"
    })

    res = client.get("/api/map/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["map_provider"] in ("google", "osm")
    assert "center" in data
    assert "disclaimer" in data
    assert "Synthetic demo" in data["disclaimer"]

    # CRITICAL: Verify secret backend Routes key is NEVER returned in response
    res_str = res.text
    if settings.GOOGLE_MAPS_ROUTES_API_KEY:
        assert settings.GOOGLE_MAPS_ROUTES_API_KEY not in res_str


def test_route_matrix_endpoint(client, seed_test_data):
    client.post("/api/auth/login", json={
        "username": "ambulance.demo",
        "password": "AmbSecret123!"
    })

    res = client.post("/api/routes/matrix", json={
        "origin_latitude": 13.0827,
        "origin_longitude": 80.2707,
        "destinations": [
            {"hospital_id": "demo-hospital-1", "latitude": 13.0827, "longitude": 80.2707},
            {"hospital_id": "demo-hospital-2", "latitude": 13.0569, "longitude": 80.2425}
        ],
        "hazards": ["rain"]
    })
    assert res.status_code == 200
    data = res.json()
    assert len(data["results"]) == 2
    assert data["results"][0]["hospital_id"] == "demo-hospital-1"
    assert data["results"][0]["duration_minutes"] > 0
    assert data["results"][1]["duration_minutes"] > 0
    assert any("rain" in w.lower() for w in data["warnings"])


def test_detailed_incident_route_endpoint(client, seed_test_data):
    client.post("/api/auth/login", json={
        "username": "ambulance.demo",
        "password": "AmbSecret123!"
    })

    # Create incident
    res_create = client.post("/api/incidents", json={
        "location": {"label": "Tech Park", "latitude": 12.9863, "longitude": 80.2432},
        "injury_category": "trauma",
        "incident_source": "Road traffic collision",
        "reported_blood_group": "O-",
        "reported_priority": "High",
        "route_hazards": ["roadworks"]
    })
    inc_id = res_create.json()["id"]

    # Request route for demo-hospital-1
    res_route = client.get(f"/api/incidents/{inc_id}/route?hospital_id=demo-hospital-1")
    assert res_route.status_code == 200
    data = res_route.json()

    assert data["hospital_id"] == "demo-hospital-1"
    assert data["distance_km"] > 0
    assert data["duration_minutes"] > 0
    assert len(data["primary_geometry"]) >= 2
    assert len(data["turn_by_turn"]) >= 1
    assert "roadworks" in " ".join(data["warnings"]).lower()
    assert data["is_live"] in (True, False)
    assert len(data["notes"]) > 0


def test_frontend_static_routes(client):
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "GOLDEN HOUR GRID" in res_index.text

    res_css = client.get("/styles.css")
    assert res_css.status_code == 200
    assert "--color-navy" in res_css.text

    res_js = client.get("/app.js")
    assert res_js.status_code == 200
    assert "renderRealRoadMap" in res_js.text
