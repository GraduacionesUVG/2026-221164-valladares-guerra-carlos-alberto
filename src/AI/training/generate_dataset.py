"""Generación sintética de datos (técnica secundaria del protocolo).

Usa un modelo de lenguaje auxiliar que corre localmente en Ollama (el "modelo
maestro") para producir, a partir de cada fragmento de la normativa:

  qa        consultas ciudadanas coloquiales (con guatemaltequismos, errores de
            ortografía y expresiones difusas), su respuesta fundamentada en el
            fragmento y el tema del fragmento.
            -> data/dataset/synthetic_qa.jsonl

  ood       consultas fuera del dominio de tránsito, para enseñar al
            clasificador a rechazar preguntas ajenas.
            -> data/dataset/out_of_domain.jsonl

  verify    control de calidad: el modelo maestro revisa cada par contra su
            fragmento y descarta los que afirman algo que el fragmento no dice.
            -> data/dataset/synthetic_qa_verified.jsonl

  testbench banco de pruebas: 100 consultas generadas por un modelo DISTINTO al
            maestro (para no evaluar con el mismo estilo de redacción con que se
            entrenó), cada una con el artículo que la responde.
            -> eval/testbench.jsonl  (debe revisarse manualmente)

El proceso es reanudable: si se interrumpe, continúa donde se quedó.

Uso:  python -m training.generate_dataset qa|verify|ood|testbench
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from service import llm  # noqa: E402

QA_PER_CHUNK = 5

QA_PROMPT = """Eres un experto en la normativa de tránsito de Guatemala y en cómo hablan los guatemaltecos.

Te daré un fragmento oficial de la normativa. Genera {n} consultas DISTINTAS que un ciudadano guatemalteco común escribiría en un chat para resolver una duda que ESTE fragmento responde, junto con la respuesta correcta.

Requisitos de las consultas:
- Lenguaje cotidiano, como en WhatsApp. Varía el estilo: algunas formales, otras muy informales.
- Usa modismos de Guatemala cuando tenga sentido (ej. "carro", "moto", "camioneta" para bus, "chonte" o "la PMT" para agentes de tránsito, "me pusieron una remisión", "la placa", "polarizado", "vos", "va", "púchica").
- Incluye en al menos 2 consultas faltas de ortografía o falta de tildes típicas.
- No menciones el número de artículo ni copies frases literales del fragmento.

Requisitos de las respuestas:
- Basadas SOLO en el fragmento; no inventes montos, plazos ni requisitos que no aparezcan.
- Cordiales, claras y breves (2 a 5 oraciones), para alguien sin formación jurídica.
- Terminan citando la fuente exactamente así: ({reference}).

Además clasifica el tema principal del fragmento con UNA de estas etiquetas: {topics}.

Responde solo con JSON con esta forma:
{{"tema": "...", "items": [{{"pregunta": "...", "respuesta": "..."}}]}}

FRAGMENTO:
{text}"""

OOD_CATEGORIES = [
    "recetas de cocina", "reparación de computadoras y celulares", "derecho laboral y despidos",
    "derecho de familia, divorcios y pensiones alimenticias", "impuestos de la SAT y facturación",
    "salud y síntomas de enfermedades", "fútbol y deportes", "tareas de matemáticas",
    "programación y software", "viajes y turismo en Guatemala", "clima y desastres naturales",
    "trámites de pasaporte y DPI en RENAP", "compra y venta de casas", "finanzas personales y préstamos",
    "historia de Guatemala", "mecánica automotriz sin relación con la ley (ej. cambiar aceite)",
    "política y elecciones", "mascotas", "relaciones de pareja", "religión",
    "instrucciones para cometer delitos o evadir a la policía",
    "saludos y conversación trivial", "tecnología e inteligencia artificial",
    "educación y universidades", "música y entretenimiento",
]

OOD_PROMPT = """Genera {n} mensajes DISTINTOS que un guatemalteco podría escribir en un chat sobre el tema: "{category}".
Varía el estilo (formal, informal, con faltas de ortografía, con modismos guatemaltecos).
Deben ser preguntas o peticiones que NO tengan relación con leyes o reglamentos de tránsito.
Responde solo con JSON: {{"mensajes": ["...", "..."]}}"""

VERIFY_PROMPT = """Eres un revisor estricto. Para cada par pregunta/respuesta, decide si la RESPUESTA es correcta y está completamente respaldada por el FRAGMENTO, y si el FRAGMENTO realmente responde la PREGUNTA.
Marca false si la respuesta inventa montos, plazos, requisitos o excepciones que el fragmento no menciona, si contradice el fragmento, o si la pregunta trata de otro tema.

