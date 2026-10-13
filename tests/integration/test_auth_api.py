from backend.app.core.config import settings


def test_anonymous_access_denied(client):
    res_me = client.get("/api/auth/me")
    assert res_me.status_code == 401

    res_inc = client.get("/api/incidents/test-id")
    assert res_inc.status_code == 401

    res_hosp = client.get("/api/hospital/me/resources")
    assert res_hosp.status_code == 401


def test_invalid_login(client, seed_test_data):
    res = client.post("/api/auth/login", json={
        "username": "ambulance.demo",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401
    assert "Invalid credentials" in res.json()["detail"]


def test_ambulance_login_me_logout(client, seed_test_data):
    # 1. Login
    res_login = client.post("/api/auth/login", json={
        "username": "ambulance.demo",
        "password": "AmbSecret123!"
    })
    assert res_login.status_code == 200
    data = res_login.json()
    assert data["user"]["username"] == "ambulance.demo"
    assert data["user"]["role"] == "ambulance"
    assert data["redirect_to"] == "/ambulance"

    # Check cookie
    assert settings.SESSION_COOKIE_NAME in client.cookies

    # 2. GET /api/auth/me
    res_me = client.get("/api/auth/me")
    assert res_me.status_code == 200
    me_data = res_me.json()
    assert me_data["user"]["role"] == "ambulance"
    assert me_data["redirect_to"] == "/ambulance"

    # 3. Logout
    res_logout = client.post("/api/auth/logout")
    assert res_logout.status_code == 200

    # 4. GET /api/auth/me after logout must be 401
    res_me_after = client.get("/api/auth/me")
    assert res_me_after.status_code == 401


def test_hospital_login(client, seed_test_data):
    res_login = client.post("/api/auth/login", json={
        "username": "hospital.demo",
        "password": "HospSecret123!"
    })
    assert res_login.status_code == 200
    data = res_login.json()
    assert data["user"]["username"] == "hospital.demo"
    assert data["user"]["role"] == "hospital"
    assert data["user"]["hospital_id"] == "demo-hospital-1"
    assert data["redirect_to"] == "/hospital"
