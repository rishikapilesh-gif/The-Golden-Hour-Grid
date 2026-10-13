def test_hospital_command_scoping_and_workflow(client, seed_test_data):
    # 1. Ambulance user denied access to hospital command endpoints
    client.post("/api/auth/login", json={
        "username": "ambulance.demo",
        "password": "AmbSecret123!"
    })
    assert client.get("/api/hospital/me/resources").status_code == 403
    assert client.get("/api/hospital/incoming-cases").status_code == 403

    # Ambulance creates incident and routes to demo-hospital-1
    res_create = client.post("/api/incidents", json={
        "location": {"label": "Central Junction"},
        "injury_category": "trauma",
        "incident_source": "Road traffic collision",
        "reported_blood_group": "O-"
    })
    inc_id = res_create.json()["id"]
    client.post(f"/api/incidents/{inc_id}/select-hospital", json={
        "hospital_id": "demo-hospital-1"
    })
    client.post("/api/auth/logout")

    # 2. Hospital 1 user logs in
    client.post("/api/auth/login", json={
        "username": "hospital.demo",
        "password": "HospSecret123!"
    })

    # Read own resources
    res_h1 = client.get("/api/hospital/me/resources")
    assert res_h1.status_code == 200
    assert res_h1.json()["id"] == "demo-hospital-1"

    # Update own resources
    res_patch = client.patch("/api/hospital/me/resources", json={
        "icu_available": 4,
        "er_load": 0.35,
        "specialists": {"trauma": "surgery"},
        "blood": {"O-": 6}
    })
    assert res_patch.status_code == 200
    assert res_patch.json()["icu_available"] == 4
    assert res_patch.json()["er_load"] == 0.35

    # See incoming case routed to demo-hospital-1
    res_cases_h1 = client.get("/api/hospital/incoming-cases")
    assert res_cases_h1.status_code == 200
    case_ids_h1 = [c["incident_id"] for c in res_cases_h1.json()]
    assert inc_id in case_ids_h1

    # Acknowledge case
    res_ack = client.post(f"/api/hospital/incidents/{inc_id}/acknowledge", json={
        "notes": "Trauma team is prepping OR 2."
    })
    assert res_ack.status_code == 200
    assert res_ack.json()["status"] == "acknowledged"

    # Dispatch doctor to Trauma Bay 1
    res_doc = client.post(f"/api/hospital/incidents/{inc_id}/dispatch-doctor", json={
        "specialist_doctor": "Dr. Mehta",
        "bay_number": "Trauma Bay 1",
        "prep_notes": "Rapid infuser and intubation tray ready."
    })
    assert res_doc.status_code == 200
    assert res_doc.json()["status"] == "doctor_dispatched"
    assert res_doc.json()["specialist_doctor"] == "Dr. Mehta"

    # Complete handover at the bay
    res_handover = client.post(f"/api/hospital/incidents/{inc_id}/complete-handover", json={
        "handover_notes": "Patient handed over to Dr. Mehta in Bay 1."
    })
    assert res_handover.status_code == 200
    assert res_handover.json()["status"] == "handover_complete"

    client.post("/api/auth/logout")

    # 3. Hospital 2 user logs in and verifies data isolation
    client.post("/api/auth/login", json={
        "username": "hospital2.demo",
        "password": "Hosp2Secret123!"
    })

    # Hospital 2 must NOT see case routed to Hospital 1!
    res_cases_h2 = client.get("/api/hospital/incoming-cases")
    assert res_cases_h2.status_code == 200
    case_ids_h2 = [c["incident_id"] for c in res_cases_h2.json()]
    assert inc_id not in case_ids_h2

    # Hospital 2 cannot acknowledge or decline case belonging to Hospital 1
    res_cross_ack = client.post(f"/api/hospital/incidents/{inc_id}/acknowledge")
    assert res_cross_ack.status_code == 404
