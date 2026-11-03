import io, json, uuid
import cv2, numpy as np, pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.security import client_key, rate_limit


def synthetic_jpeg() -> bytes:
    img = np.full((400, 500, 3), (190, 160, 140), np.uint8)
    cv2.circle(img, (250, 200), 70, (60, 40, 35), -1)
    cv2.line(img, (100, 50), (400, 300), (20, 20, 20), 1)      # fake hair
    return cv2.imencode(".jpg", img)[1].tobytes()


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_and_quiz(client):
    assert client.get("/api/health").json()["status"] == "ok"
    q = client.get("/api/quiz").json()
    assert len(q) >= 10 and any("show_if" in x for x in q)


def test_rate_limit_ignores_untrusted_forwarded_for_header():
    request = Request({
        "type": "http", "method": "POST", "path": "/api/analyze", "query_string": b"",
        "headers": [(b"x-forwarded-for", b"203.0.113.200")],
        "client": ("198.51.100.45", 4321), "server": ("testserver", 80),
    })
    assert client_key(request) == "198.51.100.45"
    rate_limit(request, "unit-test", 1)
    with pytest.raises(HTTPException) as exc:
        rate_limit(request, "unit-test", 1)
    assert exc.value.status_code == 429


def test_analyze_and_report(client):
    answers = dict(age=62, sex="male", skin_tone="II", location="trunk", duration="m2_6", change="rapid",
                   symptoms=["bleeding"], non_healing="yes", history=["none"], family_melanoma="yes",
                   sunburn="many", prior_cancer="no", immuno="no")
    r = client.post("/api/analyze", files={"image": ("a.jpg", synthetic_jpeg(), "image/jpeg")}, data={"answers": json.dumps(answers)})
    assert r.status_code == 200, r.text
    body = r.json()
    assert abs(sum(p["adjusted_probability"] for p in body["predictions"]) - 1) < 0.01
    assert body["urgency"]["level"] in ("urgent", "soon", "routine") and body["context_factors"]
    pdf = client.get(f"/api/report/{body['id']}")
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"
    pdf_ar = client.get(f"/api/report/{body['id']}?language=ar")
    assert pdf_ar.status_code == 200 and pdf_ar.content[:4] == b"%PDF"


def test_rejects_bad_input(client):
    assert client.post("/api/analyze", files={"image": ("a.txt", b"hello", "text/plain")}).status_code == 415
    assert client.post("/api/analyze", files={"image": ("a.jpg", b"notanimage", "image/jpeg")}).status_code == 422
    assert client.get("/api/report/../../etc/passwd").status_code in (400, 404)


class StubPredictor:
    demo = False
    classes = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]

    def __init__(self, confidence=0.9, sharpness=100):
        self.confidence = confidence
        self.sharpness = sharpness

    def predict(self, _rgb):
        other_probability = (1.0 - self.confidence) / (len(self.classes) - 1)
        return {
            "probs": np.array([self.confidence] + [other_probability] * (len(self.classes) - 1)),
            "details": {
                "sharpness_score": self.sharpness,
                "mean_brightness": 100,
                "hair_coverage_pct": 0,
            },
        }


def test_uncertain_or_out_of_scope_image_returns_clear_error(client, monkeypatch):
    predictor = StubPredictor(confidence=1 / 7)
    monkeypatch.setattr("backend.app.main.get_predictor", lambda: predictor)

    response = client.post(
        "/api/analyze",
        files={"image": ("photo.jpg", synthetic_jpeg(), "image/jpeg")},
    )

    assert response.status_code == 422
    assert "outside the model's scope" in response.json()["detail"]


def test_severely_blurry_image_is_rejected(client, monkeypatch):
    predictor = StubPredictor(confidence=0.9, sharpness=2)
    monkeypatch.setattr("backend.app.main.get_predictor", lambda: predictor)

    response = client.post(
        "/api/analyze",
        files={"image": ("photo.jpg", synthetic_jpeg(), "image/jpeg")},
    )

    assert response.status_code == 422
    assert "too blurry" in response.json()["detail"]


def test_rejects_dimensions_over_configured_pixel_limit(client, monkeypatch):
    monkeypatch.setattr("backend.app.main.MAX_IMAGE_PIXELS", 10_000)

    response = client.post(
        "/api/analyze",
        files={"image": ("photo.jpg", synthetic_jpeg(), "image/jpeg")},
    )

    assert response.status_code == 413
    assert "dimensions are too large" in response.json()["detail"]


