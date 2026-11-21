<template>
  <div class="view-panel">
    <div class="page-title">
      <h1>Playground RAG</h1>
      <p>Prueba el motor completo y audita el contexto recuperado. Estas consultas no se guardan en el historial.</p>
    </div>

    <div class="playground-grid">
      <!-- Chat Simulator -->
      <div class="play-chat">
        <div class="play-header">
          <h4>Simulador de Chat</h4>
          <span class="badge green">{{ lastModel || 'VialBot' }}</span>
        </div>
        <div class="play-messages">
          <div v-if="!turns.length" class="text-dim text-sm">Escribe una consulta para ver la respuesta y los fragmentos usados.</div>
          <template v-for="(t, i) in turns" :key="i">
            <div class="play-msg user">{{ t.question }}</div>
            <div class="play-msg bot">
              <span class="msg-text">{{ t.answer }}</span>
              <div class="play-meta">
                <span v-if="t.topic">Tema: {{ t.topic.replaceAll('_', ' ') }}</span>
                <span v-if="t.refused">Rechazada: {{ t.refused }}</span>
                <span>{{ (t.latency / 1000).toFixed(1) }} s</span>
              </div>
            </div>
          </template>
          <div v-if="loading" class="play-msg bot text-dim">Generando respuesta...</div>
        </div>
        <div class="play-input">
          <input v-model="question" type="text" class="form-control" placeholder="Escribe tu consulta legal..." @keydown.enter="send">
          <button class="btn-primary" style="padding: 10px 14px" :disabled="loading || !question.trim()" @click="send"><Send :size="16"/></button>
        </div>
      </div>

      <!-- Context Inspector -->
      <div class="play-context">
        <div class="play-header">
          <h4>Contexto Recuperado (Top {{ sources.length || 'K' }})</h4>
          <span v-if="sources.length" class="text-dim" style="font-size: 0.8rem">Similitud promedio: {{ avgScore }}</span>
        </div>
        <div class="chunk-list">
          <div v-if="classification" class="chunk-item">
            <div class="chunk-meta flex-between">
              <span>Clasificador de dominio</span>
              <span :class="classification.in_domain ? 'text-teal' : 'text-amber'">
                {{ classification.in_domain ? 'Dentro del dominio' : 'Fuera del dominio' }}
              </span>
            </div>
            <p>P(tránsito) = {{ classification.in_domain_probability }} • tema: {{ classification.topic }}</p>
          </div>
          <div v-if="!sources.length && !classification" class="text-dim text-sm">Aquí aparecerán los fragmentos de la ley inyectados al modelo.</div>
          <div v-for="(s, i) in sources" :key="i" class="chunk-item">
            <div class="chunk-meta flex-between">
              <span>#{{ i + 1 }} {{ s.reference }}</span>
              <span class="text-sky">Similitud: {{ s.score.toFixed(3) }}</span>
            </div>
            <p>{{ s.text }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { Send } from '@lucide/vue';
import api from '../../services/api';

const question = ref('');
const turns = ref([]);
const sources = ref([]);
const classification = ref(null);
const lastModel = ref('');
const loading = ref(false);

const avgScore = computed(() =>
  (sources.value.reduce((acc, s) => acc + s.score, 0) / sources.value.length).toFixed(3));

const send = async () => {
  const q = question.value.trim();
  if (!q || loading.value) return;
  loading.value = true;
  question.value = '';
  try {
    const { data } = await api.post('/rag/playground', { content: q });
    turns.value.push({ question: q, answer: data.answer, topic: data.topic, refused: data.refused, latency: data.latency_ms.total });
    sources.value = data.sources;
    classification.value = data.classification;
    if (data.model) lastModel.value = data.model;
  } catch (e) {
    turns.value.push({ question: q, answer: 'Motor de IA no disponible.', latency: 0 });
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.msg-text { white-space: pre-line; }
.play-meta { display: flex; gap: 12px; margin-top: 10px; font-size: 0.72rem; color: var(--txt-dim); font-family: 'Space Mono', monospace; }
.chunk-item p { white-space: pre-line; }
</style>
