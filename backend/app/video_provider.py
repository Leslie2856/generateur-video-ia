"""Adapter for a public Hugging Face Gradio video Space.

No access token is accepted or sent: the adapter must never spend paid credits.
"""
from pathlib import Path
from typing import Any

from gradio_client import Client, handle_file


class VideoProviderError(RuntimeError):
    """A safe, user-facing provider failure."""


class VideoProvider:
    def __init__(self, space_id: str):
        self.space_id = space_id

    def _client(self) -> Client:
        try:
            return Client(self.space_id, verbose=False)
        except Exception as exc:
            raise VideoProviderError(
                "Impossible de joindre le Space gratuit configuré. Vérifiez son identifiant, "
                "son état public et sa disponibilité. Aucun fournisseur payant n'a été appelé."
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
        try:
            image_input: Any = handle_file(image_path) if image_path else None
            result = client.predict(
                input_image=image_input,
                prompt=prompt,
                duration=float(duration_seconds),
                enhance_prompt=False,
                negative_prompt="shaky, glitchy, low quality, distorted, blurry",
                seed=42,
                randomize_seed=True,
                num_inference_steps=8,
                cfg_guidance_scale=3.0,
                height=height,
                width=width,
                api_name="/generate_video",
            )
        except Exception as exc:
            message = str(exc).lower()
            if any(term in message for term in ("quota", "exceeded", "rate limit", "too many")):
                raise VideoProviderError(
                    "Le quota gratuit ou la limite de requêtes est atteint. Attendez son renouvellement "
                    "puis réessayez ; aucune bascule payante n'est prévue."
                ) from exc
            raise VideoProviderError(
                "La génération a échoué ou le Space est indisponible. Vérifiez son API et réessayez plus tard. "
                "Aucune vidéo fictive n'a été créée et aucun fournisseur payant n'a été appelé."
            ) from exc

        # This Space returns (video filepath, seed). Do not accept empty or non-video output.
        video_path = result[0] if isinstance(result, (tuple, list)) and result else result
        if not isinstance(video_path, str) or not Path(video_path).is_file():
            raise VideoProviderError(
                "Le Space n'a pas renvoyé de fichier vidéo accessible. Vérifiez son API publique."
            )
        return video_path
