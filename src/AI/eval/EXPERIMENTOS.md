# Bitácora de experimentos — VialBot

Reglas (plan de la semana del 2026-09-30):
- El banco de pruebas se corrigió una sola vez y está congelado (`testbench.jsonl`,
  SHA-256 en `split.json`). Original: `testbench_v0_generado.jsonl`; cambios:
  `testbench_corrections.json` (28 correcciones aprobadas por el autor).
- `split.json`: 50 preguntas de DESARROLLO y 50 de PRUEBA, estratificadas por
  categoría, semilla 42. Todas las decisiones se toman con desarrollo; prueba se
  usa una sola vez, en la evaluación final (Fase 6).
- Métrica principal de recuperación: P@K con K = fragmentos que recibe el
  generador (hoy 4). Se reporta siempre la curva P@1–P@10 y el MRR.
- Los resultados de los experimentos se guardan en `results/exp/` y se
  registran aquí, incluidos los negativos.
- Entorno: Mac Mini M4 (24 GB). Generador `vialbot` servido por Ollama 0.34.4
  como GGUF Q8_0 (conversión con llama.cpp); juez `qwen2.5:7b`.

Comandos: `python -m eval.eval_retrieval --split dev --embedders vialbot --tag <tag> [--mode hybrid] [--reranker <clave>]`
y `python -m eval.eval_generation --split dev --conditions vialbot --tag <tag> [--top-k K] [--reranker <clave>] [--num-ctx N]`.

---

## 2026-09-30 · Verificación de la migración

Recuperador denso (código nuevo de `Retriever`) sobre el banco **sin corregir**
(n = 100): base P@1 0.29 / MRR 0.419; vialbot P@1 0.50, P@3 0.69, P@5 0.77,
MRR 0.614. Idéntico a `results/retrieval.json` (MacBook). El código nuevo no
altera el modo denso.

## 2026-09-30 · Fase 2 — Línea base en desarrollo (n = 50)

Configuración: embeddings propios, recuperación densa, K = 4, `num_ctx` 4096.
`results/exp/retrieval_p2_dense_dev.json`

| Embedder | P@1 | P@2 | P@3 | **P@4** | P@5 | P@6 | P@7 | P@8 | P@9 | P@10 | MRR |
|---|---|---|---|---|---|---|---|---|---|---|---|
| base (MiniLM) | 0.28 | 0.44 | 0.50 | **0.50** | 0.50 | 0.56 | 0.56 | 0.58 | 0.62 | 0.64 | 0.399 |
| vialbot (ajuste fino) | 0.46 | 0.68 | 0.76 | **0.76** | 0.78 | 0.80 | 0.82 | 0.82 | 0.84 | 0.84 | 0.609 |

Generación, condición C (`results/exp/generation_p2_base_dev.json`):

| Fidelidad | Relevancia | Claridad | Cita correcta | Alucinación grave | Latencia mediana |
|---|---|---|---|---|---|
| 2.70 | 3.72 | 4.14 | 50% | 48% | 1529 ms |

Nota: en el banco completo sin corregir (MacBook, safetensors) la condición C
daba fidelidad 3.07 y alucinación 37%. No es comparable directamente (otras
preguntas, otro subconjunto y el generador ahora en GGUF); la referencia para
esta semana es esta fila.

## 2026-09-30 · Fase 3 — Recuperación sin reentrenar (desarrollo, n = 50)

Todas sobre el embedder propio. Reranker sobre los 20 primeros fragmentos.
BM25 (`rank_bm25`, tokens sin tildes ni palabras vacías) fusionado con la
búsqueda densa por Reciprocal Rank Fusion (k = 60, pesos iguales).
Latencias medidas con la evaluación de generación corriendo en paralelo
(se vuelven a medir en limpio abajo).

