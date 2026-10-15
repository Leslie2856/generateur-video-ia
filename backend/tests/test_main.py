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
        output.write_bytes(b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00")
        return str(output)


class FakeAnimateProvider:
    space_id = "tests/fake-animate-space"

    def check_available(self):
        return True

    def generate(self, *, prompt, image_path, motion_video_path):
        output = Path(main.OUTPUT_DIR) / "animate-test.mp4"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00")
        return str(output)


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(main, "get_provider", lambda: FakeProvider())
    monkeypatch.setattr(main, "get_animate_provider", lambda: FakeAnimateProvider())
    return TestClient(main.app)


def test_health_never_enables_paid_fallback(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["paid_fallback"] is False
    assert body["video_provider_configured"] is True
    assert body["provider_space_id"] == "Saravutw/WAN2.2_I2V_LIGHTNING_4-8step_custom"
    assert body["animate_provider_space_id"] == "hugging-apps/wan2-2-animate-2-14b"


def test_provider_health_uses_provider_adapter(client):
    response = client.get("/api/provider/health?mode=image")
    assert response.status_code == 200
    assert response.json()["available"] is True
    assert response.json()["paid_fallback"] is False


def test_animate_provider_health_uses_animate_adapter(client):
    response = client.get("/api/provider/health?mode=animate")
    assert response.status_code == 200
    assert response.json()["available"] is True
    assert response.json()["mode"] == "animate"
    assert response.json()["paid_fallback"] is False


def test_image_generation_returns_real_file_url_from_mock_provider(client):
    response = client.post(
        "/api/jobs/image-to-video",
        data={"prompt": "Anime ce coucher de soleil", "duration_seconds": "3", "aspect_ratio": "16:9"},
        files={"image": ("source.png", b"fake image data", "image/png")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "succeeded"
    assert body["video_url"].startswith("/generated/")
    assert (main.OUTPUT_DIR / body["video_url"].split("/")[-1]).is_file()


def test_animation_returns_real_file_url_from_mock_provider(client):
    response = client.post(
        "/api/jobs/animate",
        data={"prompt": "Reproduis le mouvement du personnage"},
        files={
            "image": ("character.png", b"fake image data", "image/png"),
            "motion_video": ("motion.mp4", b"fake motion data", "video/mp4"),
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "succeeded"
    assert body["video_url"].startswith("/generated/")
    assert (main.OUTPUT_DIR / body["video_url"].split("/")[-1]).is_file()


def test_text_only_generation_explains_model_is_not_configured(client):
    response = client.post(
        "/api/jobs",
        json={"prompt": "Un coucher de soleil sur le Sahel", "duration_seconds": 3, "aspect_ratio": "16:9"},
    )
    assert response.status_code == 422
    assert "texte-seul n'est pas configuré" in response.json()["detail"]


def test_duration_over_provider_limit_is_rejected_without_generation(client):
    response = client.post(
        "/api/jobs/image-to-video",
        data={"prompt": "Anime ce coucher de soleil", "duration_seconds": "30", "aspect_ratio": "16:9"},
        files={"image": ("source.png", b"fake image data", "image/png")},
    )
    assert response.status_code == 422
    assert "5 secondes" in response.json()["detail"]


def test_default_provider_is_free_and_has_no_paid_fallback(monkeypatch):
    provider = main.get_provider()
    assert provider.space_id == "Saravutw/WAN2.2_I2V_LIGHTNING_4-8step_custom"
    assert main.health()["paid_fallback"] is False


def test_rejects_invalid_image_mime_type(client):
    response = client.post(
        "/api/jobs/image-to-video",
        data={"prompt": "Anime cette scène", "duration_seconds": "3", "aspect_ratio": "16:9"},
        files={"image": ("malware.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 415


def test_rejects_invalid_motion_video_mime_type(client):
    response = client.post(
        "/api/jobs/animate",
        data={"prompt": "Anime ce personnage"},
        files={
            "image": ("character.png", b"image", "image/png"),
            "motion_video": ("bad.txt", b"not a video", "text/plain"),
        },
    )
    assert response.status_code == 415


def test_provider_failure_returns_clear_503_without_paid_fallback(client, monkeypatch):
    class UnavailableProvider:
        space_id = "Saravutw/WAN2.2_I2V_LIGHTNING_4-8step_custom"

        def generate(self, **kwargs):
            raise main.VideoProviderError(
                "Le quota gratuit est atteint. Réessayez plus tard ; aucune bascule payante n'est prévue."
            )

    monkeypatch.setattr(main, "get_provider", lambda: UnavailableProvider())
    response = client.post(
        "/api/jobs/image-to-video",
        data={"prompt": "Anime cette scène", "duration_seconds": "3", "aspect_ratio": "16:9"},
        files={"image": ("source.png", b"image", "image/png")},
    )
    assert response.status_code == 503
    assert "quota gratuit" in response.json()["detail"]
    assert "bascule payante" in response.json()["detail"]
