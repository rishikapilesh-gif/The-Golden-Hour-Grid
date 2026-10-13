def test_e2e_coordination_workflow(client, seed_test_data):
    # 1. Health check
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"

    # 2. Ambulance login
    res_amb_login = client.post("/api/auth/login", json={
        "username": "ambulance.demo",
        "password": "AmbSecret123!"
    })
    assert res_amb_login.status_code == 200
    assert res_amb_login.json()["redirect_to"] == "/ambulance"

    # 3. Create incident
    res_create = client.post("/api/incidents", json={
        "location": {"label": "Railway Colony"},
        "injury_category": "trauma",
        "incident_source": "Railway crossing incident",
        "gender": "Unknown",
        "reported_priority": "Critical",
        "witness_assessment": "Critical",
        "vitals": {
            "heart_rate_bpm": 125,
            "spo2_percent": 91.0,
            "pao2_mmhg": 80.0
        },
        "reported_blood_group": "O-",
        "route_hazards": ["railgate", "rain"]
    })
    assert res_create.status_code == 201
    inc_id = res_create.json()["id"]

    # 4. Get recommendations
    res_rank = client.get(f"/api/incidents/{inc_id}/recommendations")
    assert res_rank.status_code == 200
    recs = res_rank.json()["recommendations"]
    top_hospital = recs[0]["hospital_id"]

    # 5. Select top destination
    res_sel = client.post(f"/api/incidents/{inc_id}/select-hospital", json={
        "hospital_id": top_hospital,
        "override_reason": "Top ranked destination with optimal trauma OT capability."
    })
    assert res_sel.status_code == 200

    # 6. Stage blood request
    res_blood = client.post(f"/api/incidents/{inc_id}/blood-requests", json={
        "hospital_id": top_hospital,
        "reported_group": "O-",
        "requested_units": 2
    })
    assert res_blood.status_code == 200

    # 7. Update status to en_route
    res_status = client.patch(f"/api/incidents/{inc_id}/status", json={
        "status": "en_route"
    })
    assert res_status.status_code == 200
    assert res_status.json()["status"] == "en_route"

    # Ambulance logs out
    client.post("/api/auth/logout")

    # 8. Hospital logs in (assuming top_hospital is demo-hospital-1)
    if top_hospital == "demo-hospital-1":
        res_hosp_login = client.post("/api/auth/login", json={
            "username": "hospital.demo",
            "password": "HospSecret123!"
        })
        assert res_hosp_login.status_code == 200
        assert res_hosp_login.json()["redirect_to"] == "/hospital"

        # 9. See incoming case
        res_incoming = client.get("/api/hospital/incoming-cases")
        assert res_incoming.status_code == 200
        inc_ids = [c["incident_id"] for c in res_incoming.json()]
        assert inc_id in inc_ids

        # 10. Acknowledge case
        res_ack = client.post(f"/api/hospital/incidents/{inc_id}/acknowledge", json={
            "notes": "Trauma team assembled at the bay."
        })
        assert res_ack.status_code == 200

        # 11. Update resources
        res_upd = client.patch("/api/hospital/me/resources", json={
            "icu_available": 3,
            "er_load": 0.50
        })
        assert res_upd.status_code == 200

        client.post("/api/auth/logout")
