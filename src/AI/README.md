# VialBot — Motor de IA (RAG con modelos propios)

Servicio Python que implementa la arquitectura RAG del trabajo de graduación.
Todo corre **localmente**: no se usa ninguna API comercial (OpenAI, etc.).

## Modelos propios

| Componente | Modelo base (abierto) | Entrenamiento propio | Uso |
|---|---|---|---|
| **Embeddings** | `paraphrase-multilingual-MiniLM-L12-v2` | Fine-tuning contrastivo (Multiple Negatives Ranking Loss) con pares *consulta coloquial → artículo* | Búsqueda semántica en ChromaDB |
| **Generador (LLM)** | `Qwen2.5-1.5B-Instruct` (Apache 2.0) | Fine-tuning LoRA con MLX sobre el Prompt Maestro + contexto recuperado + respuesta fundamentada | Redacta la respuesta citando el artículo |
| **Clasificador** | — | Regresión logística sobre embeddings | Tema de la consulta (objetivo 3) y rechazo de preguntas fuera de dominio |

El dataset de entrenamiento es **sintético** y se genera localmente con un modelo maestro
(`qwen3:8b` en Ollama) a partir de cada fragmento de la ley. El banco de pruebas lo
redacta un modelo de **otra familia** (`gemma3:4b`) y el juez es un tercer modelo
(`qwen2.5:7b`), para no evaluar con el mismo estilo con que se entrenó.

## Estructura

```text
config.py                  Rutas, modelos e hiperparámetros
data/raw/                  PDFs oficiales (Ley 132-96 y Reglamento 273-98)
data/processed/            Texto limpio, artículos y fragmentos (chunks.jsonl)
data/dataset/              Dataset sintético (QA, fuera de dominio, SFT)
pipeline/extract.py        Fase I   – extracción y limpieza (regex)
pipeline/chunk.py          Fase II  – segmentación por artículo con traslape
pipeline/build_index.py    Fase III – embeddings + ChromaDB (coseno)
service/                   Fase IV/V – API FastAPI, orquestación RAG, Prompt Maestro
training/                  Generación del dataset y entrenamiento de los 3 modelos
eval/                      Banco de pruebas, métricas y pruebas de límites
eval/results/              Resultados en JSON (los muestra el panel de administración)
```

## Reproducir todo desde cero (Mac con Apple Silicon)

Requisitos: Python 3.12, [uv](https://docs.astral.sh/uv/) y [Ollama](https://ollama.com).

```bash
cd Prototipo/AI
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-train.txt
ollama pull qwen3:8b && ollama pull gemma3:4b && ollama pull qwen2.5:7b && ollama pull qwen2.5:1.5b

# 1. Corpus (Fases I–III)
.venv/bin/python -m pipeline.extract
.venv/bin/python -m pipeline.chunk
.venv/bin/python -m pipeline.build_index --only base

# 2. Dataset sintético y banco de pruebas (~3 h; reanudable)
.venv/bin/python -m training.generate_dataset testbench
.venv/bin/python -m training.generate_dataset ood
.venv/bin/python -m training.generate_dataset qa

# 3. Entrenamiento de los modelos propios
.venv/bin/python -m training.train_embedder
.venv/bin/python -m pipeline.build_index --only vialbot
.venv/bin/python -m training.train_classifier
.venv/bin/python -m training.train_generator all     # LoRA + registro en Ollama como "vialbot"

# 4. Evaluación (examen crítico): ver eval/EXPERIMENTOS.md
#    Banco revisado y congelado (eval/testbench.jsonl) y división 50/50 (eval/split.json):
#    las decisiones se toman con --split dev; --split test se usa una sola vez.
.venv/bin/python -m eval.eval_retrieval --split test --reranker bge-m3 --tag final_bge
.venv/bin/python -m eval.eval_generation --split test --tag final
.venv/bin/python -m eval.eval_boundary --split test --tag final
.venv/bin/python -m eval.analysis        # IC 95%, pruebas pareadas y taxonomía de errores
.venv/bin/python -m eval.bench           # latencia por etapa y prueba de carga (servicio en marcha)
.venv/bin/python -m eval.human_eval sheet|score   # validación humana del juez
```

> **Importante:** el banco de pruebas (`eval/testbench.jsonl`) fue generado
> automáticamente. Antes de reportar resultados en el documento final, revisa cada
> pregunta y marca `"reviewed": true` (corrige el artículo esperado si hace falta).

## Ejecutar el servicio

```bash
.venv/bin/uvicorn service.app:app --port 8000         # local
docker compose up -d --build ai                        # con Docker (desde Prototipo/, solo CPU)
../deploy/vialbot.sh deploy                            # producción en la Mac Mini (motor de IA con GPU)
```

Ollama debe estar corriendo en la máquina anfitriona con el modelo `vialbot`. Si no
existe, el servicio usa `qwen2.5:1.5b` sin ajustar y lo indica en `/health`.

| Endpoint | Descripción |
|---|---|
| `GET /health` | Estado de embeddings, ChromaDB, clasificador y LLM |
| `POST /query` | Consulta completa: filtro de seguridad → clasificación → recuperación → generación |
| `POST /retrieve` | Solo recuperación (fragmentos, similitud y clasificación) |
| `GET /corpus` | Documentos indexados, artículos y fragmentos |
| `GET /config` | Arquitectura fija (modelos base, segmentación) |
| `GET/PUT /settings` | Parámetros ajustables en caliente: Top K (7), modo de recuperación (`dense`/`hybrid`), reranker (`bge-m3`, `mmarco-minilm` o ninguno), candidatos del reranker (20), `num_ctx` (8192), umbrales, temperatura, preferencia de modelo y Prompt Maestro. `PUT {"reset": true}` restaura los valores por defecto. Se guardan en `data/runtime_config.json` |
| `GET /metrics` | Resultados de evaluación (`eval/results/*.json`) |
| `GET /logs` | Eventos recientes del motor |

Antes del clasificador de dominio, `service/rag.py` aplica un filtro de seguridad por
expresiones regulares (`ADVERSARIAL_RE`) que bloquea intentos de manipulación del
Prompt Maestro y mezclas con normativa de otros países, sin necesidad de invocar al LLM.

Si se define `AI_SERVICE_TOKEN`, todas las peticiones (excepto `/health`) deben enviar la
cabecera `X-Internal-Token`. El servicio no debe exponerse a internet: solo el backend PHP lo consume.
