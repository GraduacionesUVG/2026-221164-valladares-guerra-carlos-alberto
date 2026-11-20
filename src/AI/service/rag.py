"""Fase IV: orquestación e inferencia del sistema RAG.

Flujo por consulta:
  1. Clasificación: el clasificador propio decide el tema de la consulta y si
     pertenece al dominio de tránsito (pruebas de límites).
  2. Vectorización en caliente de la consulta con el modelo de embeddings.
  3. Búsqueda por similitud coseno en ChromaDB (top-K fragmentos).
  4. Inyección de los fragmentos en el Prompt Maestro y generación con el LLM.
"""
import logging
import re
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from threading import Lock

import unicodedata

import chromadb
import joblib
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer

import config
from service import llm
from service import runtime_config as rc
from service.prompts import (REFUSAL_NO_CONTEXT, REFUSAL_OUT_OF_DOMAIN,
                             build_messages)

log = logging.getLogger("vialbot.rag")

# Filtro de seguridad previo al clasificador (pruebas de límites): el
# clasificador de dominio solo mide tema, no intención. Una consulta puede
# mencionar palabras de tránsito ("multa", "licencia", "retén") y aun así ser
# un intento de manipulación o de evadir la ley; el modelo generador de 1.5B
# no es lo bastante robusto para detectarlo por sí solo, así que se bloquea
# aquí con patrones explícitos antes de llegar al LLM.
ADVERSARIAL_PATTERNS = [
    r"\bignora\b.{0,30}\binstruccion",
    r"\bolvida\b.{0,30}\b(que eres|tus instrucciones|tu rol)",
    r"\bactua(r)?\s+como\b",
    r"\bmuestra\b.{0,20}\b(tu|el)\s+prompt\b",
    r"\bsystem prompt\b",
    r"\bescapar(me)?\b.{0,20}\b(ret[eé]n|control|polic[ií]a|pmt)",
    r"\bevadir\b.{0,20}\b(ret[eé]n|control|polic[ií]a)",
    r"\bfalsificar\b",
    r"\bmordida\b",
    r"\bsoborn",
    # Leyes o límites de otro país mezclados con vocabulario de tránsito
    # (en cualquier orden dentro de la misma oración)
    r"\b(m[eé]xico|espa[nñ]a|honduras|el salvador|colombia|estados unidos)\b.{0,60}"
    r"\b(ley|multa|l[ií]mite|velocidad|tr[aá]nsito)\b",
    r"\b(ley|multa|l[ií]mite|velocidad|tr[aá]nsito)\b.{0,60}"
    r"\b(m[eé]xico|espa[nñ]a|honduras|el salvador|colombia|estados unidos)\b",
]
ADVERSARIAL_RE = re.compile("|".join(ADVERSARIAL_PATTERNS), re.IGNORECASE)


STOPWORDS = set("""a al ante con de del desde el en entre es esta este hay la las le lo los me mi mis
no o para pero por que se si sin sobre su sus te tengo tu un una uno y ya como cual cuando donde
puedo debo tiene tienen ser estar esta hacer qué cómo cuál""".split())

# Rerankers evaluados (Fase 3): cross-encoders multilingües
RERANKERS = {
    "bge-m3": "BAAI/bge-reranker-v2-m3",
    "mmarco-minilm": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
}


def _tokens(text: str) -> list[str]:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return [t for t in re.findall(r"[a-z0-9]+", text) if t not in STOPWORDS and len(t) > 1]