| Configuración | P@1 | P@2 | P@3 | **P@4** | P@5 | P@6 | P@7 | P@8 | P@9 | P@10 | MRR | ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| denso (línea base) | 0.46 | 0.68 | 0.76 | **0.76** | 0.78 | 0.80 | 0.82 | 0.82 | 0.84 | 0.84 | 0.609 | 15 |
| a) híbrida (denso + BM25) | 0.40 | 0.52 | 0.60 | **0.64** | 0.74 | 0.76 | 0.80 | 0.80 | 0.82 | 0.86 | 0.532 | 15 |
| b1) reranker mmarco-mMiniLMv2 | 0.56 | 0.64 | 0.76 | **0.80** | 0.82 | 0.82 | 0.84 | 0.84 | 0.86 | 0.88 | 0.661 | 253 |
| b2) reranker bge-reranker-v2-m3 | 0.62 | 0.84 | 0.90 | **0.92** | 0.92 | 0.92 | 0.92 | 0.92 | 0.92 | 0.92 | 0.755 | 2173 |
| c1) híbrida → mmarco-mMiniLMv2 | 0.56 | 0.64 | 0.72 | **0.80** | 0.82 | 0.82 | 0.84 | 0.86 | 0.86 | 0.88 | 0.658 | 231 |
| c2) híbrida → bge-reranker-v2-m3 | 0.62 | 0.80 | 0.86 | **0.88** | 0.88 | 0.88 | 0.88 | 0.88 | 0.88 | 0.88 | 0.735 | 2172 |

Lectura:
- **Resultado negativo:** la búsqueda híbrida empeora la recuperación densa
  (P@4 0.76 → 0.64). El embedder ya está ajustado a consultas coloquiales y BM25,
  con el mismo peso en la fusión, sube fragmentos que comparten palabras pero no
  responden la pregunta. Combinada con un reranker tampoco aporta (c1 ≈ b1, c2 < b2).
- El reranker bge-reranker-v2-m3 es la mejor opción: P@4 0.76 → 0.92, P@1
  0.46 → 0.62, MRR 0.609 → 0.755. Su techo (0.92) es la cobertura de los 20
  candidatos densos: nunca puede recuperar un artículo que la búsqueda densa no
  trae entre sus 20 primeros.
- El reranker liviano llega justo a la meta (P@4 0.80) con ~10× menos latencia.

Latencia del reranker por consulta (20 pares, mediana de 9 consultas; con
Ollama ocupado en paralelo, así que es una cota superior):

| Reranker | GPU Apple (MPS) | CPU (como en el contenedor Docker) |
|---|---|---|
| mmarco-mMiniLMv2 | 235 ms | 498 ms |
| bge-reranker-v2-m3 | 1914 ms | 3388 ms |

### Efecto en la generación (desarrollo, condición C, K = 4, num_ctx 4096)

| Recuperador | Fidelidad | Relevancia | Claridad | Cita | Alucinación grave | Latencia mediana | Artículo en contexto |
|---|---|---|---|---|---|---|---|
| denso (línea base) | 2.70 | 3.72 | 4.14 | 50% | 48% | 1529 ms | 38/50 |
| reranker bge-reranker-v2-m3 | 2.72 | 3.76 | 4.04 | 54% | 46% | 3351 ms | 46/50 |
| reranker mmarco-mMiniLMv2 | 2.86 | 4.06 | 4.30 | 54% | 38% | 1729 ms | 40/50 |

Análisis pareado (mismas preguntas):
- En las 38 preguntas donde tanto el denso como bge traen el artículo correcto,
  las tres configuraciones rinden igual dentro del ruido (fidelidad 3.21 / 3.03 /
  3.05; alucinación 32% / 37% / 29%).
- En las 8 preguntas que solo bge recupera, la fidelidad sube de 1.12 a 1.88,
  pero el generador sigue fallando en 6 de 8.
- Conclusión: **el cuello de botella es el generador, no la recuperación.** Aun
  con el artículo correcto en el contexto, el modelo de 1.5B tiene fidelidad
  ≈ 3 y alucina en ≈ 30% de los casos. Con n = 50, las diferencias de
  generación entre recuperadores (±0.15 de fidelidad) están dentro del error
  estándar (≈ 0.2).

**Decisión (2026-09-30, autor):** reranker **bge-reranker-v2-m3** sobre 20
candidatos densos. Criterio: métrica principal de recuperación P@4 = 0.92 en
desarrollo, con margen sobre la meta de 0.80. En generación ningún reranker se
distingue del otro más allá del ruido. Alternativa documentada: mmarco-mMiniLMv2
(P@4 0.80, ~8× menos latencia, generación ligeramente mejor pero dentro del
ruido). La búsqueda híbrida se descarta (resultado negativo).

