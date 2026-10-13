def test_incident_creation_and_role_isolation(client, seed_test_data):
    # 1. Hospital user cannot create incident
    client.post("/api/auth/login", json={
        "username": "hospital.demo",
        "password": "HospSecret123!"
    })
    res_hosp_create = client.post("/api/incidents", json={
        "location": {"label": "Central Junction"},
        "injury_category": "trauma",
        "incident_source": "Road traffic collision",
        "reported_blood_group": "O-"
    })
    assert res_hosp_create.status_code == 403

    # Logout hospital
    client.post("/api/auth/logout")

    # 2. Ambulance user creates incident
    client.post("/api/auth/login", json={
        "username": "ambulance.demo",
        "password": "AmbSecret123!"
    })

    # Invalid blood group validation
    res_invalid_bg = client.post("/api/incidents", json={
        "location": {"label": "Central Junction"},
        "injury_category": "trauma",
        "incident_source": "Road traffic collision",
        "reported_blood_group": "INVALID_GROUP"
    })
    assert res_invalid_bg.status_code == 422

    # Valid incident
    valid_payload = {
        "location": {"label": "Central Junction"},
        "injury_category": "trauma",
        "incident_source": "Road traffic collision",
        "gender": "Unknown",
        "reported_priority": "Critical",
        "witness_assessment": "Critical",
        "vitals": {
            "heart_rate_bpm": 118,
            "spo2_percent": 92.0,
            "pao2_mmhg": 85.0
        },
        "reported_blood_group": "O-",
        "blood_group_verified": False,
        "route_hazards": ["rain"]
    }
    res_create = client.post("/api/incidents", json=valid_payload)
    assert res_create.status_code == 201
    inc_data = res_create.json()
    incident_id = inc_data["id"]
    assert inc_data["status"] == "created"
    assert inc_data["reported_blood_group"] == "O-"

    # 3. Recommendations
    res_recs = client.get(f"/api/incidents/{incident_id}/recommendations")
    assert res_recs.status_code == 200
    recs_data = res_recs.json()
    assert recs_data["incident_id"] == incident_id
    assert len(recs_data["recommendations"]) >= 2
    assert recs_data["recommendations"][0]["rank"] == 1
    assert recs_data["recommendations"][0]["score"] >= recs_data["recommendations"][1]["score"]

    # 4. Destination selection with override reason
    res_select = client.post(f"/api/incidents/{incident_id}/select-hospital", json={
        "hospital_id": "demo-hospital-1",
        "override_reason": "Dispatcher selection based on trauma OT readiness."
    })
    assert res_select.status_code == 200
    selected_data = res_select.json()
    assert selected_data["selected_hospital_id"] == "demo-hospital-1"
    assert selected_data["status"] == "hospital_selected"
    assert selected_data["override_reason"] == "Dispatcher selection based on trauma OT readiness."

    # 5. Staged blood request & deduplication
    res_blood_1 = client.post(f"/api/incidents/{incident_id}/blood-requests", json={
        "hospital_id": "demo-hospital-1",
        "reported_group": "O-",
        "requested_units": 3,
        "reason": "Demo blood shortage request"
    })
    assert res_blood_1.status_code == 200
    blood_data_1 = res_blood_1.json()
    assert blood_data_1["status"] == "pending_approval"
    req_id_1 = blood_data_1["id"]

    # Repeat request must deduplicate and return same request ID
    res_blood_2 = client.post(f"/api/incidents/{incident_id}/blood-requests", json={
        "hospital_id": "demo-hospital-1",
        "reported_group": "O-",
        "requested_units": 3
    })
    assert res_blood_2.status_code == 200
    assert res_blood_2.json()["id"] == req_id_1
