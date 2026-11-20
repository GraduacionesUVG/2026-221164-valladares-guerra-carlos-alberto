"""Configuración en caliente del motor RAG.

A diferencia de config.py (fijo: rutas, modelos, tamaño de los fragmentos —
cambiarlo exige reingesta), estos valores el administrador puede ajustarlos
desde el panel sin reiniciar el servicio ni reindexar nada: se guardan en
data/runtime_config.json y se leen en cada consulta.
"""
import json
import threading
from contextlib import contextmanager

import config

_PATH = config.BASE_DIR / "data" / "runtime_config.json"
_LOCK = threading.Lock()

DEFAULTS = {
    "top_k": config.TOP_K,
    "min_retrieval_score": 0.25,
    "in_domain_threshold": config.IN_DOMAIN_THRESHOLD,
    "temperature": 0.1,
    # Si el modelo propio "vialbot" está registrado en Ollama, usarlo antes
    # que el modelo base sin ajustar.
    "prefer_finetuned_generator": True,
    # None = usar el Prompt Maestro por defecto (service/prompts.py)
    "system_prompt": None,
    # Recuperación (ver service/rag.py, Retriever): "dense" o "hybrid"
    "retrieval_mode": "dense",
    # None o una clave de rag.RERANKERS (bge-m3 elegido en desarrollo, Fase 3)
    "reranker": "bge-m3",
    "rerank_candidates": 20,
    # Ventana de contexto del generador en Ollama (tokens)
    "num_ctx": 8192,
}


def _load() -> dict:
    if _PATH.exists():
        try:
            saved = json.loads(_PATH.read_text(encoding="utf-8"))
            return {**DEFAULTS, **{k: v for k, v in saved.items() if k in DEFAULTS}}
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULTS)


_cache = _load()


def get_all() -> dict:
    with _LOCK:
        return dict(_cache)


def get(key: str):
    with _LOCK:
        return _cache.get(key, DEFAULTS.get(key))


def update(patch: dict) -> dict:
    with _LOCK:
        _cache.update({k: v for k, v in patch.items() if k in DEFAULTS})
        _PATH.parent.mkdir(parents=True, exist_ok=True)
        _PATH.write_text(json.dumps(_cache, indent=2, ensure_ascii=False), encoding="utf-8")
        return dict(_cache)


def reset() -> dict:
    return update(dict(DEFAULTS))


@contextmanager
def override(patch: dict):
    """Cambia valores solo en memoria mientras dura el bloque (experimentos);
    no toca data/runtime_config.json."""
    with _LOCK:
        saved = dict(_cache)
        _cache.update({k: v for k, v in patch.items() if k in DEFAULTS})
    try:
        yield
    finally:
        with _LOCK:
            _cache.clear()
            _cache.update(saved)