class Retriever:
    """Recuperación de fragmentos. Modos (runtime_config):
      retrieval_mode  "dense"  similitud coseno en ChromaDB (embeddings propios)
                      "hybrid" dense + BM25 fusionados con Reciprocal Rank Fusion
      reranker        None o una clave de RERANKERS: reordena los primeros
                      `rerank_candidates` con un cross-encoder
    El campo "score" de cada fragmento es siempre la similitud coseno, para que
    el umbral min_retrieval_score conserve su significado en todos los modos."""

    RRF_K = 60

    def __init__(self, use_finetuned: bool | None = None):
        client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
        if use_finetuned is None:
            # El modelo propio solo se usa si ya tiene su colección indexada
            indexed = {c.name for c in client.list_collections()}
            use_finetuned = (config.FINETUNED_EMBEDDER_DIR.exists()
                             and config.COLLECTION_FINETUNED in indexed)
            if config.FINETUNED_EMBEDDER_DIR.exists() and not use_finetuned:
                log.warning("Embedder propio sin indexar; ejecuta pipeline.build_index --only vialbot")
        self.finetuned = use_finetuned
        self.model_name = (str(config.FINETUNED_EMBEDDER_DIR) if use_finetuned
                           else config.BASE_EMBEDDER)
        collection = config.COLLECTION_FINETUNED if use_finetuned else config.COLLECTION_BASE
        self.model = SentenceTransformer(self.model_name)
        self.collection = client.get_collection(collection)
        self._bm25 = None
        self._rerankers: dict[str, CrossEncoder] = {}
        # PyTorch sobre la GPU de Apple (MPS) no admite llamadas concurrentes
        # desde varios hilos: dos consultas simultáneas tumbaban el proceso.
        # Los modelos locales se usan de uno en uno; la generación (Ollama) no
        # pasa por aquí y sigue siendo concurrente.
        self._torch_lock = Lock()

    def embed(self, texts: list[str]):
        with self._torch_lock:
            return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    # --- Componentes ---------------------------------------------------------
    def _corpus(self):
        """Índice BM25 sobre los mismos fragmentos de la colección (se construye
        una vez, en memoria; el corpus tiene unos cientos de fragmentos)."""
        if self._bm25 is None:
            data = self.collection.get(include=["documents", "metadatas", "embeddings"])
            self._ids = data["ids"]
            self._docs = dict(zip(data["ids"], data["documents"]))
            self._metas = dict(zip(data["ids"], data["metadatas"]))
            self._embs = dict(zip(data["ids"], np.asarray(data["embeddings"])))
            self._bm25 = BM25Okapi([_tokens(d) for d in data["documents"]])
        return self._bm25

    def _dense(self, query_embedding, n: int) -> list[str]:
        res = self.collection.query(query_embeddings=[query_embedding.tolist()], n_results=n)
        return res["ids"][0]

    def _lexical(self, query: str, n: int) -> list[str]:
        scores = self._corpus().get_scores(_tokens(query))
        order = np.argsort(-scores)[:n]
        return [self._ids[i] for i in order if scores[i] > 0]

    def _reranker(self, name: str) -> CrossEncoder:
        if name not in self._rerankers:
            self._rerankers[name] = CrossEncoder(RERANKERS[name], max_length=512)
        return self._rerankers[name]

    # --- Búsqueda ------------------------------------------------------------
    def search(self, query: str, k: int | None = None, query_embedding=None,
               mode: str | None = None, reranker: str | None = "default",
               candidates: int | None = None) -> list[dict]:
        k = k if k is not None else rc.get("top_k")
        mode = mode or rc.get("retrieval_mode")
        reranker = rc.get("reranker") if reranker == "default" else reranker
        n = max(k, candidates or rc.get("rerank_candidates"))
        if query_embedding is None:
            query_embedding = self.embed([query])[0]
        self._corpus()

        dense = self._dense(query_embedding, n)
        if mode == "hybrid":
            fused: dict[str, float] = {}
            for ranking in (dense, self._lexical(query, n)):
                for rank, cid in enumerate(ranking, 1):
                    fused[cid] = fused.get(cid, 0.0) + 1.0 / (self.RRF_K + rank)
            ranked = sorted(fused, key=fused.get, reverse=True)[:n]
            rank_scores = [fused[c] for c in ranked]
        else:
            ranked, rank_scores = dense, [None] * len(dense)

        if reranker:
            with self._torch_lock:
                scores = self._reranker(reranker).predict(
                    [(query, self._docs[c]) for c in ranked], show_progress_bar=False)
            order = np.argsort(-np.asarray(scores))
            ranked = [ranked[i] for i in order]
            rank_scores = [float(scores[i]) for i in order]

        hits = []
        for cid, rs in list(zip(ranked, rank_scores))[:k]:
            cosine = float(np.dot(self._embs[cid], query_embedding))
            hits.append({**self._metas[cid], "id": cid, "text": self._docs[cid],
                         "score": round(cosine, 4),
                         **({"rank_score": round(rs, 4)} if rs is not None else {})})
        return hits


class TopicClassifier:
    """Regresión logística sobre los embeddings de la consulta (ver
    training/train_classifier.py). Predice el tema o 'fuera_de_dominio'."""

    def __init__(self, embedder_name: str):
        self.model = None
        if not config.CLASSIFIER_PATH.exists():
            return
        bundle = joblib.load(config.CLASSIFIER_PATH)
        # Se compara solo el nombre del modelo: la ruta absoluta cambia entre
        # máquinas y dentro del contenedor
        if Path(bundle["embedder"]).name != Path(embedder_name).name:
            log.warning("El clasificador fue entrenado con otro modelo de embeddings; se ignora")
            return
        self.model = bundle["model"]

    @property
    def ready(self) -> bool:
        return self.model is not None

    def predict(self, embedding) -> dict:
        probs = self.model.predict_proba([embedding])[0]
        classes = list(self.model.classes_)
        ood_idx = classes.index(config.OUT_OF_DOMAIN)
        in_domain_prob = 1.0 - float(probs[ood_idx])
        # Tema más probable excluyendo la clase fuera de dominio
        ranked = sorted(((p, c) for c, p in zip(classes, probs) if c != config.OUT_OF_DOMAIN),
                        reverse=True)
        threshold = rc.get("in_domain_threshold")
        return {
            "topic": ranked[0][1],
            "topic_confidence": round(float(ranked[0][0]) / max(in_domain_prob, 1e-9), 4),
            "in_domain_probability": round(in_domain_prob, 4),
            "in_domain": in_domain_prob >= threshold,
            "threshold": threshold,
        }


