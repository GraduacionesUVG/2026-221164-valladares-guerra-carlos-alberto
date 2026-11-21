# VialBot — Asistente Conversacional de Tránsito (Prototipo Full-Stack)

Asistente que responde consultas ciudadanas sobre la **Ley de Tránsito (Decreto 132-96)** y su
**Reglamento (Acuerdo Gubernativo 273-98)** mediante una arquitectura **RAG** con **modelos propios**
entrenados localmente (sin APIs comerciales).

## 1. Arquitectura

```text
Navegador (Vue 3) ──► API Gateway (PHP 8) ──► MySQL          usuarios, conversaciones, métricas
                                    │
                                    └──────► Motor de IA (Python / FastAPI)
                                               ├─ Clasificador propio   tema + filtro de dominio
                                               ├─ Embeddings propios    búsqueda por similitud coseno
                                               ├─ ChromaDB              277 fragmentos / 247 artículos
                                               └─ LLM propio (Ollama)   Qwen2.5-1.5B + LoRA "vialbot"
```

| Carpeta | Contenido |
|---|---|
| `Frontend/` | Vue 3 + Vite: landing, chat con historial por usuario, panel de administración |
| `Backend/` | API REST en PHP (router por atributos, JWT, capas Controller/Service/Repository) |
| `AI/` | Motor RAG: ingesta, entrenamiento de modelos, evaluación y servicio FastAPI — ver [AI/README.md](AI/README.md) |
| `Database/` | `schema.sql`, datos iniciales y `migrations/` para bases existentes |
| `tests/` | Prueba de extremo a extremo de la API (`e2e_api.sh`) |

## 2. Inicio rápido (Docker)

Requisitos: Docker y [Ollama](https://ollama.com) en la máquina anfitriona con el modelo `vialbot`
registrado (ver `AI/README.md`). Los modelos entrenados (`AI/models/`) y la base vectorial
(`AI/data/chroma/`) no se versionan: se generan con los scripts de `AI/`.

```bash
cd Prototipo
docker compose up -d --build
```

| Servicio | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8080/api/v1 |
| Motor de IA | http://localhost:8000/health |
| MySQL | localhost:3306 |

Usuarios de desarrollo: `admin@example.com` / `password` (administrador) y
`user@example.com` / `password` (ciudadano). Cualquier persona puede registrarse desde `/auth/signup`.

Prueba de extremo a extremo (con los servicios arriba):

```bash
./tests/e2e_api.sh
```

## 3. API principal

| Método | Ruta | Rol | Descripción |
|---|---|---|---|
| POST | `/auth/register` | público | Registro de ciudadanos |
| POST | `/auth/login` | público | Devuelve un JWT (expira en 8 h) |
| GET/POST | `/chat/conversations` | usuario | Listar / crear conversaciones propias |
| DELETE | `/chat/conversations/{id}` | usuario | Eliminar una conversación propia |
| GET/POST | `/chat/conversations/{id}/messages` | usuario | Historial / enviar consulta al asistente |
| GET | `/dashboard/stats` | admin | Métricas reales: temas, latencia, artículos más citados |
| GET | `/logs` | admin | Consultas con tema, fuentes y estado |
| GET | `/system/health`, `/system/logs` | admin | Estado medido de cada componente |
| GET | `/documents`, `/rag/config`, `/rag/metrics` | admin | Corpus indexado, configuración y evaluación |
| POST | `/rag/playground` | admin | Consulta de prueba con el contexto recuperado |

## 4. Despliegue en el servidor (antes de hacer push a `main`)

El workflow `.github/workflows/deploy.yml` publica el frontend y el backend en cada push a `main`.
Esta versión **requiere preparar el servidor antes**, o el backend dejará de funcionar:

1. **Respaldar la base de datos** y aplicar `Database/migrations/001_rag_conversations.sql`.
2. Crear `Backend/config/local.php` en el servidor a partir de `config/local.example.php`
   (como mínimo `JWT_SECRET`, credenciales de MySQL, `AI_SERVICE_URL` y `AI_SERVICE_TOKEN`).
   Sin `JWT_SECRET` el login responde error 500 fuera del entorno local.
3. Levantar el motor de IA (`AI/`) y Ollama en una máquina accesible **solo** desde el backend;
   no debe exponerse a internet. Si no está disponible, el chat responde con un mensaje de
   servicio no disponible en lugar de inventar respuestas.
