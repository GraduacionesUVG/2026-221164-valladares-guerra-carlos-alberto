"""Entrenamiento del modelo generador propio (VialBot LLM).

Ajusta Qwen2.5-1.5B-Instruct (modelo abierto, licencia Apache 2.0) con LoRA
(Low-Rank Adaptation) sobre el dataset sintético, usando MLX en Apple Silicon.
Cada ejemplo reproduce exactamente la situación de producción: Prompt Maestro +
fragmentos recuperados por nuestro buscador + consulta del ciudadano, y la
respuesta objetivo fundamentada en el artículo correcto. El modelo aprende así
a responder solo con el contexto, en tono ciudadano y citando el artículo.

Se incluye además una fracción de ejemplos sin el artículo relevante en el
contexto, cuya respuesta objetivo es la negativa estándar, para que el modelo
aprenda a no inventar cuando la normativa recuperada no responde la pregunta.

Pasos:
  data     construye data/dataset/sft/{train,valid}.jsonl
  train    entrena el adaptador LoRA (mlx_lm.lora)
  fuse     fusiona el adaptador con el modelo base
  ollama   registra el modelo fusionado en Ollama con el nombre "vialbot"
  all      ejecuta todos los pasos

Uso:  python -m training.train_generator all [--epochs 2]
      python -m training.train_generator all --epochs 1 --lr 5e-5 --version v3 \
          --top-k 7 --reranker bge-m3 --max-seq 4096
      (--version guarda todo aparte: sft_v3/, *-v3/ y el modelo "vialbot-v3" en
      Ollama, sin tocar el modelo vigente)
"""
import argparse
import json
import math
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402
from service import runtime_config as rc  # noqa: E402
from service.prompts import REFUSAL_NO_CONTEXT, build_messages  # noqa: E402
from service.rag import Retriever  # noqa: E402
from training.common import load_chunks_by_id, load_qa_pairs, split_by_chunk  # noqa: E402

SFT_DIR = config.DATASET_DIR / "sft"
ADAPTER_DIR = config.GENERATOR_ADAPTER_DIR
FUSED_DIR = config.GENERATOR_FUSED_DIR
GGUF_PATH = config.MODELS_DIR / "vialbot-generator-q8_0.gguf"
OLLAMA_NAME = config.GENERATOR_MODEL
TOP_K = config.TOP_K
NEGATIVE_RATIO = 0.08
BATCH_SIZE = 2
GRAD_ACCUMULATION = 4  # lote efectivo de 8 ejemplos
BIN = Path(sys.executable).parent
OLLAMA_BIN = shutil.which("ollama") or "/Applications/Ollama.app/Contents/Resources/ollama"

MODELFILE = """FROM {path}
TEMPLATE \"\"\"{{{{- if .System }}}}<|im_start|>system
{{{{ .System }}}}<|im_end|>
{{{{ end }}}}{{{{- range .Messages }}}}{{{{- if ne .Role "system" }}}}<|im_start|>{{{{ .Role }}}}
{{{{ .Content }}}}<|im_end|>
{{{{ end }}}}{{{{- end }}}}<|im_start|>assistant
\"\"\"
PARAMETER stop "<|im_start|>"
PARAMETER stop "<|im_end|>"
PARAMETER temperature 0.1
PARAMETER num_ctx 4096
"""


def set_version(version: str):
    """Rutas y nombre en Ollama separados para una nueva iteración."""
    global SFT_DIR, ADAPTER_DIR, FUSED_DIR, GGUF_PATH, OLLAMA_NAME
    SFT_DIR = config.DATASET_DIR / f"sft_{version}"
    ADAPTER_DIR = config.MODELS_DIR / f"{config.GENERATOR_ADAPTER_DIR.name}-{version}"
    FUSED_DIR = config.MODELS_DIR / f"{config.GENERATOR_FUSED_DIR.name}-{version}"
    GGUF_PATH = config.MODELS_DIR / f"vialbot-generator-{version}-q8_0.gguf"
    OLLAMA_NAME = f"{config.GENERATOR_MODEL}-{version}"


