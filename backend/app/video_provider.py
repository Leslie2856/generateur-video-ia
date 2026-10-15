"""Free-only adapter for the public Wan 2.2 ZeroGPU Space.

Intentionally does not accept or send authentication tokens, so this application cannot
spend a user's prepaid credits or silently fall back to a paid inference API.
"""
from pathlib import Path
from typing import Any

from gradio_client import Client, handle_file

DEFAULT_SPACE_ID = "Wan-AI/Wan-2.2-5B"


class VideoProviderError(RuntimeError):
    """A safe, user-facing provider failure."""


class VideoProvider:
    def __init__(self, space_id: str = DEFAULT_SPACE_ID):
        self.space_id = space_id

    def _client(self) -> Client:
        try:
            return Client(self.space_id, verbose=False)
        except Exception as exc:
            raise VideoProviderError(
                "Impossible de joindre le Space Hugging Face gratuit configuré. "
                "Vérifiez sa disponibilité et réessayez plus tard. Aucun fournisseur payant n'a été appelé."
            ) from exc

    def check_available(self) -> bool:
        self._client()
        return True

    def generate(
        self,
        *,
        prompt: str,
        duration_seconds: int,
        width: int,
        height: int,
        image_path: str | None = None,
    ) -> str:
        client = self._client()
        image_input: Any = handle_file(image_path) if image_path else None
        if width > height:
            size = "1280*704"
        elif height > width:
            size = "704*1280"
        else:
            size = "960*960"

        try:
            result = client.predict(
                image=image_input,
                prompt=prompt,
                size=size,
                duration_seconds=float(duration_seconds),
                sampling_steps=35,
                guide_scale=5.0,
                shift=5.0,
                seed=-1,
                api_name="/generate_video",
            )
        except Exception as exc:
            message = str(exc).lower()
            if any(term in message for term in ("quota", "exceeded", "rate limit", "too many", "gpu")):
                raise VideoProviderError(
                    "Le quota gratuit ou la capacité GPU est atteint. Attendez le renouvellement "
                    "ou la fin de la file puis réessayez ; aucune bascule payante n'est prévue."
                ) from exc
            raise VideoProviderError(
                "La génération a échoué ou le Space est indisponible. Vérifiez son état et réessayez plus tard. "
                "Aucune vidéo fictive n'a été créée et aucun fournisseur payant n'a été appelé."
            ) from exc

        video_path = result[0] if isinstance(result, (tuple, list)) and result else result
        if not isinstance(video_path, str) or not Path(video_path).is_file():
            raise VideoProviderError(
                "Le Space n'a pas renvoyé de fichier vidéo accessible. Vérifiez son API publique."
            )
        return video_path
