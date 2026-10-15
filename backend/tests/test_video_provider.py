from pathlib import Path

from app import video_provider as vp


class FakeGradioClient:
    def __init__(self, output_path, parameters=None):
        self.output_path = output_path
        self.parameters = parameters or []
        self.kwargs = None
        self.args = None
        self.api_name = None

    def view_api(self, print_info=False, return_format="dict"):
        return {"named_endpoints": {
            "/generate_video": {"parameters": []},
            "/animate": {"parameters": self.parameters},
        }}

    def predict(self, *args, api_name=None, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.api_name = api_name
        return (str(self.output_path), str(self.output_path), 42)


def _mp4(tmp_path):
    path = tmp_path / "result.mp4"
    path.write_bytes(b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00")
    return path


def test_i2v_provider_calls_expected_gradio_endpoint(monkeypatch, tmp_path):
    output = _mp4(tmp_path)
    fake = FakeGradioClient(output)
    monkeypatch.setattr(vp, "_client", lambda _space: fake)
    image = tmp_path / "image.png"
    image.write_bytes(b"image")
    result = vp.VideoProvider().generate(
        prompt="Anime l'image doucement",
        duration_seconds=3,
        width=768,
        height=432,
        image_path=str(image),
    )
    assert result == str(output)
    assert fake.api_name == "/generate_video"
    assert len(fake.args) == 16
    assert fake.args[2] == "Anime l'image doucement"


def test_animate_provider_maps_live_schema_by_component_and_name(monkeypatch, tmp_path):
    output = _mp4(tmp_path)
    parameters = [
        {"parameter_name": "driving_video", "label": "Motion video", "component": "Video", "parameter_has_default": False},
        {"parameter_name": "reference_image", "label": "Character image", "component": "Image", "parameter_has_default": False},
        {"parameter_name": "prompt", "label": "Prompt", "component": "Textbox", "parameter_has_default": False},
    ]
    fake = FakeGradioClient(output, parameters)
    monkeypatch.setattr(vp, "_client", lambda _space: fake)
    image = tmp_path / "character.png"
    video = tmp_path / "motion.mp4"
    image.write_bytes(b"image")
    video.write_bytes(b"video")
    result = vp.AnimateProvider().generate(
        prompt="Anime le personnage",
        image_path=str(image),
        motion_video_path=str(video),
    )
    assert result == str(output)
    assert fake.api_name == "/animate"
    assert set(fake.kwargs) == {"driving_video", "reference_image", "prompt"}
    assert fake.kwargs["prompt"] == "Anime le personnage"


def test_animate_provider_health_checks_named_endpoint(monkeypatch, tmp_path):
    fake = FakeGradioClient(_mp4(tmp_path), [])
    monkeypatch.setattr(vp, "_client", lambda _space: fake)
    assert vp.AnimateProvider().check_available() is True
