<template>
  <section id="datos">
    <div class="eyebrow">Panel de Control</div>
    <div class="h2">¿Qué preguntan los ciudadanos?</div>
    <p class="lead">Cada consulta es clasificada por el modelo propio de VialBot. Este panel muestra los temas que más dudas generan, información útil para orientar las campañas de educación vial.</p>
    
    <div class="dash" ref="dashContainer">
      <div class="kpi">
        <div class="ic-wrap"><Users :size="24" stroke-width="2.5" /></div>
        <div class="n" :data-count="stats.total_users">0</div>
        <div class="l">Usuarios Registrados</div>
        <div class="trend up">{{ stats.total_conversations }} conversaciones</div>
      </div>
      <div class="kpi">
        <div class="ic-wrap"><MessageSquare :size="24" stroke-width="2.5" /></div>
        <div class="n" :data-count="stats.total_questions">0</div>
        <div class="l">Consultas Recibidas</div>
        <div class="trend up">{{ stats.classified_questions }} clasificadas por tema</div>
      </div>
      <div class="kpi">
        <div class="ic-wrap"><Zap :size="24" stroke-width="2.5" /></div>
        <div class="n" :data-count="avgSeconds" data-suffix=" s">0</div>
        <div class="l">Tiempo Promedio de Respuesta</div>
        <div class="trend">{{ stats.out_of_domain }} fuera de dominio rechazadas</div>
      </div>
      <div class="kpi">
        <div class="ic-wrap"><Book :size="24" stroke-width="2.5" /></div>
        <div class="n" :data-count="stats.total_articles ?? 0">0</div>
        <div class="l">Artículos Indexados</div>
        <div class="trend">{{ stats.total_documents ?? '–' }} documentos oficiales</div>
      </div>
    </div>

    <div class="chartbox" ref="chartContainer">
      <h3>Temas más consultados</h3>
      <p>Distribución de las consultas dentro del dominio de tránsito, según el clasificador de VialBot.</p>

      <div v-if="!stats.topics.length" class="empty">Todavía no hay consultas clasificadas.</div>
      <div v-for="topic in stats.topics" :key="topic.key" class="barrow">
        <div class="lbl">
          <component :is="topicMeta(topic.key).icon" :size="16" class="lbl-ic" />
          {{ topicMeta(topic.key).label }}
        </div>
        <div class="track">
          <div class="fill" :data-w="topic.percentage" :style="{ background: `linear-gradient(90deg, ${topicMeta(topic.key).from}, ${topicMeta(topic.key).to})` }"></div>
        </div>
        <div class="val">{{ topic.percentage }}%</div>
      </div>
    </div>

    <div v-if="stats.top_articles.length" class="chartbox">
      <h3>Artículos más consultados</h3>
      <p>Fuente principal de las respuestas generadas.</p>
      <div v-for="art in stats.top_articles" :key="art.reference" class="article-row">
        <span>{{ art.reference }}</span>
        <b>{{ art.total }}</b>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref, computed, nextTick } from 'vue';
import { Users, MessageSquare, Zap, Book, Car, CreditCard, FileText, AlertOctagon, Siren, Shield, Wrench, Bus, Route } from '@lucide/vue';
import api from '../services/api';

const dashContainer = ref(null);
const chartContainer = ref(null);
const stats = ref({
  total_users: 0, total_conversations: 0, total_questions: 0, classified_questions: 0,
  out_of_domain: 0, avg_latency_ms: 0, total_documents: null, total_articles: null,
  topics: [], top_articles: []
});

const avgSeconds = computed(() => (stats.value.avg_latency_ms / 1000).toFixed(1));

// Etiquetas de los temas que predice el clasificador (AI/config.py → TOPICS)
const TOPICS = {
  multas: { label: 'Multas e infracciones', icon: Car, from: 'var(--amber)', to: 'var(--amber-deep)' },
  licencias: { label: 'Licencias de conducir', icon: CreditCard, from: 'var(--sky)', to: '#0284c7' },
  documentos_vehiculares: { label: 'Documentos vehiculares', icon: FileText, from: 'var(--teal)', to: '#0d9488' },
  normas_circulacion: { label: 'Normas de circulación', icon: Route, from: '#22c55e', to: '#15803d' },
  senales: { label: 'Señales de tránsito', icon: AlertOctagon, from: '#a855f7', to: '#7e22ce' },
  accidentes: { label: 'Accidentes y emergencias', icon: Siren, from: '#ef4444', to: '#b91c1c' },
  autoridades: { label: 'Autoridades de tránsito', icon: Shield, from: '#64748b', to: '#334155' },
  equipamiento_vehicular: { label: 'Equipamiento del vehículo', icon: Wrench, from: '#f97316', to: '#c2410c' },
  transporte_carga_pasajeros: { label: 'Transporte de carga y pasajeros', icon: Bus, from: '#ec4899', to: '#be185d' },
};
const topicMeta = (key) => TOPICS[key] || { label: key, icon: FileText, from: '#94a3b8', to: '#64748b' };

