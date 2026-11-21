<template>
  <div class="view-panel">
    <div class="page-title flex-between">
      <div>
        <h1>Estado del Sistema (RAG)</h1>
        <p>Estado real de cada componente, medido al momento de la consulta. Haz clic en un nodo para ver su registro.</p>
      </div>
      <button class="btn-primary" style="background: rgba(14, 165, 233, 0.2); color: var(--sky);" @click="fetchHealth">
        <Activity :size="16" :class="{ 'spin': isLoading }"/> {{ isLoading ? 'Diagnosticando...' : 'Diagnóstico de Red' }}
      </button>
    </div>

    <div class="arch-canvas">
      <template v-for="(row, i) in layout" :key="i">
        <div v-if="i > 0" class="arch-line"></div>
        <div :class="row.length > 1 ? 'arch-row' : ''">
          <div
            v-for="node in row"
            :key="node.key"
            :class="['arch-node', health[node.key]?.status, { clickable: node.logs }]"
            @click="node.logs && $emit('node-click', node.key)"
          >
            <div class="node-icon"><component :is="node.icon" :size="24"/></div>
            <div class="node-info">
              <h4>{{ node.title }}</h4>
              <span>{{ health[node.key]?.detail || node.tech }} • {{ health[node.key]?.latency || '...' }}</span>
            </div>
            <div class="status-indicator">
              <CheckCircle2 v-if="health[node.key]?.status === 'healthy'" :size="14"/>
              <AlertTriangle v-else :size="14"/>
              {{ health[node.key]?.label || '...' }}
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Activity, User, Server, CheckCircle2, Database, Cpu, AlertTriangle, Brain, Layers, ShieldCheck } from '@lucide/vue';
import api from '../../services/api';

defineEmits(['node-click']);

// Flujo de una consulta: navegador → API PHP → (MySQL | motor de IA) → componentes del motor
const layout = [
  [{ key: 'frontend', title: 'Ciudadano (Frontend)', tech: 'Vue 3', icon: User }],
  [{ key: 'api', title: 'Backend API Gateway', tech: 'PHP 8', icon: Server, logs: true }],
  [
    { key: 'database', title: 'Base de Datos', tech: 'MySQL', icon: Database, logs: true },
    { key: 'ai', title: 'Motor de IA', tech: 'Python • FastAPI', icon: Brain, logs: true },
  ],
  [
    { key: 'classifier', title: 'Clasificador de Dominio', tech: 'Modelo propio', icon: ShieldCheck, logs: true },
    { key: 'vectordb', title: 'Base Vectorial', tech: 'ChromaDB', icon: Layers, logs: true },
    { key: 'llm', title: 'Modelo de Lenguaje', tech: 'Ollama', icon: Cpu, logs: true },
  ],
];

const loading = { status: 'offline', latency: '...', label: 'Cargando...' };
const health = ref(Object.fromEntries(layout.flat().map(n => [n.key, loading])));
const isLoading = ref(false);

const fetchHealth = async () => {
  isLoading.value = true;
  try {
    const res = await api.get('/system/health');
    health.value = res.data;
  } catch (error) {
    console.error("Error fetching system health:", error);
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  fetchHealth();
});
</script>

<style scoped>
.spin { animation: spin 1s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }
.arch-row { display: flex; gap: 24px; justify-content: center; flex-wrap: wrap; }
.arch-row .arch-node { flex: 1; min-width: 240px; max-width: 340px; }
.arch-node:not(.clickable) { cursor: default; }
.warning { border-color: rgba(245, 158, 11, 0.4) !important; }
.warning .node-icon { color: var(--amber) !important; background: rgba(245, 158, 11, 0.1) !important; }
.warning .status-indicator { color: var(--amber) !important; border-color: rgba(245, 158, 11, 0.3) !important; }
.offline { border-color: rgba(239, 68, 68, 0.4) !important; }
.offline .node-icon { color: #ef4444 !important; background: rgba(239, 68, 68, 0.1) !important;}
.offline .status-indicator { color: #ef4444 !important; border-color: rgba(239, 68, 68, 0.3) !important; }
</style>
