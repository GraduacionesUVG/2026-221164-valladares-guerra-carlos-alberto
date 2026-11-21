FROM python:3.12-slim

WORKDIR /app

# PyTorch solo CPU: el contenedor hace embeddings y clasificación; el LLM se
# sirve con Ollama (en el host o en su propio contenedor).
COPY requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

COPY config.py .
COPY pipeline ./pipeline
COPY service ./service
COPY data/raw ./data/raw
COPY data/processed ./data/processed

# Los modelos entrenados y la base vectorial se montan como volúmenes
# (models/ y data/chroma/), generados con los scripts de training/ y pipeline/.
ENV TOKENIZERS_PARALLELISM=false

EXPOSE 8000
CMD ["uvicorn", "service.app:app", "--host", "0.0.0.0", "--port", "8000"]