FRAGMENTO:
{text}

PARES:
{pairs}

Responde solo con JSON: {{"veredictos": [{{"n": 1, "valido": true}}, ...]}} con un veredicto por cada par, en el mismo orden."""

TESTBENCH_PROMPT = """Lee este fragmento de la normativa de tránsito de Guatemala y escribe UNA sola pregunta realista que un ciudadano guatemalteco haría en un chat y que este fragmento responde.
- Lenguaje natural y cotidiano; no copies frases del fragmento ni menciones el número de artículo.
- La pregunta debe poder responderse con este fragmento.
Responde solo con JSON: {{"pregunta": "...", "categoria": "..."}}
La categoría debe ser una de: licencias, multas, accidentes, circulacion_general.

FRAGMENTO:
{text}"""

# Fragmentos sin valor para una consulta ciudadana (organización interna,
# derogatorias y vigencia); no se usan para generar preguntas.
SKIP_HEADINGS = {"Derogatoria", "Vigencia", "Reglamento Orgánico Interno",
                 "Nombramientos y Contrataciones", "Creación y Supresión de Dependencias"}


def ask_json(model: str, prompt: str, retries: int = 3, **kwargs) -> dict:
    """chat_json con reintentos. Si Ollama devuelve respuestas vacías (p. ej.
    tras quedarse sin memoria de GPU), se recarga el modelo antes de reintentar."""
    for attempt in range(1, retries + 1):
        try:
            return llm.chat_json(model, [{"role": "user", "content": prompt}], **kwargs)
        except Exception as e:  # noqa: BLE001
            if attempt == retries:
                raise
            print(f"[retry] intento {attempt} falló ({e}); recargando {model}")
            llm.unload(model)
            time.sleep(5)


def load_chunks() -> list[dict]:
    with open(config.PROCESSED_DIR / "chunks.jsonl", encoding="utf-8") as f:
        chunks = [json.loads(line) for line in f]
    return [c for c in chunks if c["heading"] not in SKIP_HEADINGS]


def done_ids(path: Path, key: str) -> set:
    if not path.exists():
        return set()
    with open(path, encoding="utf-8") as f:
        return {json.loads(line)[key] for line in f if line.strip()}


def append(path: Path, record: dict):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def generate_qa():
    out = config.DATASET_DIR / "synthetic_qa.jsonl"
    chunks = load_chunks()
    done = done_ids(out, "chunk_id")
    pending = [c for c in chunks if c["id"] not in done]
    print(f"[qa] {len(done)} fragmentos listos, {len(pending)} pendientes (maestro: {config.TEACHER_MODEL})")
    for i, c in enumerate(pending, 1):
        t0 = time.time()
        prompt = QA_PROMPT.format(n=QA_PER_CHUNK, reference=c["reference"], text=c["text"],
                                  topics=", ".join(config.TOPICS))
        try:
            data = ask_json(config.TEACHER_MODEL, prompt, temperature=0.8, max_tokens=1600)
        except Exception as e:  # noqa: BLE001 - se reintenta en la próxima corrida
            print(f"[qa] error en {c['id']}: {e}")
            continue
        topic = data.get("tema") if data.get("tema") in config.TOPICS else "normas_circulacion"
        items = [it for it in data.get("items", [])
                 if isinstance(it, dict) and it.get("pregunta") and it.get("respuesta")]
        append(out, {
            "chunk_id": c["id"],
            "article_key": c["article_key"],
            "reference": c["reference"],
            "topic": topic,
            "items": items[:QA_PER_CHUNK],
        })
        print(f"[qa] {i}/{len(pending)} {c['id']}: {len(items)} pares, tema={topic} ({time.time() - t0:.0f}s)")


def verify_qa():
    src = config.DATASET_DIR / "synthetic_qa.jsonl"
    out = config.DATASET_DIR / "synthetic_qa_verified.jsonl"
    chunks = {c["id"]: c for c in load_chunks()}
    done = done_ids(out, "chunk_id")
    with open(src, encoding="utf-8") as f:
        records = [json.loads(line) for line in f]
    pending = [r for r in records if r["chunk_id"] not in done and r["items"]]
    kept_total = total = 0
    for i, r in enumerate(pending, 1):
        pairs = "\n".join(f"{n}. PREGUNTA: {it['pregunta']}\n   RESPUESTA: {it['respuesta']}"
                          for n, it in enumerate(r["items"], 1))
        try:
            data = ask_json(config.TEACHER_MODEL, VERIFY_PROMPT.format(
                text=chunks[r["chunk_id"]]["text"], pairs=pairs), temperature=0.0, max_tokens=400)
        except Exception as e:  # noqa: BLE001
            print(f"[verify] error en {r['chunk_id']}: {e}")
            continue
        verdicts = {int(v.get("n", 0)): bool(v.get("valido")) for v in data.get("veredictos", [])
                    if isinstance(v, dict)}
        kept = [it for n, it in enumerate(r["items"], 1) if verdicts.get(n, False)]
        append(out, {**r, "items": kept, "discarded": len(r["items"]) - len(kept)})
        kept_total += len(kept)
        total += len(r["items"])
        print(f"[verify] {i}/{len(pending)} {r['chunk_id']}: {len(kept)}/{len(r['items'])} válidos")
    if total:
        print(f"[verify] conservados {kept_total}/{total} ({kept_total / total:.0%})")


def generate_ood(per_category: int = 14):
    out = config.DATASET_DIR / "out_of_domain.jsonl"
    done = done_ids(out, "category")
    for category in OOD_CATEGORIES:
        if category in done:
            continue
        data = ask_json(config.TEACHER_MODEL, OOD_PROMPT.format(n=per_category, category=category),
                        temperature=0.9, max_tokens=1200)
        msgs = [m for m in data.get("mensajes", []) if isinstance(m, str) and m.strip()]
        append(out, {"category": category, "messages": msgs})
        print(f"[ood] {category}: {len(msgs)} mensajes")


def generate_testbench(n: int = 100, seed: int = 2026):
    out = config.EVAL_DIR / "testbench.jsonl"
    chunks = load_chunks()
    # Muestreo estratificado: un fragmento por artículo, 100 artículos distintos
    by_article: dict[str, list[dict]] = {}
    for c in chunks:
        by_article.setdefault(c["article_key"], []).append(c)
    rng = random.Random(seed)
    keys = sorted(by_article)
    rng.shuffle(keys)
    sample = [rng.choice(by_article[k]) for k in keys[:n]]

    done = done_ids(out, "chunk_id")
    for i, c in enumerate(sample, 1):
        if c["id"] in done:
            continue
        data = ask_json(config.TESTBENCH_MODEL, TESTBENCH_PROMPT.format(text=c["text"]),
                        temperature=0.7, max_tokens=300)
        if not data.get("pregunta"):
            continue
        append(out, {
            "id": f"tb-{i:03d}",
            "question": data["pregunta"].strip(),
            "category": data.get("categoria", "circulacion_general"),
            "chunk_id": c["id"],
            "expected_article": c["article_key"],
            "reference": c["reference"],
            "reviewed": False,
        })
        print(f"[testbench] {i}/{n} {c['reference']}: {data['pregunta'][:80]}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("task", choices=["qa", "verify", "ood", "testbench"])
    args = parser.parse_args()
    config.ensure_dirs()
    {"qa": generate_qa, "verify": verify_qa, "ood": generate_ood,
     "testbench": generate_testbench}[args.task]()


if __name__ == "__main__":
    main()
