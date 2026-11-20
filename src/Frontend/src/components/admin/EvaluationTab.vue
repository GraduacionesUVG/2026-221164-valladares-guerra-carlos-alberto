<template>
  <div class="view-panel">
    <div class="page-title">
      <h1>Evaluación del Modelo</h1>
      <p>Resultados del banco de pruebas (examen crítico). Se generan con los scripts de <code>AI/eval</code>.</p>
    </div>

    <div v-if="error" class="settings-card text-amber">{{ error }}</div>
    <div v-else-if="loaded && !hasAny" class="settings-card text-dim">
      Aún no hay resultados. Ejecuta <code>python -m eval.eval_retrieval</code>, <code>eval_generation</code> y <code>eval_boundary</code> en la carpeta AI.
    </div>

    <template v-else>
      <!-- Recuperación -->
      <div v-if="m.retrieval" class="settings-card mb-6">
        <h3><Gauge :size="20"/> Recuperación (banco de {{ firstRetrieval.n }} consultas)</h3>
        <table class="data-table">
          <thead><tr><th>Configuración de recuperación</th><th>Precision@1</th><th>Precision@4</th><th>Precision@7 (K)</th><th>MRR</th></tr></thead>
          <tbody>
            <tr v-for="(r, name) in retrievalRows" :key="name">
              <td><b>{{ RETRIEVERS[name] || name }}</b></td>
              <td>{{ pct(r['precision@1']) }}</td>
              <td>{{ pct(r['precision@4']) }}</td>
              <td><b>{{ pct(r['precision@7']) }}</b></td>
              <td>{{ r.mrr.toFixed(3) }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Generación -->
      <div v-if="m.generation" class="settings-card mb-6">
        <h3><FlaskConical :size="20"/> Generación — LLM-as-a-Judge ({{ m.generation.n }} consultas, juez: {{ m.generation.judge }})</h3>
        <table class="data-table">
          <thead><tr><th>Condición</th><th>Fidelidad (1-5)</th><th>Relevancia (1-5)</th><th>Claridad (1-5)</th><th>Cita correcta</th><th>Alucinación grave</th><th>Latencia mediana</th></tr></thead>
          <tbody>
            <tr v-for="(g, name) in m.generation.summary" :key="name">
              <td><b>{{ CONDITIONS[name] || name }}</b></td>
              <td>{{ g.fidelidad.toFixed(2) }}</td>
              <td>{{ g.relevancia.toFixed(2) }}</td>
              <td>{{ g.claridad.toFixed(2) }}</td>
              <td>{{ pct(g.cita_correcta) }}</td>
              <td>{{ pct(g.alucinacion_grave) }}</td>
              <td>{{ (g.latencia_ms_mediana / 1000).toFixed(1) }} s</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="settings-grid">
        <!-- Pruebas de límites -->
        <div v-if="m.boundary" class="settings-card">
          <h3><ShieldCheck :size="20"/> Pruebas de Límites</h3>
          <div class="config-row"><span>Rechazo de consultas fuera de dominio</span><b>{{ pct(m.boundary.rejection_rate_out_of_domain) }}</b></div>
          <div class="config-row"><span>Rechazo de consultas maliciosas</span><b>{{ pct(m.boundary.rejection_rate_adversarial) }}</b></div>
          <div class="config-row"><span>Falsos rechazos (consultas válidas)</span><b>{{ pct(m.boundary.false_rejection_rate) }}</b></div>
          <div class="config-row"><span>Bloqueadas por clasificador / búsqueda / LLM</span>
            <b>{{ m.boundary.blocked_by_classifier }} / {{ m.boundary.blocked_by_retrieval }} / {{ m.boundary.blocked_by_llm }}</b></div>
        </div>

        <!-- Clasificador -->
        <div v-if="m.classifier" class="settings-card">
          <h3><Brain :size="20"/> Clasificador de Temas</h3>
          <div class="config-row"><span>Exactitud (20% de prueba)</span><b>{{ pct(m.classifier.test_accuracy) }}</b></div>
          <div class="config-row"><span>F1 macro</span><b>{{ m.classifier.macro_f1.toFixed(3) }}</b></div>
          <div class="config-row"><span>Detección fuera de dominio (recall)</span><b>{{ pct(m.classifier.domain_filter.ood_recall) }}</b></div>
          <div class="config-row"><span>Ejemplos de entrenamiento</span><b>{{ m.classifier.examples }}</b></div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { Gauge, FlaskConical, ShieldCheck, Brain } from '@lucide/vue';
import api from '../../services/api';

const CONDITIONS = {
  llm_sin_rag: 'LLM base sin RAG',
  llm_base_rag: 'LLM base + RAG',
  vialbot: 'VialBot (modelo propio + RAG)',
  vialbot_linea_base: 'VialBot línea base (v2, sin reranker, K = 4)',
};

const RETRIEVERS = {
  base: 'Embeddings base, búsqueda densa',
  vialbot: 'Embeddings propios, búsqueda densa',
  vialbot_reranker: 'Embeddings propios + reranker (final)',
};

const m = ref({});
const loaded = ref(false);
const error = ref('');

const hasAny = computed(() => Object.keys(m.value).length > 0);
// Solo las entradas con métricas (el JSON también trae "split" y "config")
const retrievalRows = computed(() => Object.fromEntries(
  Object.entries(m.value.retrieval || {}).filter(([, r]) => r && typeof r === 'object' && 'mrr' in r)));
const firstRetrieval = computed(() => Object.values(retrievalRows.value)[0] || {});
const pct = (v) => (v == null ? '–' : `${(v * 100).toFixed(1)}%`);

onMounted(async () => {
  try {
    m.value = (await api.get('/rag/metrics')).data;
  } catch (e) {
    error.value = 'No se pudo conectar con el motor de IA.';
  } finally {
    loaded.value = true;
  }
});
</script>

<style scoped>
.config-row { display: flex; justify-content: space-between; gap: 16px; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.9rem; }
.config-row span { color: var(--txt-dim); }
.config-row b { color: #fff; }
.mb-6 { margin-bottom: 24px; }
code { font-family: 'Space Mono', monospace; color: var(--amber); }
.data-table { width: 100%; }
</style>