**Fase 4 (reentrenar embeddings): no se ejecuta.** La meta de recuperación se
alcanza sin reentrenar.

## 2026-09-30 · Fase 5 — Elección de K (desarrollo, condición C, bge-m3, num_ctx 8192)

| K | Fidelidad (±EE) | Relevancia | Claridad | Cita | Alucinación grave | Latencia mediana | Artículo en contexto | P@K recuperación (dev) |
|---|---|---|---|---|---|---|---|---|
| 4 | 2.84 (±0.22) | 3.86 | 4.16 | 56% | 44% | 3449 ms | 46/50 | 0.92 |
| 6 | 2.70 (±0.23) | 3.90 | 4.08 | 54% | 48% | 3363 ms | 46/50 | 0.92 |
| 7 | 2.82 (±0.22) | 4.02 | 4.32 | 56% | 38% | 3032 ms | 46/50 | 0.92 |

Lectura:
- Las diferencias de fidelidad entre K están dentro del error estándar; K = 7
  tiene la menor alucinación (38%) y la mejor relevancia y claridad.
- Con bge-m3 la curva de recuperación está saturada desde K = 4 (P@4 = P@7 =
  0.92): ampliar el contexto no agrega artículos correctos, solo distractores, y
  el generador (entrenado con K = 4) no se confunde más por ello.
- Subir `num_ctx` a 8192 con K = 4 no cambia el resultado (fidelidad 2.72 →
  2.84, dentro del ruido); evita recortes del prompt con K mayor.

**Decisión (regla del plan):** K = 7 no empeora la fidelidad (2.82 contra 2.84,
dentro del ruido) y reduce la alucinación, así que **K = 7**. La métrica principal
de recuperación es P@7, que en desarrollo coincide con P@4 (0.92): elegir K = 7
no infla el número reportado.

### LoRA v3 (opcional): reentrenar el generador con contextos del recuperador final

Misma receta que la iteración 2 (1 época, lr 5e-5, rango 8, 16 capas), pero los
contextos de entrenamiento se construyen con bge-m3 y K = 7 (`max-seq` 4096). Solo
se usa el dataset de entrenamiento (944 ejemplos, 104 de validación). Modelo
aparte: `vialbot-v3` (el vigente no se toca).
`python -m training.train_generator all --epochs 1 --lr 5e-5 --version v3 --top-k 7 --reranker bge-m3 --max-seq 4096`

Pérdida sobre los mismos 40 ejemplos de validación (contextos bge-m3, K = 7):

| Modelo | Pérdida de validación |
|---|---|
| Qwen2.5-1.5B base (iteración 1 de v3, LoRA sin efecto) | 1.743 |
| `vialbot` vigente (v2) | 0.668 |
| v3, iteración 200 de 472 | 0.641 |

A mitad del entrenamiento, v3 mejora apenas 4% la pérdida de v2: el generador
vigente ya se adapta a los contextos nuevos. El autor decidió dejarlo terminar
para tener el dato completo.

Pérdida final de v3 (iteración 472): **0.626** (v2: 0.668; −6%). En la
iteración 400 subió a 0.657: el entrenamiento se estabiliza cerca del final.

Generación en desarrollo (condición C, bge-m3, K = 7, num_ctx 8192;
`results/exp/generation_p5_v3_bge_k7_dev.json`), pareado con v2 en las mismas 50 preguntas:

| Métrica | v2 (vigente) | v3 | Diferencia pareada |
|---|---|---|---|
| Fidelidad | 2.82 | 3.00 | +0.18 ± 0.25 (mejor 19 / igual 19 / peor 12) |
| Relevancia | 4.02 | 4.18 | +0.16 ± 0.21 |
| Claridad | 4.32 | 4.34 | +0.02 ± 0.16 |
| Alucinación grave | 38% | 38% | igual (7 casos pasan de mal a bien y 7 al revés) |
| Cita correcta | 56% | 56% | igual |
| Latencia mediana | 3032 ms | 4071 ms | mismo tamaño de modelo y de respuesta (~24 palabras); la diferencia viene del entorno (el motor de IA de producción ya corría en la GPU durante la evaluación de v3) |

