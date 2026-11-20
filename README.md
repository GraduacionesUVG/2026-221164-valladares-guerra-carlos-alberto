# VialBot — Asistente Conversacional de Tránsito y Educación Vial en Guatemala

**Trabajo de graduación:** *Desarrollo de un Asistente Conversacional Inteligente para la Gestión de Consultas de Tránsito y Educación Vial en Guatemala mediante Procesamiento de Lenguaje Natural*

Universidad del Valle de Guatemala — Facultad de Ingeniería — Ingeniería en Ciencias de la Computación y Tecnologías de la Información

**Demo en línea:** https://vialbot.vallague.com

## Descripción

En Guatemala la **Ley de Tránsito (Decreto 132-96)** y su **Reglamento (Acuerdo Gubernativo 273-98)** son documentos extensos y técnicos, y la ciudadanía tiene dificultades para encontrar respuestas puntuales: multas, documentos obligatorios, licencias o qué hacer ante un accidente. **VialBot** es un asistente conversacional que responde esas consultas en lenguaje natural y **cita el artículo de la ley** en el que se basa cada respuesta.

El sistema usa una arquitectura **RAG (Retrieval-Augmented Generation)** con **modelos propios entrenados localmente**, sin APIs comerciales:

1. **Filtro de seguridad y clasificador propio:** identifica el tema de la consulta y rechaza preguntas fuera de dominio o intentos de manipulación.
2. **Embeddings propios:** un modelo multilingüe con fine-tuning contrastivo busca los fragmentos de la ley más relevantes en **ChromaDB** (277 fragmentos / 247 artículos), con re-ranking `bge-m3`.
3. **LLM propio:** `Qwen2.5-1.5B-Instruct` con fine-tuning **LoRA** (MLX), servido con Ollama como el modelo `vialbot`. Redacta la respuesta usando solo el contexto recuperado.

Funcionalidades:

- Registro e inicio de sesión de ciudadanos (JWT).
- Chat con historial de conversaciones por usuario y citas a los artículos.
- Panel de administración con métricas reales, logs de consultas, base documental, configuración del RAG en caliente, gestión de usuarios, estado del sistema, *playground* y resultados de la evaluación del modelo.

```text
Navegador (Vue 3) ──► API Gateway (PHP 8) ──► MySQL          usuarios, conversaciones, métricas
                                    │
                                    └──────► Motor de IA (Python / FastAPI)
                                               ├─ Clasificador propio   tema + filtro de dominio
                                               ├─ Embeddings propios    búsqueda por similitud coseno
                                               ├─ ChromaDB              base vectorial
                                               └─ LLM propio (Ollama)   Qwen2.5-1.5B + LoRA "vialbot"
```

## Tecnologías Utilizadas

- **Frontend:** Vue 3, Vite, Pinia, Vue Router, Tailwind CSS, Axios
- **Backend:** PHP 8.2 (API REST con JWT; capas Controller/Service/Repository), Apache
- **Base de datos:** MySQL 8
- **Motor de IA:** Python 3.12, FastAPI, Sentence-Transformers, ChromaDB, scikit-learn, PyTorch, rank-bm25
- **Entrenamiento:** MLX / mlx-lm (LoRA en Apple Silicon), Hugging Face Datasets
- **LLM:** Ollama + Qwen2.5-1.5B-Instruct (LoRA propio, cuantizado GGUF Q8_0)
- **Infraestructura:** Docker / Docker Compose, Cloudflare Tunnel

## Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| [`src/Frontend/`](src/Frontend/) | Vue 3: landing, chat y panel de administración |
| [`src/Backend/`](src/Backend/) | API REST en PHP |
| [`src/AI/`](src/AI/) | Motor RAG: ingesta, entrenamiento, evaluación y servicio FastAPI ([README](src/AI/README.md)) |
| [`src/Database/`](src/Database/) | `schema.sql`, datos iniciales y migraciones |
| [`src/tests/`](src/tests/) | Prueba de extremo a extremo de la API |
| [`src/deploy/`](src/deploy/) | Scripts de despliegue en producción |

## Requisitos Previos