def build_data():
    chunks = load_chunks_by_id()
    retriever = Retriever()
    train_pairs, val_pairs = split_by_chunk(load_qa_pairs())
    rng = random.Random(7)
    SFT_DIR.mkdir(parents=True, exist_ok=True)

    for name, pairs in (("train", train_pairs), ("valid", val_pairs)):
        questions = [p["question"] for p in pairs]
        embeddings = retriever.embed(questions)
        n_neg = 0
        with open(SFT_DIR / f"{name}.jsonl", "w", encoding="utf-8") as f:
            for p, emb in zip(pairs, embeddings):
                hits = retriever.search(p["question"], k=TOP_K + 4, query_embedding=emb)
                negative = rng.random() < NEGATIVE_RATIO
                if negative:
                    # Se quita del contexto todo fragmento del artículo correcto
                    context = [h for h in hits if h["article_key"] != p["article_key"]][:TOP_K]
                    answer = REFUSAL_NO_CONTEXT
                    n_neg += 1
                else:
                    context = [h for h in hits if h["id"] != p["chunk_id"]][:TOP_K - 1]
                    gold = {**chunks[p["chunk_id"]]}
                    # El fragmento correcto se inserta en una posición aleatoria
                    context.insert(rng.randrange(len(context) + 1), gold)
                    answer = p["answer"]
                messages = build_messages(p["question"], context)
                messages.append({"role": "assistant", "content": answer})
                f.write(json.dumps({"messages": messages}, ensure_ascii=False) + "\n")
        print(f"[generator] {name}: {len(pairs)} ejemplos ({n_neg} sin contexto relevante)")


def run(cmd: list[str]):
    print("[generator] $", " ".join(cmd))
    subprocess.run(cmd, check=True)


def train(epochs: float, lr: float, max_seq: int = 2048):
    n_train = sum(1 for _ in open(SFT_DIR / "train.jsonl", encoding="utf-8"))
    iters = math.ceil(epochs * n_train / BATCH_SIZE)
    print(f"[generator] {n_train} ejemplos x {epochs} épocas = {iters} iteraciones, lr={lr}")
    run([str(BIN / "mlx_lm.lora"),
         "--model", config.GENERATOR_BASE_HF,
         "--train",
         "--data", str(SFT_DIR),
         "--adapter-path", str(ADAPTER_DIR),
         "--fine-tune-type", "lora",
         "--num-layers", "16",
         "--batch-size", str(BATCH_SIZE),
         "--grad-accumulation-steps", str(GRAD_ACCUMULATION),
         "--iters", str(iters),
         "--learning-rate", str(lr),
         "--max-seq-length", str(max_seq),
         "--mask-prompt",
         "--grad-checkpoint",
         "--steps-per-eval", "200",
         "--val-batches", "20",
         "--save-every", "200",
         "--seed", "42"])


def fuse():
    # El modelo base ya está en caché (se descargó antes de empezar el
    # entrenamiento); se fuerza modo sin conexión para no depender de internet
    os.environ["HF_HUB_OFFLINE"] = "1"
    run([str(BIN / "mlx_lm.fuse"),
         "--model", config.GENERATOR_BASE_HF,
         "--adapter-path", str(ADAPTER_DIR),
         "--save-path", str(FUSED_DIR)])


def register_ollama():
    # Las versiones recientes de Ollama ya no importan safetensors de Qwen2 ni
    # cuantizan a q8_0; se convierte antes a GGUF Q8_0 con llama.cpp
    # (LLAMA_CPP_DIR apunta a un clon de https://github.com/ggml-org/llama.cpp)
    gguf = GGUF_PATH
    llama_cpp = Path(os.getenv("LLAMA_CPP_DIR", Path.home() / "llama.cpp"))
    run([sys.executable, str(llama_cpp / "convert_hf_to_gguf.py"), str(FUSED_DIR),
         "--outtype", "q8_0", "--outfile", str(gguf)])
    modelfile = config.MODELS_DIR / ("Modelfile" if OLLAMA_NAME == config.GENERATOR_MODEL
                                     else f"Modelfile-{OLLAMA_NAME}")
    modelfile.write_text(MODELFILE.format(path=gguf), encoding="utf-8")
    run([OLLAMA_BIN, "create", OLLAMA_NAME, "-f", str(modelfile)])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["data", "train", "fuse", "ollama", "all"])
    parser.add_argument("--epochs", type=float, default=2.0)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--version", default=None, help="p. ej. v3: rutas y modelo aparte")
    parser.add_argument("--top-k", type=int, default=config.TOP_K)
    parser.add_argument("--reranker", default=None, help="clave de service.rag.RERANKERS")
    parser.add_argument("--max-seq", type=int, default=2048)
    args = parser.parse_args()
    global TOP_K
    TOP_K = args.top_k
    if args.version:
        set_version(args.version)
    if args.step in ("data", "all"):
        # Los contextos de entrenamiento se construyen con el mismo recuperador
        # que se usará en producción
        with rc.override({"reranker": args.reranker, "top_k": TOP_K}):
            build_data()
    if args.step in ("train", "all"):
        train(args.epochs, args.lr, args.max_seq)
    if args.step in ("fuse", "all"):
        fuse()
    if args.step in ("ollama", "all"):
        register_ollama()


if __name__ == "__main__":
    main()
