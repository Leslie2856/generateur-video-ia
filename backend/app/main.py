from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Générateur vidéo IA API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AspectRatio = Literal["9:16", "16:9", "1:1"]


class GenerationRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=4000)
    duration_seconds: int = Field(default=10, ge=1, le=180)
    aspect_ratio: AspectRatio = "16:9"


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "generateur-video-ia", "video_provider_configured": False}


@app.post("/api/jobs")
def create_text_job(request: GenerationRequest):
    raise HTTPException(
        status_code=501,
        detail="La génération vidéo n'est pas encore configurée. Connectez un modèle ou fournisseur vidéo compatible.",
    )


@app.post("/api/jobs/image-to-video")
async def create_image_job(
    prompt: str = Form(..., min_length=3, max_length=4000),
    duration_seconds: int = Form(default=10, ge=1, le=180),
    aspect_ratio: AspectRatio = Form(default="16:9"),
    image: UploadFile = File(...),
):
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Formats acceptés : JPEG, PNG ou WebP.")
    raise HTTPException(
        status_code=501,
        detail="La génération vidéo à partir d'une image n'est pas encore configurée. Aucun fichier vidéo n'a été créé.",
    )
