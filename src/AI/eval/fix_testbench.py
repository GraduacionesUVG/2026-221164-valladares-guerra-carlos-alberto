"""Revisión manual del banco de pruebas (única, 2026-09-30).

Aplica las correcciones aprobadas por el autor pregunta por pregunta, marca las
100 preguntas como revisadas y congela el banco. El banco generado se conserva
en testbench_v0_generado.jsonl y cada cambio queda registrado en
testbench_corrections.json.

    .venv/bin/python -m eval.fix_testbench
"""
import json
import shutil
from pathlib import Path

EVAL = Path(__file__).parent
BANK = EVAL / "testbench.jsonl"
ORIGINAL = EVAL / "testbench_v0_generado.jsonl"
LOG = EVAL / "testbench_corrections.json"


def ref(doc: str, art: int) -> dict:
    name = "Ley de Tránsito" if doc == "ley" else "Reglamento de Tránsito"
    return {"expected_article": f"{doc}:{art}", "chunk_id": f"{doc}-art{art}-0",
            "reference": f"{name}, Artículo {art}"}


# (id, motivo, campos nuevos)
CORRECTIONS = [
    # Artículo esperado incorrecto
    ("tb-004", "articulo", ref("reglamento", 25)),  # pregunta por la licencia, no por el permiso de aprendizaje
    ("tb-011", "articulo", ref("reglamento", 82)),  # conductor ante obras: prevalece la señalización de obras
    ("tb-039", "articulo", ref("reglamento", 44)),
    ("tb-048", "articulo", ref("reglamento", 144)),
    ("tb-052", "articulo", {**ref("reglamento", 7), "chunk_id": "reglamento-art7-2"}),  # definiciones 13 y 114
    ("tb-078", "articulo", ref("reglamento", 62)),
    ("tb-088", "articulo", ref("reglamento", 82)),  # órdenes de los agentes, no norma de peatones
    ("tb-098", "articulo", ref("reglamento", 100)),
    # Reescritas para que coincidan con su artículo
    ("tb-042", "reescrita", {"question": "Si tengo que ceder el paso para entrar a una calle principal, ¿cuándo puedo arrancar?"}),
    ("tb-063", "reescrita", {"question": "¿Quién se encarga de hacer el reglamento de la Ley de Tránsito?",
                             "category": "circulacion_general"}),
    # Ambiguas
    ("tb-012", "ambigua", {"question": "Si manejo un bus de transporte público y no hay carril exclusivo, ¿por qué carril tengo que ir?"}),
    ("tb-018", "ambigua", {"question": "¿Puedo ir rápido en una zona escolar si no hay niños cerca?"}),
    ("tb-040", "ambigua", {"question": "Si no hay ninguna señal, ¿igual tengo que ir por la derecha en una curva?"}),
    ("tb-077", "ambigua", {"question": "Si manejo un taxi, ¿puedo parar en la calle para que se bajen mis pasajeros si es rápido?"}),
    # Redacción
    ("tb-002", "redaccion", {"question": "¿Puedo estacionar mi coche donde quiera en la calle si la municipalidad lo permite?"}),
    ("tb-067", "redaccion", {"question": "Si el Ministerio de Gobernación contrata a una empresa para hacer funciones del Departamento de Tránsito, ¿esa empresa tiene que cumplir con las leyes de tránsito?"}),
    ("tb-085", "redaccion", {"question": "¿Pueden varias municipalidades trabajar juntas para controlar el tránsito en sus ciudades?"}),
    ("tb-089", "redaccion", {"question": "Si choco mientras aprendo a manejar con un instructor, ¿quién responde por los daños?",
                             "category": "accidentes"}),
    # Categorías (taxonomía del banco: licencias, multas, accidentes, circulacion_general)
    ("tb-001", "categoria", {"category": "circulacion_general"}),
    ("tb-010", "categoria", {"category": "circulacion_general"}),
    ("tb-066", "categoria", {"category": "circulacion_general"}),
    ("tb-075", "categoria", {"category": "circulacion_general"}),
    ("tb-079", "categoria", {"category": "circulacion_general"}),
]
DOUBLE_QUESTION_MARK = ["tb-026", "tb-032", "tb-034", "tb-087", "tb-092"]


def main():
    if ORIGINAL.exists():
        raise SystemExit("El banco ya fue corregido y congelado; no se vuelve a modificar.")
    shutil.copy(BANK, ORIGINAL)
    rows = [json.loads(line) for line in BANK.open(encoding="utf-8")]
    by_id = {r["id"]: r for r in rows}
    log = []
    for case_id, reason, fields in CORRECTIONS:
        row = by_id[case_id]
        before = {k: row[k] for k in fields}
        row.update(fields)
        log.append({"id": case_id, "motivo": reason, "antes": before, "despues": fields})
    for case_id in DOUBLE_QUESTION_MARK:
        row = by_id[case_id]
        before = row["question"]
        assert before.startswith("¿") and before.count("¿") == 2, case_id
        row["question"] = before[1:]
        log.append({"id": case_id, "motivo": "redaccion", "antes": {"question": before},
                    "despues": {"question": row["question"]}})
    for row in rows:
        row["reviewed"] = True
    with BANK.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(log)} correcciones aplicadas; {len(rows)} preguntas revisadas")


if __name__ == "__main__":
    main()
