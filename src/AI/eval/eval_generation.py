"""Métricas semánticas de generación con LLM-as-a-Judge.

Diseño cuasi-experimental: se responde el mismo banco de pruebas bajo tres
condiciones y un modelo juez (distinto del maestro que generó los datos de
entrenamiento) califica cada respuesta sin saber qué condición la produjo.

  A. llm_sin_rag       modelo base (Qwen2.5-1.5B) respondiendo solo con su
                       conocimiento interno, sin contexto legal.
  B. llm_base_rag      modelo base + RAG (Prompt Maestro y fragmentos).
  C. vialbot           sistema completo: modelo propio + RAG.

Criterios (escala 1 a 5):
  fidelidad    todo lo afirmado está respaldado por el artículo oficial
               (penaliza alucinaciones).
  relevancia   la respuesta atiende directamente la consulta.
  claridad     es comprensible para un ciudadano sin formación jurídica.
Además, de forma automática:
  cita_correcta  la respuesta menciona el número del artículo esperado.

Salida: eval/results/generation.json, o results/exp/generation_<tag>_<split>.json
con --tag (experimentos; no se sobrescribe generation.json).

Uso:  python -m eval.eval_generation [--n 50]
      python -m eval.eval_generation --split dev --conditions vialbot --top-k 4 --tag base
"""
import argparse
import json
import random
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from eval.make_split import load_split  # noqa: E402
from service import llm  # noqa: E402
from service import runtime_config as rc  # noqa: E402
from service.rag import RagEngine  # noqa: E402
from training.common import load_chunks_by_id  # noqa: E402

JUDGE_PROMPT = """Eres un evaluador imparcial experto en la Ley de Tránsito de Guatemala.
Califica la RESPUESTA de un asistente a la CONSULTA de un ciudadano, comparándola con el ARTÍCULO OFICIAL que contiene la información correcta.

Criterios (entero de 1 a 5):
- fidelidad: 5 = todo lo afirmado coincide con el artículo oficial; 1 = contiene datos inventados o contradictorios (montos, plazos, requisitos). Una negativa honesta sin datos falsos recibe 3.
- relevancia: 5 = responde directamente lo que se preguntó; 1 = no responde la consulta.
- claridad: 5 = muy clara para un ciudadano sin formación jurídica; 1 = confusa.

ARTÍCULO OFICIAL:
{article}

CONSULTA:
{question}

RESPUESTA:
{answer}

Responde solo con JSON: {{"fidelidad": n, "relevancia": n, "claridad": n, "justificacion": "una oración"}}"""


def article_text(chunks: dict, article_key: str) -> str:
    parts = sorted((c for c in chunks.values() if c["article_key"] == article_key),
                   key=lambda c: c["part"])
    return "\n".join(c["text"] for c in parts)[:4000]


def cites(answer: str, article_key: str) -> bool:
    number = article_key.split(":")[1]
    return re.search(rf"[Aa]rt[íi]culo\s+{number}\b", answer) is not None


def judge(article: str, question: str, answer: str) -> dict:
    data = llm.chat_json(config.JUDGE_MODEL, [{"role": "user", "content":
                         JUDGE_PROMPT.format(article=article, question=question, answer=answer)}],
                         temperature=0.0, max_tokens=250)
    return {k: int(data.get(k, 1)) for k in ("fidelidad", "relevancia", "claridad")} | {
        "justificacion": data.get("justificacion") or data.get("justificación", "")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=50, help="consultas del banco a evaluar")
    parser.add_argument("--split", choices=["all", "dev", "test"], default="all",
                        help="dev/test: se evalúan todas las preguntas del subconjunto")
    parser.add_argument("--conditions", default="llm_sin_rag,llm_base_rag,vialbot")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--mode", choices=["dense", "hybrid"], default=None)
    parser.add_argument("--reranker", default=None, help='clave de RERANKERS o "none"')
    parser.add_argument("--num-ctx", type=int, default=None)
    parser.add_argument("--tag", default=None)
    parser.add_argument("--generator", default=config.GENERATOR_MODEL,
                        help="modelo de Ollama para la condición C (p. ej. vialbot-v3)")
    args = parser.parse_args()

    with open(config.EVAL_DIR / "testbench.jsonl", encoding="utf-8") as f:
        testbench = [json.loads(line) for line in f]
    if args.split == "all":
        testbench = random.Random(1).sample(testbench, min(args.n, len(testbench)))
    else:
        ids = load_split(args.split)
        testbench = [r for r in testbench if r["id"] in ids]
    overrides = {k: v for k, v in {"top_k": args.top_k, "retrieval_mode": args.mode,
                                   "reranker": args.reranker, "num_ctx": args.num_ctx}.items()
                 if v is not None}
    if args.reranker == "none":  # línea base: sin reranker aunque esté activo por defecto
        overrides["reranker"] = None
    if not args.tag and (args.split != "all" or overrides):
        raise SystemExit("Los experimentos requieren --tag (no se sobrescribe generation.json)")
    with rc.override(overrides):
        run(args, testbench, overrides)