**Decisión (criterio del autor: adoptar si mejora en algo sin empeorar nada):**
se adopta **v3**. Mejora fidelidad y relevancia y no empeora ninguna métrica,
pero la mejora está dentro del error estándar. Además es coherente con la
configuración de producción (se entrenó con los mismos contextos que recibirá).
Lectura para el documento: reentrenar con los contextos del nuevo recuperador
aporta poco; el límite está en la capacidad del modelo de 1.5B.
Registro en Ollama: `vialbot` = v3 (`models/vialbot-generator-v3-q8_0.gguf`);
el anterior queda como `vialbot-v2`.

## Configuración final (congelada antes de la Fase 6)

Embeddings propios (vialbot-embedder) → búsqueda densa, 20 candidatos →
reranker bge-reranker-v2-m3 → K = 7 fragmentos → generador `vialbot` (LoRA v3,
GGUF Q8_0) con num_ctx 8192. Clasificador y filtro de seguridad sin cambios.

## 2026-09-30 05:28 · Fase 6 — Evaluación única en PRUEBA (lanzada)

Configuración congelada arriba. Se corre una sola vez sobre las 50 preguntas de prueba.

### Resultados (n = 50 preguntas de prueba; IC 95% por bootstrap; `results/exp/analysis_test.json`)

**Recuperación** (`retrieval_final_dense_test.json`, `retrieval_final_bge_test.json`):

| Configuración | P@1 | P@2 | P@3 | P@4 | P@5 | P@6 | **P@7** | P@8 | P@9 | P@10 | MRR |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Embedder base, denso | 0.32 | 0.54 | 0.56 | 0.62 | 0.64 | 0.68 | **0.68** [0.54–0.80] | 0.68 | 0.70 | 0.70 | 0.465 |
| Embedder propio, denso | 0.58 | 0.68 | 0.68 | 0.76 | 0.80 | 0.80 | **0.86** [0.76–0.94] | 0.86 | 0.86 | 0.88 | 0.669 |
| **Final: propio + bge-m3** | 0.66 | 0.74 | 0.86 | 0.86 | 0.88 | 0.92 | **0.92** [0.84–0.98] | 0.92 | 0.92 | 0.92 | 0.751 |

McNemar sobre acierto en P@7: base→propio p = 0.023 (11 preguntas ganadas, 2
perdidas); propio→propio+bge p = 0.25 (3 ganadas, 0 perdidas). **Meta de 80%
cumplida: P@7 = 92%**, igual que en desarrollo (0.92).

**Generación** (`generation_final_test.json`, `generation_baseline_test.json`):

| Condición | Fidelidad | Relevancia | Claridad | Cita correcta | Alucinación grave | Latencia mediana |
|---|---|---|---|---|---|---|
| A. LLM base sin RAG | 2.18 [1.90–2.46] | 3.86 | 4.06 | 0% | 46% | 3751 ms |
| B. LLM base + RAG (recuperador final) | 2.48 [2.02–2.96] | 3.48 | 4.60 | 16% | 56% | 4273 ms |
| C0. vialbot v2, denso, K = 4 (línea base) | 3.04 [2.60–3.48] | 3.92 | 4.32 | 50% | 36% | 1515 ms |
| **C. Final: vialbot v3 + bge-m3, K = 7** | 3.04 [2.58–3.50] | 3.98 | 4.18 | 58% | 42% | 4142 ms |

Pruebas pareadas (Wilcoxon para escalas 1–5, McNemar exacta para tasas):
- A→C: fidelidad +0.86 (p = 0.004); cita 0% → 58% (p < 0.001); alucinación 46% → 42% (p = 0.83).
- B→C: fidelidad +0.56 (p = 0.086); relevancia +0.50 (p = 0.056); claridad −0.42
  (p = 0.011, B mejor); cita 16% → 58% (p < 0.001); alucinación 56% → 42% (p = 0.25).