def test_answers_must_be_a_json_object(client):
    response = client.post(
        "/api/analyze",
        files={"image": ("photo.jpg", synthetic_jpeg(), "image/jpeg")},
        data={"answers": "[]"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Answers must be a JSON object."


def test_account_progress_assistant_and_acne_guide(client, monkeypatch, tmp_path):
    from backend.app import records
    monkeypatch.setattr(records, "DB_PATH", tmp_path / "accounts.sqlite3")
    records.initialize()
    email = f"skinai-{uuid.uuid4().hex}@example.test"
    created = client.post("/api/auth/register", json={"email": email, "password": "a-long-demo-password-123"})
    assert created.status_code == 200 and created.cookies
    assert client.get("/api/auth/me").status_code == 200
    assert client.get("/api/history").json() == []
    progress = client.post("/api/progress", json={"lesion_id": "left arm spot", "recorded_at": "2026-11-01", "note": "baseline"})
    assert progress.status_code == 200
    assert client.get("/api/progress").json()[0]["note"] == "baseline"
    assert client.post("/api/progress", json={"lesion_id": "spot", "analysis_id": {}}).status_code == 422
    answer = client.post("/api/assistant/chat", json={"message": "What is gentle acne care?", "language": "en"})
    assert answer.status_code == 200 and "not a diagnosis" in answer.json()["disclaimer"]
    unrelated = client.post("/api/assistant/chat", json={"message": "Tell me about eczema", "language": "en"})
    assert "benzoyl peroxide" not in unrelated.json()["answer"]
    pdf = client.get("/api/reports/acne-guide?language=en")
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"
    pdf_ar = client.get("/api/reports/acne-guide?language=ar")
    assert pdf_ar.status_code == 200 and pdf_ar.content[:4] == b"%PDF"
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/history").status_code == 401

    second_email = f"skinai-delete-{uuid.uuid4().hex}@example.test"
    assert client.post("/api/auth/register", json={"email": second_email, "password": "a-long-demo-password-456"}).status_code == 200
    deleted = client.delete("/api/auth/me")
    assert deleted.status_code == 200 and deleted.json() == {"ok": True}
    assert client.get("/api/auth/me").status_code == 401


def test_assistant_handles_greetings_and_matches_arabic_script(client, monkeypatch):
    greeting = client.post("/api/assistant/chat", json={"message": "Hello!", "language": "en"})
    assert greeting.status_code == 200
    assert greeting.json()["answer"].startswith("Hi!")
    assert "cannot diagnose" not in greeting.json()["answer"]

    arabic = client.post(
        "/api/assistant/chat",
        json={"message": "ما أفضل روتين بسيط للبشرة الجافة؟", "language": "en"},
    )
    assert arabic.status_code == 200
    assert "روتين" in arabic.json()["answer"]
    assert "تشخيصاً" in arabic.json()["disclaimer"]
    assert arabic.json()["sources"] and arabic.json()["mode"] == "retrieval"

    casual = client.post("/api/assistant/chat", json={"message": "كيف الحال؟", "language": "en"})
    assert casual.status_code == 200 and "شكراً لسؤالك" in casual.json()["answer"]
    name = client.post("/api/assistant/chat", json={"message": "What is your name?", "language": "en"})
    assert "SkinAI" in name.json()["answer"]
    rosacea = client.post("/api/assistant/chat", json={"message": "What can help with rosacea?", "language": "en"})
    assert rosacea.json()["sources"][0]["url"].startswith("https://www.aad.org/")
    assert "gentle" in rosacea.json()["answer"]
    guide = client.get("/api/assistant/guide/acne?language=ar")
    assert guide.status_code == 200 and "حب الشباب" in guide.json()["guidance"]
    assert guide.json()["source"]["url"].startswith("https://www.aad.org/")
    emergency = client.post("/api/assistant/chat", json={"message": "I have hives and trouble breathing", "language": "en"})
    assert "emergency" in emergency.json()["answer"].lower()

    captured = {}
    def generated(question, language, history, refs):
        captured.update(question=question, language=language, history=list(history), refs=list(refs))
        return "Grounded generated reply."
    monkeypatch.setattr("backend.app.assistant._external_generation", generated)
    response = client.post(
        "/api/assistant/chat",
        json={
            "message": "How can I care for acne?",
            "language": "en",
            "allow_generation": True,
            "history": [{"role": "user", "content": "I have a skincare question."}],
        },
    )
    assert response.status_code == 200
    assert response.json()["mode"] == "generated"
    assert response.json()["answer"] == "Grounded generated reply."
    assert captured["history"][0]["content"] == "I have a skincare question."
