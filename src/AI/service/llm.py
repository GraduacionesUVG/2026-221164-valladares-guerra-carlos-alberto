"""Cliente mínimo para la API HTTP de Ollama.

Ollama sirve localmente tanto el modelo propio (vialbot) como los modelos
auxiliares usados en el entrenamiento y la evaluación. No se envía ningún dato
a servicios externos.
"""
import json
import re

import httpx

import config


class OllamaError(RuntimeError):
    pass


def chat(model: str, messages: list[dict], *, temperature: float = 0.2,
         json_mode: bool = False, max_tokens: int = 700, timeout: float = 180.0,
         num_ctx: int | None = None, base_url: str | None = None) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    if num_ctx:
        # Ventana de contexto; si no se indica, la del Modelfile del modelo
        payload["options"]["num_ctx"] = num_ctx
    if json_mode:
        payload["format"] = "json"
    url = f"{base_url or config.OLLAMA_URL}/api/chat"
    try:
        r = httpx.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise OllamaError(f"Ollama no respondió ({model}): {e}") from e
    content = r.json()["message"]["content"]
    # Algunos modelos (qwen3) pueden emitir su razonamiento entre etiquetas
    return re.sub(r"<think>.*?</think>", "", content, flags=re.S).strip()


def chat_json(model: str, messages: list[dict], **kwargs) -> dict:
    raw = chat(model, messages, json_mode=True, **kwargs)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, flags=re.S)
        if not m:
            raise
        return json.loads(m.group(0))


def unload(model: str, base_url: str | None = None):
    """Descarga el modelo de memoria; Ollama lo recarga en la siguiente petición."""
    try:
        httpx.post(f"{base_url or config.OLLAMA_URL}/api/generate",
                   json={"model": model, "keep_alive": 0}, timeout=30)
    except httpx.HTTPError:
        pass


def list_models(base_url: str | None = None) -> list[str]:
    r = httpx.get(f"{base_url or config.OLLAMA_URL}/api/tags", timeout=5.0)
    r.raise_for_status()
    return [m["name"] for m in r.json().get("models", [])]