- [Docker](https://www.docker.com/) y Docker Compose
- [Ollama](https://ollama.com) en la máquina anfitriona
- Git
- Para reentrenar los modelos (opcional): Mac con Apple Silicon, Python 3.12 y [uv](https://docs.astral.sh/uv/)
- Para desarrollar el frontend sin Docker (opcional): Node.js 22+

## Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/vgcarlol/2026-221164-valladares-guerra-carlos-alberto.git
   cd 2026-221164-valladares-guerra-carlos-alberto/src
   ```

2. Configurar las variables de entorno:
   ```bash
   cp .env.example .env
   # Editar .env con las configuraciones correspondientes
   ```

3. Obtener los modelos entrenados. Pesan varios GB y superan el límite de GitHub, por eso no están en el repositorio. Hay dos opciones:

   **a) Descargar los modelos ya entrenados** desde Hugging Face: https://huggingface.co/vgcarlol/vialbot

   ```bash
   # Embeddings, clasificador y base vectorial en src/AI
   hf download vgcarlol/vialbot --local-dir AI/models-descarga
   mv AI/models-descarga/models AI/models
   mv AI/models-descarga/chroma AI/data/chroma

   # Registrar el LLM propio en Ollama
   cd AI/models && ollama create vialbot -f Modelfile && cd ../..
   ```

   **b) Entrenarlos desde cero** con los scripts de `src/AI/training` (ver [src/AI/README.md](src/AI/README.md#reproducir-todo-desde-cero-mac-con-apple-silicon)).

4. Levantar los servicios:
   ```bash
   docker compose up -d --build
   ```

5. Abrir la aplicación:

   | Servicio | URL |
   |---|---|
   | Frontend | http://localhost:5173 |
   | Backend API | http://localhost:8080/api/v1 |
   | Motor de IA | http://localhost:8000/health |

   Usuarios de desarrollo: `admin@example.com` / `password` (administrador) y `user@example.com` / `password` (ciudadano). También es posible registrarse desde `/auth/signup`.

6. (Opcional) Ejecutar la prueba de extremo a extremo:
   ```bash
   ./tests/e2e_api.sh
   ```

## Resultados principales

Los resultados completos de la evaluación (recuperación, generación con *LLM-as-a-Judge*, clasificador y pruebas de límites) están en el capítulo de Resultados del [informe final](docs/informe_final.pdf). Los archivos JSON de cada experimento están en [`src/AI/eval/results/`](src/AI/eval/results/) y se pueden consultar en el panel de administración.

## Capturas

Las capturas de pantalla del sistema se encuentran en [`/capturas`](capturas/):

| # | Pantalla |
|---|---|
| 01 | [Página de inicio](capturas/captura-01.png) |
| 02 | [Página de inicio: ¿Cómo funciona?](capturas/captura-02.png) |
| 03 | [Registro de usuario](capturas/captura-03.png) |
| 04 | [Inicio de sesión](capturas/captura-04.png) |
| 05 | [Chat: nueva conversación con sugerencias](capturas/captura-05.png) |
| 06 | [Chat: respuesta sobre multas con cita del artículo](capturas/captura-06.png) |
| 07 | [Chat: respuesta sobre documentos obligatorios](capturas/captura-07.png) |
| 08 | [Chat: rechazo de una pregunta fuera de dominio](capturas/captura-08.png) |
| 09 | [Admin: Overview con métricas](capturas/captura-09.png) |
| 10 | [Admin: logs de consultas](capturas/captura-10.png) |
| 11 | [Admin: base documental](capturas/captura-11.png) |
| 12 | [Admin: configuración del RAG](capturas/captura-12.png) |
| 13 | [Admin: usuarios y roles](capturas/captura-13.png) |
| 14 | [Admin: estado del sistema](capturas/captura-14.png) |
| 15 | [Admin: evaluación del modelo](capturas/captura-15.png) |
| 16 | [Admin: playground RAG](capturas/captura-16.png) |

## Demo

El video demostrativo se encuentra en [`/demo/demo.mp4`](demo/demo.mp4)

## Documentación

El informe final del proyecto está disponible en [`/docs/informe_final.pdf`](docs/informe_final.pdf)

El consentimiento de uso de foto y video firmado se encuentra en [`/docs/consentimiento_firmado.pdf`](docs/consentimiento_firmado.pdf)

## Autores

- Carlos Alberto Valladares Guerra — 221164

**Asesor:** Ing. Juan Luis García Zarceño

## Licencia

MIT. Los modelos base conservan sus licencias originales (Qwen2.5: Apache 2.0). Los textos legales del corpus son documentos públicos del Estado de Guatemala.
