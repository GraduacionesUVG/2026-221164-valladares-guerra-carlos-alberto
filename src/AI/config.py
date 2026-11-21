"""Configuración central del motor de IA de VialBot.

Todas las rutas y nombres de modelos se definen aquí para que el pipeline de
ingesta, el entrenamiento, la evaluación y el servicio usen exactamente los
mismos artefactos. Cada valor puede sobrescribirse con variables de entorno.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# --- Datos -------------------------------------------------------------------
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DATASET_DIR = BASE_DIR / "data" / "dataset"
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", BASE_DIR / "data" / "chroma"))
MODELS_DIR = Path(os.getenv("MODELS_DIR", BASE_DIR / "models"))
EVAL_DIR = BASE_DIR / "eval"
RESULTS_DIR = EVAL_DIR / "results"

# Corpus oficial (muestra delimitada del protocolo)
DOCUMENTS = [
    {
        "id": "ley",
        "file": "ley_transito_132-96.pdf",
        "title": "Ley de Tránsito (Decreto 132-96)",
        "short": "Ley de Tránsito",
        "source": "https://transito.gob.gt/wp-content/uploads/2019/02/Ley-de-Transito.pdf",
    },
    {
        "id": "reglamento",
        "file": "reglamento_transito_273-98.pdf",
        "title": "Reglamento de Tránsito (Acuerdo Gubernativo 273-98)",
        "short": "Reglamento de Tránsito",
        "source": "https://portal.pnc.edu.gt/wp-content/uploads/2023/09/Reglamento-de-Transito.pdf",
    },
]

# --- Segmentación (chunking) -------------------------------------------------
# Un artículo es la unidad de análisis. Solo los artículos más largos que
# CHUNK_MAX_CHARS se subdividen, con un traslape de CHUNK_OVERLAP_CHARS.
CHUNK_MAX_CHARS = int(os.getenv("CHUNK_MAX_CHARS", 1500))
CHUNK_OVERLAP_CHARS = int(os.getenv("CHUNK_OVERLAP_CHARS", 250))

# --- Modelos -----------------------------------------------------------------
# Modelo base de embeddings (pre-entrenado, multilingüe) y el modelo propio
# obtenido tras el fine-tuning con el dataset de consultas ciudadanas.
BASE_EMBEDDER = os.getenv(
    "BASE_EMBEDDER", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
FINETUNED_EMBEDDER_DIR = MODELS_DIR / "vialbot-embedder"
CLASSIFIER_PATH = MODELS_DIR / "vialbot-classifier.joblib"

# Colección de ChromaDB (una por modelo de embeddings para poder compararlos)
COLLECTION_BASE = "ley_transito_base"
COLLECTION_FINETUNED = "ley_transito_vialbot"

# --- LLM generador (servido por Ollama) ----------------------------------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
# Modelo propio (Qwen2.5-1.5B-Instruct + LoRA entrenado con nuestro dataset)
GENERATOR_MODEL = os.getenv("GENERATOR_MODEL", "vialbot")
# Modelo base sin fine-tuning, usado solo en la evaluación comparativa
BASE_GENERATOR_MODEL = os.getenv("BASE_GENERATOR_MODEL", "qwen2.5:1.5b")
# Modelo maestro local: genera el dataset sintético de entrenamiento.
# Nunca se usa para responder a los usuarios.
TEACHER_MODEL = os.getenv("TEACHER_MODEL", "qwen3:8b")
# El banco de pruebas lo redacta un modelo de otra familia (Gemma) para que las
# preguntas de evaluación no compartan el estilo de las de entrenamiento, y el
# juez es distinto del maestro para no favorecer sus propias respuestas.
TESTBENCH_MODEL = os.getenv("TESTBENCH_MODEL", "gemma3:4b")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "qwen2.5:7b")

GENERATOR_BASE_HF = "Qwen/Qwen2.5-1.5B-Instruct"
GENERATOR_ADAPTER_DIR = MODELS_DIR / "vialbot-generator-lora"
GENERATOR_FUSED_DIR = MODELS_DIR / "vialbot-generator-fused"

# --- Recuperación ------------------------------------------------------------
# K = 7 elegido en desarrollo (eval/EXPERIMENTOS.md, Fase 5)
TOP_K = int(os.getenv("TOP_K", 7))
# Umbral de probabilidad del clasificador para considerar una consulta dentro
# del dominio de tránsito. Por debajo, el asistente rechaza la pregunta.
IN_DOMAIN_THRESHOLD = float(os.getenv("IN_DOMAIN_THRESHOLD", 0.5))

TOPICS = [
    "multas",
    "licencias",
    "documentos_vehiculares",
    "normas_circulacion",
    "senales",
    "accidentes",
    "autoridades",
    "equipamiento_vehicular",
    "transporte_carga_pasajeros",
]
OUT_OF_DOMAIN = "fuera_de_dominio"


def ensure_dirs():
    for d in (PROCESSED_DIR, DATASET_DIR, CHROMA_DIR, MODELS_DIR, RESULTS_DIR):
        d.mkdir(parents=True, exist_ok=True)
