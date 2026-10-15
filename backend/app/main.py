import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .video_provider import DEFAULT_SPACE_ID, VideoProvider, VideoProviderError

app = FastAPI(title="Générateur vidéo IA API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    # Vite may choose 5174/5175 when the default port is already occupied.
    allow_origin_regex=r"https?://(localhost|127\\.0\\.0\\.1)(:\\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = Path(os.getenv("VIDEO_OUTPUT_DIR", Path(__file__).resolve().parent.parent / "generated"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/generated", StaticFiles(directory=str(OUTPUT_DIR)), name="generated")

AspectRatio = Literal["9:16", "16:9", "1:1"]
MAX_PROMPT_LENGTH = 4000
MAX_IMAGE_BYTES = 10 * 1024 * 1024
# The selected public Wan 2.2 Space supports short clips only.
MAX_PROVIDER_DURATION_SECONDS = 5


class GenerationRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=MAX_PROMPT_LENGTH)
    duration_seconds: int = Field(default=5, ge=1, le=180)
    aspect_ratio: AspectRatio = "16:9"


def get_provider() -> VideoProvider:
    # Deliberately no token support: this integration must not consume paid credits.
    # Fixed to the public ZeroGPU Space. No token or configurable paid provider is supported.
    return VideoProvider(space_id=DEFAULT_SPACE_ID)


def dimensions_for_ratio(ratio: AspectRatio) -> tuple[int, int]:
    return {"16:9": (768, 432), "9:16": (432, 768), "1:1": (512, 512)}[ratio]


def validate_provider_duration(duration_seconds: int) -> None:
    if duration_seconds > MAX_PROVIDER_DURATION_SECONDS:
        raise HTTPException(
            status_code=422,
            detail=(
                "Le moteur gratuit actuel accepte au maximum 5 secondes par clip. "
                "Les vidéos de 1 à 3 minutes nécessitent un pipeline multi-scènes "
                "et un quota gratuit suffisant ; aucun clip fictif ne sera créé."
            ),
        )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": "generateur-video-ia",
        "video_provider_configured": True,
        "provider_space_id": DEFAULT_SPACE_ID,
        "max_clip_seconds": MAX_PROVIDER_DURATION_SECONDS,
        "paid_fallback": False,
    }


@app.get("/api/provider/health")
async def provider_health():
    provider = get_provider()
    try:
        available = await run_in_threadpool(provider.check_available)
    except VideoProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"configured": True, "available": available, "space_id": provider.space_id, "max_clip_seconds": MAX_PROVIDER_DURATION_SECONDS, "paid_fallback": False}


async def save_generated_video(provider: VideoProvider, prompt: str, duration: int, ratio: AspectRatio, image_path: str | None = None):
    validate_provider_duration(duration)
    width, height = dimensions_for_ratio(ratio)
    try:
        result_path = await run_in_threadpool(
            provider.generate,
            prompt=prompt,
            duration_seconds=duration,
            width=width,
            height=height,
            image_path=image_path,
        )
    except VideoProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    source = Path(result_path)
    if not source.is_file() or source.stat().st_size < 12:
        raise HTTPException(status_code=502, detail="Le moteur n'a pas renvoyé de fichier vidéo valide.")
    with source.open("rb") as video_file:
        header = video_file.read(12)
    if b"ftyp" not in header:
        raise HTTPException(status_code=502, detail="Le résultat reçu n'est pas un MP4 valide. Aucun fichier n'a été présenté comme vidéo.")
    output_name = f"{uuid.uuid4().hex}.mp4"
    destination = OUTPUT_DIR / output_name
    shutil.copyfile(source, destination)
    return {"status": "succeeded", "video_url": f"/generated/{output_name}", "duration_seconds": duration, "aspect_ratio": ratio}


@app.post("/api/jobs")
async def create_text_job(request: GenerationRequest):
    provider = get_provider()
    return await save_generated_video(provider, request.prompt, request.duration_seconds, request.aspect_ratio)


@app.post("/api/jobs/image-to-video")
async def create_image_job(
    prompt: str = Form(..., min_length=3, max_length=MAX_PROMPT_LENGTH),
    duration_seconds: int = Form(default=5, ge=1, le=180),
    aspect_ratio: AspectRatio = Form(default="16:9"),
    image: UploadFile = File(...),
):
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Formats acceptés : JPEG, PNG ou WebP.")
    validate_provider_duration(duration_seconds)
    data = await image.read(MAX_IMAGE_BYTES + 1)
    if not data:
        raise HTTPException(status_code=400, detail="Le fichier image est vide.")
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="L'image doit faire 10 Mo maximum.")

    suffix = { "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp" }[image.content_type]
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp.write(data)
            temp_path = temp.name
        provider = get_provider()
        return await save_generated_video(provider, prompt, duration_seconds, aspect_ratio, image_path=temp_path)
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
        await image.close()
