from app import create_app, db


def setup_client():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    return app, app.test_client()


def test_health_endpoint():
    _, client = setup_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json["status"] == "healthy"


def test_all_eight_stages_are_available():
    _, client = setup_client()
    response = client.get("/api/stages")
    assert response.status_code == 200
    assert len(response.json["stages"]) == 8
    assert response.json["stages"][4]["name"] == "Their need"


def test_individual_stage_and_invalid_stage():
    _, client = setup_client()
    assert client.get("/api/stages/5").json["stage"]["name"] == "Their need"
    assert client.get("/api/stages/9").status_code == 404


def test_call_outcomes_are_available():
    _, client = setup_client()
    response = client.get("/api/outcomes")
    assert response.status_code == 200
    assert "Not interested" in response.json["outcomes"]


def test_create_update_end_and_history():
    _, client = setup_client()

    created = client.post("/api/calls", json={
        "prospect_name": "Alex",
        "company_name": "Example Ltd"
    })
    assert created.status_code == 201
    call_id = created.json["call"]["id"]

    updated = client.patch(f"/api/calls/{call_id}", json={
        "current_stage": 5,
        "prospect_words": "Our team spends too much time on manual reports.",
        "notes": "Reports take several hours each week."
    })
    assert updated.status_code == 200
    assert updated.json["call"]["stage_name"] == "Their need"
    assert "manual reports" in updated.json["call"]["prospect_words"]

    ended = client.post(f"/api/calls/{call_id}/end", json={
        "outcome": "Follow-up required",
        "next_step": "Send information next week."
    })
    assert ended.status_code == 200
    assert ended.json["call"]["status"] == "completed"
    assert ended.json["call"]["current_stage"] == 5

    history = client.get("/api/calls")
    assert history.status_code == 200
    assert len(history.json["calls"]) == 1
    assert history.json["calls"][0]["outcome"] == "Follow-up required"


def test_missing_call_returns_404():
    _, client = setup_client()
    assert client.get("/api/calls/999").status_code == 404


def test_invalid_stage_update_is_rejected():
    _, client = setup_client()
    created = client.post("/api/calls", json={"prospect_name": "Taylor"})
    call_id = created.json["call"]["id"]

    response = client.patch(f"/api/calls/{call_id}", json={
        "current_stage": 9
    })
    assert response.status_code == 400


def test_call_can_end_at_an_early_stage():
    _, client = setup_client()
    created = client.post("/api/calls", json={"prospect_name": "Jordan"})
    call_id = created.json["call"]["id"]

    client.patch(f"/api/calls/{call_id}", json={"current_stage": 2})
    ended = client.post(f"/api/calls/{call_id}/end", json={
        "outcome": "Not interested"
    })

    assert ended.status_code == 200
    assert ended.json["call"]["current_stage"] == 2
    assert ended.json["call"]["status"] == "completed"
