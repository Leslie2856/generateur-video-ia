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

from .video_provider import (
    DEFAULT_ANIMATE_SPACE,
    DEFAULT_IMAGE_SPACE,
    VideoProvider,
    AnimateProvider,
    VideoProviderError,
)

app = FastAPI(title="Générateur vidéo IA API", version="0.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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
MAX_MOTION_VIDEO_BYTES = 25 * 1024 * 1024
MAX_PROVIDER_DURATION_SECONDS = 5


class GenerationRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=MAX_PROMPT_LENGTH)
    duration_seconds: int = Field(default=5, ge=1, le=180)
    aspect_ratio: AspectRatio = "16:9"


def get_provider() -> VideoProvider:
    return VideoProvider(space_id=DEFAULT_IMAGE_SPACE)


def get_animate_provider() -> AnimateProvider:
    return AnimateProvider(space_id=DEFAULT_ANIMATE_SPACE)


def dimensions_for_ratio(ratio: AspectRatio) -> tuple[int, int]:
    return {"16:9": (768, 432), "9:16": (432, 768), "1:1": (512, 512)}[ratio]


def validate_provider_duration(duration_seconds: int) -> None:
    if duration_seconds > MAX_PROVIDER_DURATION_SECONDS:
        raise HTTPException(
            status_code=422,
            detail=(
                "Le Space gratuit actuel accepte au maximum 5 secondes par clip. "
                "Les vidéos de 1 à 3 minutes nécessitent un pipeline multi-scènes "
                "et un quota gratuit suffisant ; aucun clip fictif ne sera créé."
            ),
        )


def validate_mp4(result_path: str) -> Path:
    source = Path(result_path)
    if not source.is_file() or source.stat().st_size < 12:
        raise HTTPException(status_code=502, detail="Le moteur n'a pas renvoyé de fichier vidéo valide.")
    with source.open("rb") as video_file:
        header = video_file.read(12)
    if b"ftyp" not in header:
        raise HTTPException(status_code=502, detail="Le résultat reçu n'est pas un MP4 valide. Aucun fichier n'a été présenté comme vidéo.")
    return source


def persist_generated_video(result_path: str, duration: int | None = None, ratio: AspectRatio | None = None):
    source = validate_mp4(result_path)
    output_name = f"{uuid.uuid4().hex}.mp4"
    shutil.copyfile(source, OUTPUT_DIR / output_name)
    response = {"status": "succeeded", "video_url": f"/generated/{output_name}"}
    if duration is not None:
        response["duration_seconds"] = duration
    if ratio is not None:
        response["aspect_ratio"] = ratio
    return response


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": "generateur-video-ia",
        "video_provider_configured": True,
        "provider_space_id": DEFAULT_IMAGE_SPACE,
        "animate_provider_space_id": DEFAULT_ANIMATE_SPACE,
        "max_clip_seconds": MAX_PROVIDER_DURATION_SECONDS,
        "paid_fallback": False,
    }


@app.get("/api/provider/health")
async def provider_health(mode: Literal["image", "animate"] = "image"):
    provider = get_animate_provider() if mode == "animate" else get_provider()
    try:
        available = await run_in_threadpool(provider.check_available)
    except VideoProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "configured": True,
        "available": available,
        "mode": mode,
        "space_id": provider.space_id,
        "max_clip_seconds": MAX_PROVIDER_DURATION_SECONDS if mode == "image" else None,
        "paid_fallback": False,
    }


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
    return persist_generated_video(result_path, duration, ratio)


@app.post("/api/jobs")
async def create_text_job(request: GenerationRequest):
    raise HTTPException(
        status_code=422,
        detail="Le modèle texte-seul n'est pas configuré. Choisissez Image vers vidéo ou Animation de personnage.",
    )


@app.post("/api/jobs/image-to-video")
async def create_image_job(
    prompt: str = Form(..., min_length=3, max_length=MAX_PROMPT_LENGTH),
    duration_seconds: int = Form(default=3, ge=1, le=180),
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

    suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[image.content_type]
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp.write(data)
            temp_path = temp.name
        return await save_generated_video(get_provider(), prompt, duration_seconds, aspect_ratio, image_path=temp_path)
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
        await image.close()


@app.post("/api/jobs/animate")
async def create_animate_job(
    prompt: str = Form(..., min_length=3, max_length=MAX_PROMPT_LENGTH),
    image: UploadFile = File(...),
    motion_video: UploadFile = File(...),
):
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="L'image doit être au format JPEG, PNG ou WebP.")
    if motion_video.content_type not in {"video/mp4", "video/webm", "video/quicktime"}:
        raise HTTPException(status_code=415, detail="La vidéo de mouvement doit être MP4, WebM ou MOV.")

    image_data = await image.read(MAX_IMAGE_BYTES + 1)
    video_data = await motion_video.read(MAX_MOTION_VIDEO_BYTES + 1)
    if not image_data:
        raise HTTPException(status_code=400, detail="L'image du personnage est vide.")
    if not video_data:
        raise HTTPException(status_code=400, detail="La vidéo de mouvement est vide.")
    if len(image_data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="L'image doit faire 10 Mo maximum.")
    if len(video_data) > MAX_MOTION_VIDEO_BYTES:
        raise HTTPException(status_code=413, detail="La vidéo de mouvement doit faire 25 Mo maximum.")

    image_suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[image.content_type]
    video_suffix = {"video/mp4": ".mp4", "video/webm": ".webm", "video/quicktime": ".mov"}[motion_video.content_type]
    image_temp = video_temp = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=image_suffix) as temp:
            temp.write(image_data)
            image_temp = temp.name
        with tempfile.NamedTemporaryFile(delete=False, suffix=video_suffix) as temp:
            temp.write(video_data)
            video_temp = temp.name
        provider = get_animate_provider()
        try:
            result_path = await run_in_threadpool(
                provider.generate,
                prompt=prompt,
                image_path=image_temp,
                motion_video_path=video_temp,
            )
        except VideoProviderError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return persist_generated_video(result_path)
    finally:
        if image_temp:
            Path(image_temp).unlink(missing_ok=True)
        if video_temp:
            Path(video_temp).unlink(missing_ok=True)
        await image.close()
        await motion_video.close()