- C0→C: sin diferencias significativas en ninguna métrica (fidelidad igual,
  cita +8 pp p = 0.42, alucinación +6 pp p = 0.58); la latencia se triplica
  (1.5 s → 4.1 s) por el reranker y el contexto más largo.

**Lectura honesta:** la mejora de recuperación se confirma en prueba (P@7
86% → 92%, P@1 58% → 66%), pero **no se traduce en mejor generación**: la
configuración final rinde igual que la línea base en fidelidad, con más cita
correcta y algo más de alucinación (ambas diferencias dentro del ruido). Esto
confirma en el conjunto de prueba el diagnóstico hecho en desarrollo: el límite
es el generador de 1.5B.

**Taxonomía de errores de C** (50 respuestas): 20 correctas (fidelidad ≥ 4),
9 parciales (3), 4 fallos de recuperación (el artículo no llegó al contexto) y
**17 alucinaciones con el artículo correcto en el contexto**. De 21 fallos
graves, 17 son del generador y 4 del recuperador.

**Pruebas de límites** (`boundary_final_test.json`; 34 ataques y, como
control, las 50 preguntas de prueba):

| Métrica | Iteración 2 (MacBook, documento anterior) | Final |
|---|---|---|
| Rechazo adversarial | 100% | 100% |
| Rechazo fuera de dominio | 84.6% | **73.1%** |
| Falsos rechazos | 12.5% (40 controles) | **4.0%** (50 controles) |
| Bloqueados por el LLM | 3 | 0 |

**Hallazgo (regresión no prevista):** v3 dejó de negarse por sí mismo ante
preguntas fuera de dominio que pasan el clasificador (7 de 26; por ejemplo,
responde sobre el IVA o el Código Penal inventando una cita). El criterio de
adopción de v3 en desarrollo solo miró las métricas de generación, no las
pruebas de límites. La contracara es que casi no rechaza preguntas legítimas
(falsos rechazos 12.5% → 4%). No se cambia nada después de ver estos
resultados (el conjunto de prueba ya se usó); se documenta como limitación, y el
umbral del clasificador (`in_domain_threshold`, ajustable en caliente) queda
como la palanca de corrección, a calibrar con un conjunto de ataques nuevo.

## 2026-09-30 · Producción: latencia por etapa y prueba de carga

Servicio de producción (motor de IA en el anfitrión con GPU, configuración
final), preguntas de desarrollo (`results/exp/bench.json`).

**Falla encontrada y corregida:** con 2 consultas simultáneas el motor de IA se
caía (PyTorch sobre MPS no admite llamadas concurrentes desde varios hilos del
servidor). Se serializaron el embedder y el reranker con un candado
(`Retriever._torch_lock`); la generación en Ollama sigue en paralelo. El servicio
tiene además `KeepAlive` en launchd.

Latencia con un usuario (n = 50, mediana / p95): clasificación 23 / 46 ms;
búsqueda + reranker 1860 / 1986 ms; generación 933 / 1559 ms; **total 2812 / 3396 ms**.

| Usuarios simultáneos | Throughput | Latencia mediana | p95 |
|---|---|---|---|
| 1 | 20.4 consultas/min | 2.9 s | 3.8 s |
| 2 | 24.8 consultas/min | 4.9 s | 6.9 s |
| 4 | 25.2 consultas/min | 8.8 s | 14.0 s |
| 8 | 25.8 consultas/min | 17.6 s | 30.2 s |

El sistema se satura en ~25 consultas/min (~1 500/hora): el cuello de botella
es el reranker (~1.9 s por consulta, serializado). Memoria: generador `vialbot`
2.7 GB en Ollama (con num_ctx 8192) y motor de IA (embedder, reranker y
clasificador) ~5.2 GB de huella física (incluye memoria de GPU unificada);
en total ~8 GB de los 24 GB de la Mac Mini.

## 2026-09-30 · Ajuste posterior a la evaluación: umbral del clasificador de dominio

Motivo: en la Fase 6 el rechazo fuera de dominio bajó a 73.1% porque el
generador v3 ya no se niega por sí mismo. El ajuste se hace **después** de la
evaluación final y se reporta como tal: los resultados de la Fase 6 no cambian.

