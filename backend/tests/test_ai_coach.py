import json

from app import create_app


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def make_client():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    return app.test_client()


def test_ai_coach_rejects_invalid_stage(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")

    response = make_client().post("/api/coach", json={"stage_id": 99})

    assert response.status_code == 400
    assert response.json["error"] == "Invalid call stage"


def test_ai_coach_requires_api_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")

    response = make_client().post("/api/coach", json={"stage_id": 5})

    assert response.status_code == 503
    assert "GEMINI_API_KEY" in response.json["error"]


def test_ai_coach_rejects_non_text_context(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")

    response = make_client().post(
        "/api/coach",
        json={"stage_id": 5, "prospect_words": ["not", "text"]},
    )

    assert response.status_code == 400
    assert "must be text" in response.json["error"]


def test_ai_coach_parses_successful_gemini_response(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    def fake_urlopen(req, timeout):
        assert "gemini-3.5-flash-lite:generateContent" in req.full_url
        assert "key=" not in req.full_url
        assert req.get_header("X-goog-api-key") == "test-only-key"
        assert timeout == 60
        sent = json.loads(req.data.decode("utf-8"))
        prompt = sent["contents"][0]["parts"][0]["text"]
        assert "Too expensive" in prompt
        assert "Current stage: Objection" in prompt
        assert sent["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "minimal"
        assert "temperature" not in sent["generationConfig"]
        return FakeResponse({
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "1. What to listen for\nUnderstand the budget concern."
                    }]
                }
            }]
        })

    monkeypatch.setattr("app.coach.urlopen", fake_urlopen)

    response = make_client().post(
        "/api/coach",
        json={
            "stage_id": 6,
            "prospect_words": "Too expensive",
            "notes": "Asked about budget",
        },
    )

    assert response.status_code == 200
    assert response.json["stage_name"] == "Objection"
    assert "budget concern" in response.json["coaching"]


def test_ai_coach_reports_connection_failure_without_exposing_key(monkeypatch):
    from urllib.error import URLError

    monkeypatch.setenv("GEMINI_API_KEY", "test-secret-that-must-not-be-logged")

    def fake_urlopen(req, timeout):
        raise URLError("network unreachable")

    monkeypatch.setattr("app.coach.urlopen", fake_urlopen)

    response = make_client().post("/api/coach", json={"stage_id": 1})

    assert response.status_code == 502
    assert "str" in response.json["error"]
    assert "test-secret-that-must-not-be-logged" not in response.get_data(as_text=True)
