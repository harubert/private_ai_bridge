"""
Wrapper für lokale LLMs via Ollama.
Kann mit jedem Modell verwendet werden, das Ollama unterstützt.
"""
import httpx
import os
import json

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("PRIVATE_AI_BRIDGE_MODEL", "gemma4:e4b")


class LocalLLMError(Exception):
    pass


async def generate(prompt: str, model: str = None, temperature: float = 0.3, max_tokens: int = 4096) -> str:
    """Schickt einen Prompt an das lokale LLM und gibt die Antwort zurück."""
    model = model or DEFAULT_MODEL

    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                        "num_ctx": 8192,
                    },
                },
            )
            response.raise_for_status()
            return response.json()["response"]
        except httpx.ConnectError:
            raise LocalLLMError(
                "Ollama läuft nicht. Starte mit: brew services start ollama"
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise LocalLLMError(
                    f"Modell '{model}' nicht installiert. "
                    f"Installiere mit: ollama pull {model}"
                )
            raise LocalLLMError(f"Ollama-Fehler: {e}")


async def list_available_models() -> list[str]:
    """Listet alle in Ollama installierten Modelle."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            response.raise_for_status()
            return [m["name"] for m in response.json().get("models", [])]
        except httpx.ConnectError:
            raise LocalLLMError("Ollama läuft nicht.")


async def is_available() -> bool:
    """Prüft ob Ollama erreichbar und das Default-Modell verfügbar ist."""
    try:
        models = await list_available_models()
        return any(DEFAULT_MODEL.split(":")[0] in m for m in models)
    except Exception:
        return False
