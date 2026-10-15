from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main


class FakeProvider:
    space_id = "tests/fake-space"

    def check_available(self):
        return True

    def generate(self, *, prompt, duration_seconds, width, height, image_path=None):
        output = Path(main.OUTPUT_DIR) / "provider-test.mp4"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"not-a-real-video-test-fixture")
        return str(output)


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "OUTPUT_DIR", tmp_path)
    monkeypatch.setenv("HF_VIDEO_SPACE_ID", "tests/fake-space")
    monkeypatch.setattr(main, "get_provider", lambda: FakeProvider())
    return TestClient(main.app)


def test_health_never_enables_paid_fallback(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["paid_fallback"] is False
    assert response.json()["video_provider_configured"] is True


def test_provider_health_uses_provider_adapter(client):
    response = client.get("/api/provider/health")
    assert response.status_code == 200
    assert response.json()["available"] is True
    assert response.json()["paid_fallback"] is False


def test_text_generation_returns_real_file_url_from_provider(client):
    response = client.post(
        "/api/jobs",
        json={"prompt": "Un coucher de soleil sur le Sahel", "duration_seconds": 5, "aspect_ratio": "16:9"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "succeeded"
    assert body["video_url"].startswith("/generated/")
    assert (main.OUTPUT_DIR / body["video_url"].split("/")[-1]).is_file()


def test_duration_over_provider_limit_is_rejected_without_generation(client):
    response = client.post(
        "/api/jobs",
        json={"prompt": "Une scène au Sahel", "duration_seconds": 30, "aspect_ratio": "16:9"},
    )
    assert response.status_code == 422
    assert "10 secondes" in response.json()["detail"]


def test_missing_provider_is_reported_without_paid_fallback(monkeypatch):
    monkeypatch.delenv("HF_VIDEO_SPACE_ID", raising=False)
    client = TestClient(main.app)
    response = client.post(
        "/api/jobs",
        json={"prompt": "Un coucher de soleil", "duration_seconds": 5, "aspect_ratio": "16:9"},
    )
    assert response.status_code == 503
    assert "aucun fournisseur payant" in response.json()["detail"]


def test_rejects_invalid_image_mime_type(client):
    response = client.post(
        "/api/jobs/image-to-video",
        data={"prompt": "Anime cette scène", "duration_seconds": "5", "aspect_ratio": "16:9"},
        files={"image": ("malware.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 415