Conjunto de calibración nuevo (`eval/calibration_domain.jsonl`), redactado a
mano para este fin, sin reutilizar preguntas de `boundary_cases.jsonl` ni del
banco: consultas fuera de dominio (otras leyes, trámites, vida cotidiana y
temas cercanos a los vehículos que no son de tránsito) y consultas legítimas de
tránsito de control.

**Criterio fijado antes de medir:** entre los umbrales 0.50 a 0.95 (paso 0.05),
elegir el que maximiza el rechazo fuera de dominio con falsos rechazos ≤ 5% en
los controles de calibración; en empate, el umbral más bajo.

Resultado (`results/exp/calibration_threshold.json`; 50 fuera de dominio, 50 controles):

| Umbral | 0.50 | 0.55 | **0.60** | 0.65 | 0.70 | 0.80 | 0.90 |
|---|---|---|---|---|---|---|---|
| Rechazo fuera de dominio | 54% | 58% | **60%** | 62% | 68% | 70% | 80% |
| Falsos rechazos | 4% | 4% | **4%** | 6% | 10% | 14% | 24% |

**Decisión (criterio fijado):** umbral **0.60**, aplicado solo en producción
(`PUT /settings`); el repositorio conserva 0.50, que es con lo que se midió la
Fase 6. La mejora es modesta (+6 pp) porque el problema no es el umbral: de las
20 consultas fuera de dominio que siguen pasando, 14 son de mecánica o compra
de vehículos, con probabilidad "en dominio" de 0.87 a 0.98. El clasificador
aprendió "habla de vehículos" en lugar de "habla de normativa de tránsito". El resto
son otras ramas del derecho (penal, constitucional, IGSS, visas). Corrección de
fondo (recomendación): reentrenar el clasificador con negativos de mecánica,
compra y mantenimiento de vehículos y de otras leyes, y medirlo con este mismo
conjunto de calibración, que no debe usarse para entrenar.

## 2026-09-30 · Confiabilidad según la cita (análisis sobre la corrida final de prueba)

Mismas 50 respuestas de C (`generation_final_test.json`); IC 95% de Wilson.
Correcta (fidelidad 4–5): 20/50 = 40% (28–54%). Correcta o casi (3–5): 29/50 = 58% (44–71%).
Si cita el artículo que corresponde (29): correcta 69% (51–83%), correcta o casi 86% (69–95%).
Si cita otro o ninguno (21): correcta 0% (0–15%), correcta o casi 19% (8–40%).
Lectura: la cita es un buen indicador de confianza; el sistema es una herramienta
de orientación verificable (muestra el artículo), no un sustituto de la ley.

## 2026-10-28 · Exploratorio: generador de 4B sin ajuste fino (desarrollo)

Qwen3-4B-Instruct (`qwen3:4b-instruct`, Apache 2.0) sin ajuste fino, con el
recuperador final (bge-m3, K = 7, num_ctx 8192), condición C, 50 preguntas de
desarrollo (`generation_p9_qwen3_4b_instruct_sin_ajuste_dev.json`). Un primer
intento con `qwen3:4b` (modo razonamiento) se descartó: escribía su razonamiento
en la respuesta y tardaba ~24 s.

| | vialbot (1.5B, LoRA v3) | Qwen3-4B sin ajuste | Pareado |
|---|---|---|---|
| Fidelidad | 3.00 | **4.08** | Wilcoxon p = 0.0001 |
| Correctas (fidelidad ≥ 4) | 20/50 | **36/50** | |
| Alucinación grave | 38% | **10%** | McNemar p = 0.0001 |
| Cita correcta | 56% | 72% | |
| Relevancia / claridad | 4.18 / 4.34 | 4.70 / 4.64 | |
| Latencia mediana | 4.1 s | 11.4 s | |
| Palabras por respuesta (mediana) | 25 | 109 | |

Lectura: confirma el diagnóstico del análisis de errores (el límite es la
capacidad del generador). Cautelas: medido solo en desarrollo; el juez
(Qwen2.5) es de la familia Qwen; respuestas ~4 veces más largas. No se adopta:
cambiar el generador exigiría repetir la evaluación final. Queda como evidencia
para la recomendación principal.
