<template>
  <div class="view-panel">
    <div class="page-title flex-between">
      <div>
        <h1>Configuración del Modelo RAG</h1>
        <p>Estos parámetros se aplican al instante, sin reiniciar el motor de IA. La arquitectura fija (modelos, segmentación) se muestra abajo como referencia.</p>
      </div>
      <div class="header-actions">
        <button class="btn-outline" :disabled="saving" @click="restoreDefaults">Restaurar valores por defecto</button>
        <button class="btn-primary" :disabled="saving || !dirty" @click="save">
          <Save :size="16"/> {{ saving ? 'Guardando...' : 'Guardar Cambios' }}
        </button>
      </div>
    </div>

    <div v-if="error" class="settings-card text-amber">{{ error }}</div>
    <div v-if="saveError" class="settings-card text-amber">{{ saveError }}</div>
    <div v-else-if="loaded" class="settings-grid">
      <div class="settings-card">
        <h3><Settings :size="20"/> Parámetros de Generación</h3>

        <div class="form-group">
          <label>
            <span>Preferir modelo propio (VialBot) sobre el base</span>
          </label>
          <select class="form-control" v-model="prefer">
            <option :value="true">VialBot (entrenado con datos propios)</option>
            <option :value="false">Modelo base sin ajustar</option>
          </select>
          <small class="help-text">Si el modelo elegido no está cargado en Ollama, el sistema usa automáticamente el otro.</small>
        </div>

        <div class="form-group">
          <label><span>Temperatura</span> <span>{{ form.temperature.toFixed(2) }}</span></label>
          <input type="range" min="0" max="1" step="0.05" v-model.number="form.temperature" class="form-control-range">
          <small class="help-text">Valores bajos hacen respuestas más precisas y consistentes (recomendado para un asistente legal).</small>
        </div>

        <div class="form-group">
          <label class="flex-between">
            <span>Prompt Maestro (System Prompt)</span>
            <a href="#" class="text-sky text-sm" @click.prevent="restorePrompt">usar el de fábrica</a>
          </label>
          <textarea class="form-control" rows="10" v-model="form.system_prompt"></textarea>
          <small class="help-text">Se entrega al modelo antes de cada consulta. Cambiarlo no reentrena al modelo propio, solo afecta cómo se le instruye en producción.</small>
        </div>
      </div>

      <div class="settings-card">
        <h3><Database :size="20"/> Búsqueda Vectorial (Retrieval)</h3>

        <div class="form-group">
          <label><span>Top K (fragmentos inyectados)</span> <span>{{ form.top_k }}</span></label>
          <input type="range" min="1" max="10" step="1" v-model.number="form.top_k" class="form-control-range">
        </div>

        <div class="form-group">
          <label><span>Umbral de Similitud mínima</span> <span>{{ form.min_retrieval_score.toFixed(2) }}</span></label>
          <input type="range" min="0" max="1" step="0.05" v-model.number="form.min_retrieval_score" class="form-control-range">
          <small class="help-text">Si la similitud del mejor fragmento es menor a este valor, el bot responde que no encontró información en lugar de alucinar.</small>
        </div>

        <div class="form-group">
          <label><span>Umbral del filtro de dominio</span> <span>{{ form.in_domain_threshold.toFixed(2) }}</span></label>
          <input type="range" min="0" max="1" step="0.05" v-model.number="form.in_domain_threshold" class="form-control-range" :disabled="!cfg.classifier_ready">
          <small class="help-text">
            {{ cfg.classifier_ready ? 'Probabilidad mínima de que la consulta sea sobre tránsito para no rechazarla.' : 'El clasificador aún no está entrenado; este umbral no tiene efecto.' }}
          </small>
        </div>

        <div class="config-row"><span>Base vectorial</span><b>{{ cfg.vectordb }}</b></div>
        <div class="config-row"><span>Métrica de similitud</span><b>Coseno</b></div>
        <div class="config-row">
          <span>Modelo de embeddings</span>
          <b>{{ shortName(cfg.embedder) }} <span :class="['badge', cfg.embedder_finetuned ? 'green' : 'gray']">{{ cfg.embedder_finetuned ? 'propio' : 'base' }}</span></b>
        </div>
        <div class="config-row"><span>Segmentación (fija)</span><b>Por artículo, {{ cfg.chunk_max_chars }} / {{ cfg.chunk_overlap_chars }} caracteres</b></div>
        <small class="help-text">Cambiar el modelo de embeddings o el tamaño de segmentación exige reindexar el corpus completo; se hace desde <code>AI/pipeline</code>, no desde este panel.</small>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { Settings, Database, Save } from '@lucide/vue';
import api from '../../services/api';

const cfg = ref({});
const original = ref(null);
const form = ref({
  top_k: 4, min_retrieval_score: 0.25, in_domain_threshold: 0.5,
  temperature: 0.1, system_prompt: '',
});
const prefer = ref(true);
const defaultPrompt = ref('');
const loaded = ref(false);
const error = ref('');
const saving = ref(false);
const saveError = ref('');

const shortName = (path) => (path ? path.split('/').pop() : '...');

const dirty = computed(() => {
  if (!original.value) return false;
  return JSON.stringify({ ...form.value, prefer_finetuned_generator: prefer.value })
      !== JSON.stringify(original.value);
});

const applySettings = (current) => {
  form.value = {
    top_k: current.top_k,
    min_retrieval_score: current.min_retrieval_score,
    in_domain_threshold: current.in_domain_threshold,
    temperature: current.temperature,
    system_prompt: current.system_prompt ?? defaultPrompt.value,
  };
  prefer.value = current.prefer_finetuned_generator;
  original.value = { ...form.value, prefer_finetuned_generator: prefer.value };
};

const restorePrompt = () => { form.value.system_prompt = defaultPrompt.value; };

const load = async () => {
  const [configRes, settingsRes] = await Promise.all([
    api.get('/rag/config'),
    api.get('/rag/settings'),
  ]);
  cfg.value = configRes.data;
  defaultPrompt.value = settingsRes.data.default_system_prompt;
  applySettings(settingsRes.data.current);
};

const save = async () => {
  saving.value = true;
  saveError.value = '';
  try {
    const payload = { ...form.value, prefer_finetuned_generator: prefer.value };
    // No enviar el prompt si es idéntico al de fábrica: así el backend lo
    // trata como "usar el valor por defecto" (queda null en el motor).
    if (payload.system_prompt === defaultPrompt.value) payload.system_prompt = null;
    const { data } = await api.put('/rag/settings', payload);
    applySettings(data.current);
  } catch (e) {
    saveError.value = e.response?.data?.error || 'No se pudo guardar la configuración.';
  } finally {
    saving.value = false;
  }
};

const restoreDefaults = async () => {
  saving.value = true;
  saveError.value = '';
  try {
    const { data } = await api.put('/rag/settings', { reset: true });
    applySettings(data.current);
  } catch (e) {
    saveError.value = 'No se pudo restaurar la configuración.';
  } finally {
    saving.value = false;
  }
};

onMounted(async () => {
  try {
    await load();
  } catch (e) {
    error.value = 'No se pudo conectar con el motor de IA.';
  } finally {
    loaded.value = true;
  }
});
</script>

<style scoped>
.config-row { display: flex; justify-content: space-between; align-items: center; gap: 16px; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.9rem; }
.config-row span { color: var(--txt-dim); }
.config-row b { color: #fff; text-align: right; display: flex; align-items: center; gap: 8px; }
code { font-family: 'Space Mono', monospace; color: var(--amber); }
.header-actions { display: flex; gap: 12px; }
</style>
