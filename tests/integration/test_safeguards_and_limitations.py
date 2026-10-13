def test_blood_shortage_does_not_hard_exclude(client, seed_test_data):
    """A blood shortage should lower the score and add a warning, but NOT hard-exclude an otherwise viable hospital."""
    client.post("/api/auth/login", json={
        "username": "ambulance.demo",
        "password": "AmbSecret123!"
    })

    # Create incident needing AB- blood
    res_create = client.post("/api/incidents", json={
        "location": {"label": "Tech Park"},
        "injury_category": "trauma",
        "incident_source": "Road traffic collision",
        "reported_blood_group": "AB-",
        "reported_priority": "Critical"
    })
    inc_id = res_create.json()["id"]

    res_rank = client.get(f"/api/incidents/{inc_id}/recommendations")
    recs = res_rank.json()["recommendations"]

    # Even if hospital has low stock, it should still be marked eligible if accepting patients
    eligible_recs = [r for r in recs if r["eligible"]]
    assert len(eligible_recs) >= 2

    # Check for blood shortage warning
    low_blood_rec = next((r for r in eligible_recs if any("blood" in w.lower() for w in r["warnings"])), None)
    assert low_blood_rec is not None


def test_no_survival_probability_in_ranking_output(client, seed_test_data):
    """Assert that the ranking payload never contains survival probabilities or clinical diagnostic claims."""
    client.post("/api/auth/login", json={
        "username": "ambulance.demo",
        "password": "AmbSecret123!"
    })

    res_create = client.post("/api/incidents", json={
        "location": {"label": "Tech Park"},
        "injury_category": "cardiac",
        "incident_source": "Cardiac emergency",
        "reported_blood_group": "A+",
        "reported_priority": "Critical"
    })
    inc_id = res_create.json()["id"]

    res_rank = client.get(f"/api/incidents/{inc_id}/recommendations")
    rank_str = res_rank.text.lower()

    # Forbidden terminology in software coordination prototype
    assert "survival" not in rank_str
    assert "mortality" not in rank_str
    assert "cure" not in rank_str
    assert "diagnosis" not in rank_str


def test_assistant_disabled_by_default(client, seed_test_data):
    """Local assistant must be disabled by default and not in the critical path."""
    client.post("/api/auth/login", json={
        "username": "ambulance.demo",
        "password": "AmbSecret123!"
    })

    res = client.get("/api/assistant/health")
    assert res.status_code == 200
    data = res.json()
    assert data["enabled"] is False
    assert data["status"] == "disabled"
    assert "deterministic" in data["notes"].lower()


def test_hospital_user_cannot_tamper_hospital_id(client, seed_test_data):
    """Hospital user 2 cannot update resources of hospital 1."""
    client.post("/api/auth/login", json={
        "username": "hospital2.demo",
        "password": "Hosp2Secret123!"
    })

    # The PATCH /api/hospital/me/resources strictly uses user.hospital_id from DB
    res = client.patch("/api/hospital/me/resources", json={
        "icu_available": 6
    })
    assert res.status_code == 200
    # Must only update hospital 2 (demo-hospital-2)
    assert res.json()["id"] == "demo-hospital-2"

    # Verify hospital 1's ICU was NOT modified
    hosp_1 = seed_test_data["hospital_1"]
    assert hosp_1.icu_available != 6