def run(args, testbench, overrides):
    chunks = load_chunks_by_id()
    engine = RagEngine()
    available = llm.list_models()
    own_available = args.generator in available or f"{args.generator}:latest" in available

    conditions = {
        "llm_sin_rag": dict(use_rag=False, model=config.BASE_GENERATOR_MODEL),
        "llm_base_rag": dict(use_rag=True, model=config.BASE_GENERATOR_MODEL),
    }
    if own_available:
        conditions["vialbot"] = dict(use_rag=True, model=args.generator)
    else:
        print(f"[eval] el modelo propio '{args.generator}' no está en Ollama; se omite la condición C")
    wanted = args.conditions.split(",")
    conditions = {k: v for k, v in conditions.items() if k in wanted}

    # El clasificador se desactiva para medir solo la generación
    classifier_model = engine.classifier.model
    engine.classifier.model = None

    rows = []
    for i, case in enumerate(testbench, 1):
        article = article_text(chunks, case["expected_article"])
        row = {"id": case["id"], "question": case["question"],
               "expected_article": case["expected_article"], "conditions": {}}
        for name, kwargs in conditions.items():
            result = engine.answer(case["question"], **kwargs)
            scores = judge(article, case["question"], result["answer"])
            row["conditions"][name] = {
                "answer": result["answer"],
                "sources": [s["article_key"] for s in result["sources"]],
                "latency_ms": result["latency_ms"]["total"],
                "cita_correcta": cites(result["answer"], case["expected_article"]),
                **scores,
            }
        rows.append(row)
        summary = " | ".join(f"{k}: F{v['fidelidad']} R{v['relevancia']}"
                             for k, v in row["conditions"].items())
        print(f"[eval] {i}/{len(testbench)} {case['id']} {summary}")

    engine.classifier.model = classifier_model

    def agg(name: str) -> dict:
        vals = [r["conditions"][name] for r in rows]
        return {
            "fidelidad": round(statistics.mean(v["fidelidad"] for v in vals), 3),
            "relevancia": round(statistics.mean(v["relevancia"] for v in vals), 3),
            "claridad": round(statistics.mean(v["claridad"] for v in vals), 3),
            "cita_correcta": round(sum(v["cita_correcta"] for v in vals) / len(vals), 3),
            "alucinacion_grave": round(sum(v["fidelidad"] <= 2 for v in vals) / len(vals), 3),
            "latencia_ms_mediana": int(statistics.median(v["latency_ms"] for v in vals)),
        }

    result = {
        "n": len(rows),
        "split": args.split,
        "judge": config.JUDGE_MODEL,
        "config": {**{k: rc.get(k) for k in ("top_k", "retrieval_mode", "reranker", "num_ctx")},
                   "generator": args.generator},
        "summary": {name: agg(name) for name in conditions},
        "rows": rows,
    }
    if args.tag:
        out = config.RESULTS_DIR / "exp" / f"generation_{args.tag}_{args.split}.json"
    else:
        out = config.RESULTS_DIR / "generation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result["config"], ensure_ascii=False))
    print(json.dumps(result["summary"], indent=2, ensure_ascii=False))
    print(f"→ {out.relative_to(config.BASE_DIR)}")


if __name__ == "__main__":
    main()
