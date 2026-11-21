"""API interna del motor de IA de VialBot (FastAPI).

Solo el backend PHP la consume. Si se define AI_SERVICE_TOKEN, toda petición
debe incluir la cabecera X-Internal-Token con ese valor.

Uso local:  uvicorn service.app:app --port 8000
"""
import json
import logging
import os
import sys
from collections import Counter
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from service import llm  # noqa: E402
from service import runtime_config as rc  # noqa: E402
from service.prompts import SYSTEM_PROMPT  # noqa: E402
from service.rag import RagEngine  # noqa: E402

logging.basicConfig(level=logging.INFO)
engine: RagEngine | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global engine
    engine = RagEngine()
    # Carga el reranker (si está activo) al arrancar y no en la primera consulta
    engine.retriever.search("calentamiento del servicio", k=1)
    yield


app = FastAPI(title="VialBot AI Service", version="1.0.0", lifespan=lifespan)


def check_token(x_internal_token: str | None = Header(default=None)):
    expected = os.getenv("AI_SERVICE_TOKEN")
    if expected and x_internal_token != expected:
        raise HTTPException(status_code=401, detail="Token interno inválido")


class Turn(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    history: list[Turn] = []
    top_k: int | None = Field(default=None, ge=1, le=10)


class RetrieveRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    top_k: int | None = Field(default=None, ge=1, le=10)


class SettingsUpdate(BaseModel):
    """Todos los campos son opcionales: solo se actualizan los que se envían."""
    top_k: int | None = Field(default=None, ge=1, le=10)
    min_retrieval_score: float | None = Field(default=None, ge=0, le=1)
    in_domain_threshold: float | None = Field(default=None, ge=0, le=1)
    temperature: float | None = Field(default=None, ge=0, le=1)
    prefer_finetuned_generator: bool | None = None
    system_prompt: str | None = Field(default=None, max_length=4000)
    retrieval_mode: Literal["dense", "hybrid"] | None = None
    reranker: Literal["bge-m3", "mmarco-minilm"] | None = None
    rerank_candidates: int | None = Field(default=None, ge=5, le=50)
    num_ctx: int | None = Field(default=None, ge=2048, le=32768)
    reset: bool = False


@app.get("/health")
def health():
    try:
        models = llm.list_models()
        ollama = "healthy"
    except Exception:  # noqa: BLE001
        models, ollama = [], "offline"
    generator = engine.generator_model()
    return {
        "status": "healthy" if ollama == "healthy" else "degraded",
        "embedder": {
            "model": Path(engine.retriever.model_name).name,
            "finetuned": engine.retriever.finetuned,
        },
        "vectordb": {
            "status": "healthy",
            "collection": engine.retriever.collection.name,
            "vectors": engine.retriever.collection.count(),
        },
        "classifier": {"status": "healthy" if engine.classifier.ready else "missing"},
        "llm": {
            "status": ollama,
            "model": generator,
            "own_model": generator == config.GENERATOR_MODEL,
            "available": generator in models or f"{generator}:latest" in models,
        },
    }


@app.post("/query", dependencies=[Depends(check_token)])
def query(req: QueryRequest):
    try:
        return engine.answer(req.question, [t.model_dump() for t in req.history], req.top_k)
    except llm.OllamaError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@app.post("/retrieve", dependencies=[Depends(check_token)])
def retrieve(req: RetrieveRequest):
    embedding = engine.retriever.embed([req.question])[0]
    classification = engine.classifier.predict(embedding) if engine.classifier.ready else None
    hits = engine.retriever.search(req.question, k=req.top_k, query_embedding=embedding)
    return {"classification": classification, "sources": hits}


@app.get("/settings", dependencies=[Depends(check_token)])
def get_settings():
    """Parámetros ajustables en caliente desde el panel de administración."""
    return {
        "current": rc.get_all(),
        "defaults": rc.DEFAULTS,
        "default_system_prompt": SYSTEM_PROMPT,
    }


@app.put("/settings", dependencies=[Depends(check_token)])
def update_settings(req: SettingsUpdate):
    if req.reset:
        return {"current": rc.reset(), "default_system_prompt": SYSTEM_PROMPT}
    patch = req.model_dump(exclude={"reset"}, exclude_unset=True)
    return {"current": rc.update(patch), "default_system_prompt": SYSTEM_PROMPT}


@app.get("/corpus", dependencies=[Depends(check_token)])
def corpus():
    chunks_path = config.PROCESSED_DIR / "chunks.jsonl"
    with open(chunks_path, encoding="utf-8") as f:
        chunks = [json.loads(line) for line in f]
    chunk_count = Counter(c["doc_id"] for c in chunks)
    article_count = Counter(c["doc_id"] for c in chunks if c["part"] == 0)
    docs = []
    for meta in config.DOCUMENTS:
        pdf = config.RAW_DIR / meta["file"]
        docs.append({
            "id": meta["id"],
            "title": meta["title"],
            "filename": meta["file"],
            "source": meta["source"],
            "size_mb": round(pdf.stat().st_size / 1_048_576, 2) if pdf.exists() else None,
            "articles": article_count[meta["id"]],
            "chunks": chunk_count[meta["id"]],
            "status": "Indexado",
        })
    return {"documents": docs, "collection": engine.retriever.collection.name,
            "vectors": engine.retriever.collection.count()}


@app.get("/config", dependencies=[Depends(check_token)])
def get_config():
    """Arquitectura fija: cambiarla exige reingesta o reentrenar (ver AI/README.md).
    Los parámetros que sí se pueden ajustar en caliente están en /settings."""
    try:
        models = llm.list_models()
    except Exception:  # noqa: BLE001
        models = []
    return {
        "embedder": engine.retriever.model_name,
        "embedder_base": config.BASE_EMBEDDER,
        "embedder_finetuned": engine.retriever.finetuned,
        "generator_base": config.GENERATOR_BASE_HF,
        "generator_finetuned_available": any(m.split(":")[0] == config.GENERATOR_MODEL for m in models),
        "chunk_max_chars": config.CHUNK_MAX_CHARS,
        "chunk_overlap_chars": config.CHUNK_OVERLAP_CHARS,
        "chunking_strategy": "Por artículo, con subdivisión y traslape si excede el tamaño máximo",
        "classifier_ready": engine.classifier.ready,
        "distance": "cosine",
        "vectordb": "ChromaDB",
    }


@app.get("/metrics", dependencies=[Depends(check_token)])
def metrics():
    """Resultados más recientes de los scripts de evaluación (eval/results)."""
    out = {}
    for name in ("retrieval", "generation", "boundary", "classifier", "embedder_training"):
        path = config.RESULTS_DIR / f"{name}.json"
        if path.exists():
            out[name] = json.loads(path.read_text(encoding="utf-8"))
    return out


@app.get("/logs", dependencies=[Depends(check_token)])
def logs(source: str | None = None, limit: int = 50):
    return {"logs": engine.recent_events(source, min(limit, 200))}
