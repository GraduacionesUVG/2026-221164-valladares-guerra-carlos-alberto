<template>
  <div class="view-panel">
    <div class="page-title">
      <h1>Logs de Consultas</h1>
      <p>Consultas de los ciudadanos con el tema asignado por el clasificador y los artículos usados como fuente.</p>
    </div>
    
    <div class="data-table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Fecha y Hora</th>
            <th>Usuario</th>
            <th>Consulta</th>
            <th>Tema</th>
            <th>Fuentes (RAG)</th>
            <th>Estado</th>
            <th>Latencia</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="8" class="text-center text-dim py-4">Cargando logs...</td>
          </tr>
          <tr v-else-if="logs.length === 0">
            <td colspan="8" class="text-center text-dim py-4">No hay consultas registradas.</td>
          </tr>
          <tr v-for="log in logs" :key="log.id">
            <td class="td-id">#{{ log.id }}</td>
            <td>{{ formatDate(log.created_at) }}</td>
            <td><span class="text-amber font-bold">{{ log.user_name }}</span></td>
            <td class="td-query">"{{ log.query }}"</td>
            <td><span class="text-sm">{{ log.topic ? log.topic.replaceAll('_', ' ') : '—' }}</span></td>
            <td>
              <span v-if="log.sources.length" class="text-sm">{{ [...new Set(log.sources)].slice(0, 2).join(', ') }}</span>
              <span v-else class="text-dim text-sm">—</span>
            </td>
            <td><span :class="['badge', status(log).color]">{{ status(log).label }}</span></td>
            <td><span class="text-dim text-sm">{{ log.latency_ms != null ? (log.latency_ms / 1000).toFixed(1) + ' s' : '—' }}</span></td>
          </tr>
        </tbody>
      </table>
      
      <!-- Paginación -->
      <div v-if="totalPages > 1" class="pagination-controls">
        <button class="btn-outline" :disabled="currentPage === 1" @click="changePage(currentPage - 1)">Anterior</button>
        <span class="page-info">Página {{ currentPage }} de {{ totalPages }}</span>
        <button class="btn-outline" :disabled="currentPage === totalPages" @click="changePage(currentPage + 1)">Siguiente</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../../services/api';

const logs = ref([]);
const loading = ref(true);
const currentPage = ref(1);
const totalPages = ref(1);

const loadLogs = async (page = 1) => {
  loading.value = true;
  try {
    const res = await api.get(`/logs?page=${page}&limit=10`);
    logs.value = res.data.data;
    currentPage.value = res.data.meta.current_page;
    totalPages.value = res.data.meta.total_pages;
  } catch (error) {
    console.error("Error cargando logs:", error);
  } finally {
    loading.value = false;
  }
};

const STATUS = {
  out_of_domain: { label: 'Fuera de dominio', color: 'gray' },
  no_context: { label: 'Sin normativa', color: 'gray' },
  unavailable: { label: 'Motor no disponible', color: 'red' },
};
const status = (log) => STATUS[log.refused] || { label: 'Respondida', color: 'green' };

const changePage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    loadLogs(page);
  }
};

const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleString('es-GT', { 
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' 
  });
};

onMounted(() => {
  loadLogs(1);
});
</script>

<style scoped>
.pagination-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: rgba(0,0,0,0.2);
  border-top: 1px solid rgba(255,255,255,0.05);
}
.page-info {
  font-size: 0.85rem;
  color: var(--txt-dim);
  font-family: 'Space Mono', monospace;
}
.text-center { text-align: center; }
.py-4 { padding-top: 16px; padding-bottom: 16px; }
.font-bold { font-weight: 700; }
</style>