const initAnimations = () => {
  const io = new IntersectionObserver((es) => {
    es.forEach(e => {
      if(e.isIntersecting) {
        e.target.querySelectorAll('.fill').forEach(f => f.style.width = f.dataset.w + '%');
        e.target.querySelectorAll('.n[data-count]').forEach(n => {
          const end = parseFloat(n.getAttribute('data-count') || n.dataset.count);
          if(isNaN(end)) return;
          const suf = n.dataset.suffix || '';
          let cur = 0;
          const dec = end % 1 !== 0;
          const step = Math.max(end / 40, dec ? 0.1 : 1); // Evitar loop infinito si end es 0
          const it = setInterval(() => {
            cur += step;
            if(cur >= end) {
              cur = end;
              clearInterval(it);
            }
            n.textContent = (dec ? cur.toFixed(1) : Math.floor(cur)) + suf;
          }, 25);
        });
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.2 });
  
  if (dashContainer.value) io.observe(dashContainer.value);
  if (chartContainer.value) io.observe(chartContainer.value);
};

onMounted(async () => {
  try {
      const response = await api.get('/dashboard/stats');
      stats.value = response.data;
  } catch (error) {
      console.error("Error al cargar estadísticas", error);
  } finally {
      nextTick(() => {
          initAnimations();
      });
  }
});
</script>

<style scoped>
.dash { margin-top: 50px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
@media(max-width:900px){.dash{grid-template-columns:1fr 1fr;}}
@media(max-width:500px){.dash{grid-template-columns:1fr;}}

.kpi { background: rgba(30, 41, 59, 0.6); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.05); border-radius: 24px; padding: 24px; position: relative; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.2); transition: all 0.3s ease;}
.ic-wrap { width: 48px; height: 48px; border-radius: 16px; display: grid; place-items: center; font-size: 1.5rem; margin-bottom: 16px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.05); transition: all 0.3s ease;}

/* Colores dinámicos por KPI - Estilo Vidrio */
.kpi:nth-child(1) { background: linear-gradient(145deg, rgba(245, 158, 11, 0.25), rgba(30, 41, 59, 0.6)); border-color: rgba(245, 158, 11, 0.4); }
.kpi:nth-child(1) .ic-wrap { color: #fbbf24; border-color: rgba(245, 158, 11, 0.5); background: rgba(245, 158, 11, 0.2); }
.kpi:nth-child(1):hover { border-color: #fbbf24; box-shadow: 0 20px 40px rgba(245, 158, 11, 0.3); transform: translateY(-8px); }

.kpi:nth-child(2) { background: linear-gradient(145deg, rgba(20, 184, 166, 0.25), rgba(30, 41, 59, 0.6)); border-color: rgba(20, 184, 166, 0.4); }
.kpi:nth-child(2) .ic-wrap { color: #2dd4bf; border-color: rgba(20, 184, 166, 0.5); background: rgba(20, 184, 166, 0.2); }
.kpi:nth-child(2):hover { border-color: #2dd4bf; box-shadow: 0 20px 40px rgba(20, 184, 166, 0.3); transform: translateY(-8px); }

.kpi:nth-child(3) { background: linear-gradient(145deg, rgba(14, 165, 233, 0.25), rgba(30, 41, 59, 0.6)); border-color: rgba(14, 165, 233, 0.4); }
.kpi:nth-child(3) .ic-wrap { color: #38bdf8; border-color: rgba(14, 165, 233, 0.5); background: rgba(14, 165, 233, 0.2); }
.kpi:nth-child(3):hover { border-color: #38bdf8; box-shadow: 0 20px 40px rgba(14, 165, 233, 0.3); transform: translateY(-8px); }

.kpi:nth-child(4) { background: linear-gradient(145deg, rgba(168, 85, 247, 0.25), rgba(30, 41, 59, 0.6)); border-color: rgba(168, 85, 247, 0.4); }
.kpi:nth-child(4) .ic-wrap { color: #c084fc; border-color: rgba(168, 85, 247, 0.5); background: rgba(168, 85, 247, 0.2); }
.kpi:nth-child(4):hover { border-color: #c084fc; box-shadow: 0 20px 40px rgba(168, 85, 247, 0.3); transform: translateY(-8px); }

.kpi .n { font-size: 2.5rem; font-weight: 800; letter-spacing: -0.03em; color: #fff; line-height: 1;}
.kpi .l { font-size: 0.9rem; color: var(--txt-dim); font-weight: 500; margin-top: 8px; }
.kpi .trend { font-size: 0.8rem; font-weight: 600; margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.05); color: var(--txt-dim);}
.kpi .trend.up { color: var(--teal); }

.chartbox { margin-top: 40px; background: rgba(30, 41, 59, 0.6); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.05); border-radius: 24px; padding: 32px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
.chartbox h3 { font-size: 1.25rem; font-weight: 700; color: #fff; }
.chartbox p { font-size: 0.95rem; color: var(--txt-dim); margin-top: 6px; margin-bottom: 30px; }

.barrow { display: flex; align-items: center; gap: 20px; margin-bottom: 20px; }
.barrow .lbl { width: 220px; font-size: 0.95rem; font-weight: 600; color: #fff; display: flex; align-items: center; }
.lbl-ic { margin-right: 8px; color: var(--txt-dim); }
@media(max-width:600px){.barrow .lbl{width:140px;font-size:0.85rem}}

.barrow .track { flex: 1; height: 16px; background: rgba(255,255,255,0.05); border-radius: 99px; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);}
.barrow .fill { height: 100%; border-radius: 99px; width: 0; transition: width 1.5s cubic-bezier(0.2, 0.8, 0.2, 1); }
.barrow .val { width: 50px; text-align: right; font-weight: 700; font-size: 0.95rem; color: var(--amber); }
.empty { color: var(--txt-dim); font-size: 0.9rem; }
.article-row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.05); color: #fff; font-size: 0.95rem; }
.article-row b { color: var(--amber); }
</style>