class RagEngine:
    def __init__(self):
        self.retriever = Retriever()
        self.classifier = TopicClassifier(self.retriever.model_name)
        self.events: deque = deque(maxlen=200)
        self._lock = Lock()

    # --- Registro de eventos para el panel de administración -----------------
    def _event(self, source: str, level: str, message: str):
        with self._lock:
            self.events.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "type": level,
                "source": source,
                "message": message,
            })

    def recent_events(self, source: str | None = None, limit: int = 50) -> list[dict]:
        with self._lock:
            items = [e for e in self.events if source is None or e["source"] == source]
        return items[-limit:]

    # --- Generador -----------------------------------------------------------
    def generator_model(self, prefer_finetuned: bool | None = None) -> str:
        """Modelo propio si está registrado en Ollama y está preferido en la
        configuración; si no, el modelo base."""
        if prefer_finetuned is None:
            prefer_finetuned = rc.get("prefer_finetuned_generator")
        order = ((config.GENERATOR_MODEL, config.BASE_GENERATOR_MODEL) if prefer_finetuned
                else (config.BASE_GENERATOR_MODEL, config.GENERATOR_MODEL))
        try:
            available = llm.list_models()
        except Exception:  # noqa: BLE001
            return order[0]
        for name in order:
            if name in available or f"{name}:latest" in available:
                return name
        return order[0]

    # --- Consulta completa ---------------------------------------------------
    def answer(self, question: str, history: list[dict] | None = None,
               top_k: int | None = None, use_rag: bool = True,
               model: str | None = None) -> dict:
        settings = rc.get_all()
        t0 = time.perf_counter()
        if ADVERSARIAL_RE.search(question):
            self._event("classifier", "WARN", "Consulta bloqueada por el filtro de seguridad")
            return self._result(REFUSAL_OUT_OF_DOMAIN, [], None, None, t0, t0, t0,
                                refused="adversarial")

        embedding = self.retriever.embed([question])[0]

        classification = None
        if self.classifier.ready:
            classification = self.classifier.predict(embedding)
            if not classification["in_domain"]:
                self._event("classifier", "WARN",
                            f"Consulta fuera de dominio (p={classification['in_domain_probability']:.2f})")
                return self._result(REFUSAL_OUT_OF_DOMAIN, [], classification, None, t0, t0, t0,
                                    refused="out_of_domain")

        t1 = time.perf_counter()
        top_k = top_k if top_k is not None else settings["top_k"]
        sources = self.retriever.search(question, k=top_k, query_embedding=embedding) if use_rag else []
        t2 = time.perf_counter()
        if use_rag:
            # Con reranker el primer fragmento no es necesariamente el de mayor
            # similitud coseno; el umbral se aplica al mejor de los recuperados
            best = max((s["score"] for s in sources), default=0.0)
            self._event("vectordb", "INFO",
                        f"{len(sources)} fragmentos recuperados en {(t2 - t1) * 1000:.0f} ms "
                        f"(mejor: {sources[0]['reference'] if sources else '-'}, similitud {best:.2f})")
            if best < settings["min_retrieval_score"]:
                return self._result(REFUSAL_NO_CONTEXT, sources, classification, None, t0, t1, t2,
                                    refused="no_context")

        model = model or self.generator_model(settings["prefer_finetuned_generator"])
        messages = build_messages(question, sources, history,
                                  system_prompt=settings["system_prompt"]) if use_rag else [
            {"role": "user", "content": question}]
        try:
            text = llm.chat(model, messages, temperature=settings["temperature"], max_tokens=500,
                            num_ctx=settings["num_ctx"])
        except llm.OllamaError as e:
            self._event("llm", "ERROR", str(e))
            raise
        t3 = time.perf_counter()
        self._event("llm", "SUCCESS", f"Respuesta generada con {model} en {(t3 - t2) * 1000:.0f} ms")
        return self._result(text, sources, classification, model, t0, t1, t2, t3)

    def _result(self, text, sources, classification, model, t0, t1, t2, t3=None, refused=None):
        t3 = t3 or time.perf_counter()
        return {
            "answer": text,
            "refused": refused,
            "model": model,
            "topic": classification["topic"] if classification else None,
            "in_domain": classification["in_domain"] if classification else None,
            "classification": classification,
            "sources": [{
                "reference": s["reference"],
                "article_key": s["article_key"],
                "heading": s["heading"],
                "score": s["score"],
                "text": s["text"],
            } for s in sources],
            "latency_ms": {
                "classification": round((t1 - t0) * 1000),
                "retrieval": round((t2 - t1) * 1000),
                "generation": round((t3 - t2) * 1000),
                "total": round((t3 - t0) * 1000),
            },
        }
