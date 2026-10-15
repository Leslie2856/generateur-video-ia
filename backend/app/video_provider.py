"""Free-only adapters for public Hugging Face ZeroGPU Spaces.

No Hugging Face token is accepted or sent. Public Space quotas and availability
remain controlled by Hugging Face; this module never falls back to a paid API.
"""
from pathlib import Path
from gradio_client import Client, handle_file

DEFAULT_IMAGE_SPACE = "Saravutw/WAN2.2_I2V_LIGHTNING_4-8step_custom"
DEFAULT_ANIMATE_SPACE = "hugging-apps/wan2-2-animate-2-14b"
DEFAULT_SPACE_ID = DEFAULT_IMAGE_SPACE


class VideoProviderError(RuntimeError):
    """A safe, user-facing provider failure."""


def _client(space_id: str) -> Client:
    try:
        return Client(space_id, verbose=False)
    except Exception as exc:
        raise VideoProviderError(
            f"Impossible de joindre le Space Hugging Face gratuit « {space_id} ». "
            "Vérifiez sa disponibilité et réessayez plus tard. Aucun fournisseur payant n'a été appelé."
        ) from exc


def _result_video_path(result) -> str:
    candidates = result if isinstance(result, (tuple, list)) else [result]
    for candidate in candidates:
        if isinstance(candidate, str) and Path(candidate).is_file():
            return candidate
        if isinstance(candidate, dict):
            path = candidate.get("path")
            if isinstance(path, str) and Path(path).is_file():
                return path
            video = candidate.get("video")
            if isinstance(video, dict) and isinstance(video.get("path"), str):
                if Path(video["path"]).is_file():
                    return video["path"]
    raise VideoProviderError(
        "Le Space n'a pas renvoyé de fichier vidéo accessible. Aucune vidéo fictive n'a été créée."
    )


def _provider_error(exc: Exception, space_id: str) -> VideoProviderError:
    message = str(exc).lower()
    if any(term in message for term in ("quota", "exceeded", "rate limit", "too many", "gpu", "queue full")):
        return VideoProviderError(
            "Le quota gratuit ou la capacité GPU est atteint. Attendez le renouvellement "
            "ou la fin de la file puis réessayez ; aucune bascule payante n'est prévue."
        )
    return VideoProviderError(
        f"La génération a échoué ou le Space gratuit « {space_id} » est indisponible. "
        "Vérifiez son état et réessayez. Aucune vidéo fictive n'a été créée et aucun fournisseur payant n'a été appelé."
    )


class VideoProvider:
    """Wan2.2 image-to-video provider, using a public ZeroGPU Space."""

    def __init__(self, space_id: str = DEFAULT_IMAGE_SPACE):
        self.space_id = space_id

    def check_available(self) -> bool:
        client = _client(self.space_id)
        try:
            api = client.view_api(print_info=False, return_format="dict")
            endpoints = api.get("named_endpoints", {}) if isinstance(api, dict) else {}
            if "/generate_video" not in endpoints:
                raise VideoProviderError("Le Space I2V ne publie plus l'endpoint /generate_video.")
        except VideoProviderError:
            raise
        except Exception as exc:
            raise VideoProviderError("Impossible de vérifier l'API du Space I2V gratuit.") from exc
        return True

    def generate(self, *, prompt: str, duration_seconds: int, width: int, height: int, image_path: str | None = None) -> str:
        if not image_path:
            raise VideoProviderError("Le mode Wan2.2 Image vers vidéo exige une image de départ.")
        client = _client(self.space_id)
        try:
            # Parameters follow the live Space UI's /generate_video endpoint.
            result = client.predict(
                handle_file(image_path),
                None,
                prompt,
                4,
                "blurry, low quality, chaotic, deformed, watermark, bad anatomy, shaky camera",
                float(min(max(duration_seconds, 1), 5)),
                1.0,
                1.0,
                42,
                True,
                5,
                "UniPCMultistep",
                3.0,
                16,
                False,
                True,
                api_name="/generate_video",
            )
        except Exception as exc:
            raise _provider_error(exc, self.space_id) from exc
        return _result_video_path(result)


class AnimateProvider:
    """Wan-Animate-2 provider: reference character image + driving video + prompt."""

    def __init__(self, space_id: str = DEFAULT_ANIMATE_SPACE):
        self.space_id = space_id

    def check_available(self) -> bool:
        client = _client(self.space_id)
        try:
            api = client.view_api(print_info=False, return_format="dict")
            endpoints = api.get("named_endpoints", {}) if isinstance(api, dict) else {}
            if "/animate" not in endpoints:
                raise VideoProviderError("Le Space Animate-2 ne publie plus l'endpoint /animate.")
        except VideoProviderError:
            raise
        except Exception as exc:
            raise VideoProviderError("Impossible de vérifier l'API du Space Animate-2 gratuit.") from exc
        return True

    def generate(self, *, prompt: str, image_path: str, motion_video_path: str) -> str:
        client = _client(self.space_id)
        try:
            # Inspect the live schema so a Space UI update does not silently scramble file order.
            api = client.view_api(print_info=False, return_format="dict")
            endpoint = api.get("named_endpoints", {}).get("/animate") if isinstance(api, dict) else None
            parameters = endpoint.get("parameters", []) if isinstance(endpoint, dict) else []
            kwargs = {}
            image_assigned = video_assigned = prompt_assigned = False
            for parameter in parameters:
                name = parameter.get("parameter_name") or parameter.get("label") or ""
                label = str(parameter.get("label") or name).lower()
                component = str(parameter.get("component") or "").lower()
                normalized = str(name).lower()
                combined = f"{normalized} {label}"
                if not image_assigned and ("image" in component or any(word in combined for word in ("image", "character", "reference"))):
                    kwargs[name] = handle_file(image_path)
                    image_assigned = True
                elif not video_assigned and ("video" in component or any(word in combined for word in ("video", "motion", "driving"))):
                    kwargs[name] = handle_file(motion_video_path)
                    video_assigned = True
                elif not prompt_assigned and ("textbox" in component or any(word in combined for word in ("prompt", "description", "instruction"))):
                    kwargs[name] = prompt
                    prompt_assigned = True
                elif not parameter.get("parameter_has_default", False):
                    raise VideoProviderError(
                        f"Le schéma actuel du Space Animate-2 contient un champ obligatoire non pris en charge : {name}."
                    )
            if not image_assigned or not video_assigned:
                raise VideoProviderError(
                    "Le schéma de l'API Animate-2 ne permet pas d'identifier les champs image et vidéo. "
                    "Vérifiez l'API publique du Space."
                )
            result = client.predict(api_name="/animate", **kwargs)
        except VideoProviderError:
            raise
        except Exception as exc:
            raise _provider_error(exc, self.space_id) from exc
        return _result_video_path(result)
