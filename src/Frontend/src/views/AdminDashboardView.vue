<template>
  <div class="admin-layout">
    <!-- Admin Sidebar (en celular se abre como panel lateral) -->
    <div v-if="sidebarOpen" class="admin-backdrop" @click="sidebarOpen = false"></div>
    <aside :class="['admin-sidebar', { open: sidebarOpen }]">
      <div class="brand">
        <div class="sig"><BotMessageSquare :size="20" stroke-width="2.5" /></div>
        <div>VialBot <span>Admin</span></div>
      </div>
      
      <nav class="admin-nav">
        <div class="nav-lbl">Principal</div>
        <button :class="['nav-btn', { active: activeView === 'overview' }]" @click="activeView = 'overview'">
          <LayoutDashboard :size="18" /> Overview
        </button>
        <button :class="['nav-btn', { active: activeView === 'logs' }]" @click="activeView = 'logs'">
          <TerminalSquare :size="18" /> Logs de Consultas
        </button>
        
        <div class="nav-lbl mt-6">Conocimiento (RAG)</div>
        <button :class="['nav-btn', { active: activeView === 'knowledge' }]" @click="activeView = 'knowledge'">
          <Database :size="18" /> Base Documental
        </button>
        <button :class="['nav-btn', { active: activeView === 'config' }]" @click="activeView = 'config'">
          <Settings :size="18" /> Configuración RAG
        </button>

        <div class="nav-lbl mt-6">Administración</div>
        <button :class="['nav-btn', { active: activeView === 'users' }]" @click="activeView = 'users'">
          <Users :size="18" /> Usuarios y Roles
        </button>

        <div class="nav-lbl mt-6">Monitoreo y Pruebas</div>
        <button :class="['nav-btn', { active: activeView === 'architecture' }]" @click="activeView = 'architecture'">
          <Workflow :size="18" /> Estado del Sistema
        </button>
        <button :class="['nav-btn', { active: activeView === 'playground' }]" @click="activeView = 'playground'">
          <Terminal :size="18" /> Playground RAG
        </button>
        <button :class="['nav-btn', { active: activeView === 'evaluation' }]" @click="activeView = 'evaluation'">
          <FlaskConical :size="18" /> Evaluación del Modelo
        </button>
        
        <router-link to="/" class="nav-btn mt-auto text-sky">
          <ArrowLeft :size="18" /> Volver a la App
        </router-link>
      </nav>
    </aside>

    <!-- Main Content -->
    <main class="admin-main">
      <!-- Top Header -->
      <header class="admin-header">
        <div class="header-title">
          <button class="admin-menu-btn" aria-label="Abrir menú" @click="sidebarOpen = true"><Menu :size="20" /></button>
          <div class="text-dim text-sm">Panel de administración</div>
        </div>
        <div class="header-actions">
          <span class="text-sm">{{ authStore.user?.name }}</span>
          <div class="avatar"><User :size="20" /></div>
        </div>
      </header>

      <div class="admin-content-scroll">
        
        <!-- Overview View -->
        <div v-if="activeView === 'overview'" class="view-panel">
          <div class="page-title">
            <h1>Dashboard Overview</h1>
            <p>Resumen de actividad y salud del sistema VialBot.</p>
          </div>
          
          <AnalyticsDash />
        </div>

        <!-- Logs View -->
        <LogsTab v-if="activeView === 'logs'" />

        <!-- Vista Base Documental -->
        <div v-if="activeView === 'knowledge'" class="view-panel">
          <div class="page-title">
            <h1>Base Documental</h1>
            <p>Normativa oficial indexada en la base vectorial ({{ corpus.vectors ?? '…' }} vectores en <code>{{ corpus.collection ?? '…' }}</code>).
              Para reindexar se ejecuta el pipeline de ingesta de la carpeta <code>AI/</code>.</p>
          </div>
          
          <div class="data-table-wrap">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Documento</th>
                  <th>Tamaño</th>
                  <th>Artículos</th>
                  <th>Fragmentos</th>
                  <th>Fuente oficial</th>
                  <th>Status VectorDB</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="documentsError">
                  <td colspan="6" class="text-center text-amber py-6">{{ documentsError }}</td>
                </tr>
                <tr v-else-if="documents.length === 0">
                  <td colspan="6" class="text-center text-dim py-6">Cargando documentos...</td>
                </tr>
                <tr v-for="doc in documents" :key="doc.id">
                  <td>
                    <div class="file-name">
                      <FileText :size="18" class="text-amber" />
                      <div>
                        <b>{{ doc.title }}</b>
                        <span>{{ doc.filename }}</span>
                      </div>
                    </div>
                  </td>
                  <td>{{ doc.size_mb }} MB</td>
                  <td>{{ doc.articles }}</td>
                  <td>{{ doc.chunks }}</td>
                  <td><a :href="doc.source" target="_blank" rel="noopener" class="text-sky">Ver PDF</a></td>
                  <td><span class="badge green">{{ doc.status }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <RAGSettingsTab v-if="activeView === 'config'" />
        <UsersTab v-if="activeView === 'users'" ref="usersTabRef" @new-user="activeModal = 'newUser'" />
        <EvaluationTab v-if="activeView === 'evaluation'" />
        <ArchitectureTab v-if="activeView === 'architecture'" @node-click="activeLogNode = $event" />
        <PlaygroundTab v-if="activeView === 'playground'" />
        
      </div>
    </main>

    <!-- Generic Modals (Forms) -->
    <div v-if="activeModal === 'newUser'" class="modal-overlay" @click.self="activeModal = null">
      <div class="modal-content system-logs-panel p-6" style="margin-top: 0;">
        <div class="flex-between mb-6">
          <h2 class="m-0 text-white">Añadir Nuevo Usuario</h2>
          <button class="icon-btn-small" @click="activeModal = null"><X :size="16"/></button>
        </div>
        <div class="form-group mb-4">
          <label>Nombre Completo</label>
          <input type="text" v-model="newUserForm.name" class="form-control w-full" placeholder="Ej. Ana Pérez">
        </div>
        <div class="form-group mb-4">
          <label>Correo Electrónico</label>
          <input type="email" v-model="newUserForm.email" class="form-control w-full" placeholder="ana@vialbot.gt">
        </div>
        <div class="form-group mb-4">
          <label>Rol de Acceso</label>
          <select v-model="newUserForm.role_id" class="form-control w-full">
            <option :value="1">Administrador</option>
            <option :value="2">Ciudadano</option>
          </select>
        </div>
        <div class="form-group mb-6">
          <label>Contraseña Temporal</label>
          <input type="password" v-model="newUserForm.password" class="form-control w-full" placeholder="••••••••">
        </div>
        
        <div v-if="newUserError" class="text-amber mb-4 text-sm">{{ newUserError }}</div>
        
        <div class="flex-end">
          <button class="btn-outline mr-4" @click="activeModal = null">Cancelar</button>
          <button class="btn-primary" :disabled="isSubmittingUser" @click="submitNewUser">
            {{ isSubmittingUser ? 'Guardando...' : 'Guardar Usuario' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Toast Notification -->
    <div v-if="toastMsg" class="toast-notification">
      <CheckCircle2 :size="18" class="text-teal"/> {{ toastMsg }}
    </div>

    <!-- Modal for Node Logs -->
    <div v-if="activeLogNode" class="modal-overlay" @click.self="activeLogNode = null">
      <div class="modal-content system-logs-panel" style="margin-top: 0;">
        <div class="logs-header">
          <div class="logs-tabs">
            <button class="log-tab active">
              Logs: {{ NODE_LABELS[activeLogNode] || activeLogNode }}
            </button>
          </div>
          <div class="logs-actions">
            <span class="pulse-dot"></span> Live
            <button class="icon-btn-small" style="margin-left: 8px;" title="Cerrar" @click="activeLogNode = null"><X :size="16"/></button>
          </div>
        </div>
        <div class="logs-window">
          <div v-if="isLoadingLogs" class="text-center text-dim mt-4">Obteniendo logs...</div>
          <div v-else-if="nodeLogs.length === 0" class="text-center text-dim mt-4">No hay logs disponibles.</div>
          <div v-else v-for="(log, i) in nodeLogs" :key="i" class="log-line">
            <span>[{{ log.time }}]</span>
            <span :class="{'log-info': log.type === 'INFO', 'log-warn': log.type === 'WARN' || log.type === 'ERROR', 'log-success': log.type === 'SUCCESS'}">{{ log.type }}</span>
            <span style="margin-right: 8px;">[{{ log.source }}]</span>
            {{ log.message }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import AnalyticsDash from '../components/AnalyticsDash.vue';
import LogsTab from '../components/admin/LogsTab.vue';
import RAGSettingsTab from '../components/admin/RAGSettingsTab.vue';
import ArchitectureTab from '../components/admin/ArchitectureTab.vue';
import UsersTab from '../components/admin/UsersTab.vue';
import EvaluationTab from '../components/admin/EvaluationTab.vue';
import PlaygroundTab from '../components/admin/PlaygroundTab.vue';
import { 
  BotMessageSquare, LayoutDashboard, TerminalSquare, Database, Settings, ArrowLeft,
  User, FileText, Workflow, CheckCircle2,
  Users, Terminal, X, FlaskConical, Menu
} from '@lucide/vue';
import { useAuthStore } from '../stores/authStore';

import api from '../services/api';
import { watch, onMounted } from 'vue';

const activeView = ref('overview');
const sidebarOpen = ref(false);
const activeLogNode = ref(null);
const activeModal = ref(null);
const toastMsg = ref('');

const authStore = useAuthStore();
const documents = ref([]);
const corpus = ref({});
const documentsError = ref('');

const NODE_LABELS = {
  api: 'API Gateway', database: 'Base de Datos', ai: 'Motor de IA',
  vectordb: 'Base Vectorial', llm: 'Modelo de Lenguaje', classifier: 'Clasificador',
};

const fetchDocuments = async () => {
  try {
    const res = await api.get('/documents');
    corpus.value = res.data;
    documents.value = res.data.documents;
  } catch (error) {
    documentsError.value = 'Motor de IA no disponible.';
  }
};

onMounted(() => {
  fetchDocuments();
});

// Al elegir una sección en celular se cierra el panel lateral
watch(activeView, () => { sidebarOpen.value = false; });

const nodeLogs = ref([]);
const isLoadingLogs = ref(false);

// Watch for changes in activeLogNode to fetch logs
watch(activeLogNode, async (newNode) => {
  if (newNode) {
    isLoadingLogs.value = true;
    nodeLogs.value = [];
    try {
      const res = await api.get(`/system/logs?node=${newNode}`);
      nodeLogs.value = res.data.logs;
    } catch (e) {
      console.error(e);
      nodeLogs.value = [{ time: new Date().toLocaleTimeString(), type: 'WARN', source: 'System', message: 'Failed to fetch logs.' }];
    } finally {
      isLoadingLogs.value = false;
    }
  }
});

const usersTabRef = ref(null);
const isSubmittingUser = ref(false);
const newUserError = ref('');
const newUserForm = ref({ name: '', email: '', role_id: 2, password: '' });

const submitNewUser = async () => {
  newUserError.value = '';
  isSubmittingUser.value = true;
  try {
    await api.post('/users', newUserForm.value);
    
    // Reset form and reload
    newUserForm.value = { name: '', email: '', role_id: 2, password: '' };
    closeModalAndToast('Usuario creado exitosamente');
    
    if (usersTabRef.value) {
      usersTabRef.value.loadUsers();
    }
  } catch (error) {
    console.error("Error creating user:", error);
    newUserError.value = error.response?.data?.error || "Error de conexión al crear usuario";
  } finally {
    isSubmittingUser.value = false;
  }
};

const showToast = (msg) => {
  toastMsg.value = msg;
  setTimeout(() => { toastMsg.value = ''; }, 3000);
};

const closeModalAndToast = (msg) => {
  activeModal.value = null;
  showToast(msg);
};
</script>

<style>
.admin-layout {
  display: flex;
  height: 100vh;
  background: #0b1120;
  color: var(--txt-main);
  position: relative;
  z-index: 10;
}

/* Sidebar */
.admin-sidebar {
  width: 280px;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  border-right: 1px solid rgba(255,255,255,0.05);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  position: relative;
  z-index: 2;
}
.brand {
  display: flex; align-items: center; gap: 12px; padding: 24px; font-weight: 800; font-size: 1.2rem;
  border-bottom: 1px solid var(--line);
}
.brand .sig {
  width: 34px; height: 34px; border-radius: 8px; display: grid; place-items: center;
  background: linear-gradient(135deg, var(--amber), var(--amber-deep)); color: #0f172a;
}
.brand span { color: var(--amber); }

.admin-nav { padding: 24px 16px; display: flex; flex-direction: column; gap: 4px; flex: 1; }
.nav-lbl { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--txt-dim); font-weight: 700; margin-bottom: 8px; padding-left: 12px; }
.mt-6 { margin-top: 24px; }
.mt-auto { margin-top: auto; }
.text-sky { color: var(--sky) !important; }

.nav-btn {
  display: flex; align-items: center; gap: 12px; padding: 12px; width: 100%; border-radius: 8px;
  border: none; background: transparent; color: var(--txt-dim); font-weight: 600; font-size: 0.95rem; font-family: 'Sora'; cursor: pointer; text-decoration: none; text-align: left;
  transition: 0.2s;
}
.nav-btn:hover { background: rgba(255,255,255,0.05); color: #fff; }
.nav-btn.active { background: rgba(255,255,255,0.08); color: #fff; border-left: 3px solid var(--amber); border-radius: 4px 8px 8px 4px; }

/* Main */
.admin-main { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: transparent; position: relative; z-index: 1;}

.admin-layout::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300' viewBox='0 0 300 300'%3E%3Ctext x='30' y='50' font-size='24' opacity='0.06' transform='rotate(15 30 50)'%3E%F0%9F%9A%97%3C/text%3E%3Ctext x='180' y='80' font-size='28' opacity='0.06' transform='rotate(-20 180 80)'%3E%F0%9F%9A%A6%3C/text%3E%3Ctext x='90' y='200' font-size='26' opacity='0.06' transform='rotate(-10 90 200)'%3E%F0%9F%9B%91%3C/text%3E%3Ctext x='240' y='240' font-size='24' opacity='0.06' transform='rotate(25 240 240)'%3E%F0%9F%9A%8C%3C/text%3E%3Ctext x='140' y='140' font-size='22' opacity='0.06' transform='rotate(45 140 140)'%3E%F0%9F%9A%93%3C/text%3E%3Ctext x='30' y='260' font-size='24' opacity='0.06' transform='rotate(-15 30 260)'%3E%E2%9A%A0%EF%B8%8F%3C/text%3E%3Ctext x='260' y='40' font-size='26' opacity='0.06' transform='rotate(5 260 40)'%3E%F0%9F%8E%AB%3C/text%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 300px 300px;
  z-index: 0;
  pointer-events: none;
}

/* Header */
.admin-header {
  height: 70px; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; align-items: center; justify-content: space-between; padding: 0 40px; background: rgba(15, 23, 42, 0.6); flex-shrink: 0;
  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  position: relative;
  z-index: 2;
}
.search-box {
  display: flex; align-items: center; gap: 10px; background: rgba(255,255,255,0.05); padding: 8px 16px; border-radius: 8px; width: 300px; border: 1px solid rgba(255,255,255,0.05);
}
.search-box input { background: transparent; border: none; outline: none; color: #fff; font-size: 0.9rem; font-family: 'Sora'; width: 100%; }
.search-box input::placeholder { color: var(--txt-dim); }
.text-dim { color: var(--txt-dim); }

.header-actions { display: flex; align-items: center; gap: 20px; }
.icon-btn { background: transparent; border: none; color: var(--txt-dim); cursor: pointer; transition: 0.2s; display: grid; place-items: center; }
.icon-btn:hover { color: #fff; }
.avatar { width: 36px; height: 36px; border-radius: 50%; background: #1e293b; border: 1px solid var(--line); display: grid; place-items: center; color: var(--txt-dim); cursor: pointer; }

/* Content */
.admin-content-scroll { flex: 1; overflow-y: auto; padding: 40px; position: relative; z-index: 1; }
.view-panel { animation: fade 0.3s ease-out; }
@keyframes fade { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

.page-title { margin-bottom: 30px; }
.page-title h1 { font-size: 1.8rem; font-weight: 800; color: #fff; }
.page-title p { color: var(--txt-dim); font-size: 1rem; margin-top: 4px; }
.flex-between { display: flex; justify-content: space-between; align-items: flex-end; }

/* Data Tables */
.data-table-wrap {
  background: linear-gradient(145deg, rgba(14, 165, 233, 0.15), rgba(15, 23, 42, 0.7)); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(14, 165, 233, 0.3); border-radius: 12px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
}
.data-table { width: 100%; border-collapse: collapse; text-align: left; }
.data-table th { padding: 16px 20px; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--txt-dim); border-bottom: 1px solid rgba(255,255,255,0.05); background: rgba(0,0,0,0.2); font-weight: 700; }
.data-table td { padding: 16px 20px; font-size: 0.95rem; border-bottom: 1px solid rgba(255,255,255,0.05); color: #fff; vertical-align: middle; }
.data-table tr:last-child td { border-bottom: none; }
.data-table tr:hover td { background: rgba(255,255,255,0.02); }

.td-id { font-family: 'Space Mono', monospace; font-size: 0.85rem; color: var(--txt-dim) !important; }
.td-query { font-weight: 600; }

.badge { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 99px; font-size: 0.75rem; font-weight: 700; border: 1px solid transparent; }
.badge.gray { background: #1e293b; color: var(--txt-dim); border-color: var(--line); }
.badge.green { background: rgba(20, 184, 166, 0.1); color: var(--teal); border-color: rgba(20, 184, 166, 0.2); }
.badge.yellow { background: rgba(245, 158, 11, 0.1); color: var(--amber); border-color: rgba(245, 158, 11, 0.2); }
.badge.red { background: rgba(239, 68, 68, 0.1); color: #ef4444; border-color: rgba(239, 68, 68, 0.2); }

.file-name { display: flex; align-items: center; gap: 16px; }
.file-name b { display: block; font-size: 0.95rem; }
.file-name span { display: block; font-size: 0.8rem; color: var(--txt-dim); font-family: 'Space Mono', monospace; margin-top: 2px;}
.text-amber { color: var(--amber); }

.icon-btn-small { background: transparent; border: none; color: var(--txt-dim); cursor: pointer; display: grid; place-items: center; border-radius: 4px; padding: 4px;}
.icon-btn-small:hover { background: #1e293b; color: #fff; }

/* Settings Form */
.settings-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.settings-card { background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; padding: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); transition: all 0.3s ease; }
.settings-card:hover { transform: translateY(-4px); box-shadow: 0 20px 40px rgba(0,0,0,0.3); }

/* Colores dinámicos y vibrantes para las tarjetas */
.settings-card:nth-child(1) { background: linear-gradient(145deg, rgba(168, 85, 247, 0.2), rgba(15, 23, 42, 0.7)); border-color: rgba(168, 85, 247, 0.4); }
.settings-card:nth-child(1) h3 svg { color: #c084fc; }
.settings-card:nth-child(1):hover { border-color: rgba(168, 85, 247, 0.6); }

.settings-card:nth-child(2) { background: linear-gradient(145deg, rgba(20, 184, 166, 0.2), rgba(15, 23, 42, 0.7)); border-color: rgba(20, 184, 166, 0.4); }
.settings-card:nth-child(2) h3 svg { color: #2dd4bf; }
.settings-card:nth-child(2):hover { border-color: rgba(20, 184, 166, 0.6); }

.settings-card h3 { font-size: 1.1rem; color: #fff; margin-bottom: 24px; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 12px;}
.form-group { margin-bottom: 20px; }
.form-group label { display: flex; justify-content: space-between; font-size: 0.85rem; color: var(--txt-dim); margin-bottom: 8px; font-weight: 600; }
.form-group label span:last-child { color: var(--amber); font-family: 'Space Mono', monospace; }
.form-control { width: 100%; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; color: #fff; font-family: 'Sora'; font-size: 0.95rem; outline: none; transition: 0.2s; -webkit-appearance: none; appearance: none;}
.form-control:focus { border-color: var(--amber); box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.2); background: rgba(255,255,255,0.06); }
textarea.form-control { resize: vertical; line-height: 1.6;}
.form-control-range { width: 100%; accent-color: var(--amber); margin-top: 4px;}
.help-text { display: block; font-size: 0.75rem; color: var(--txt-dim); margin-top: 8px; line-height: 1.4;}
.split-group { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

.btn-primary { background: var(--amber); color: #0a1628; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 700; font-family: 'Sora'; font-size: 0.9rem; cursor: pointer; display: flex; align-items: center; gap: 8px; transition: 0.2s; }
.btn-primary:hover { filter: brightness(1.1); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3); }

/* Architecture View */
.arch-canvas { display: flex; flex-direction: column; align-items: center; padding: 60px 40px; background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border-radius: 16px; border: 1px solid rgba(255,255,255,0.05); margin-top: 20px; box-shadow: inset 0 0 40px rgba(0,0,0,0.5);}
.arch-node { display: flex; align-items: center; gap: 16px; background: #0f172a; border: 1px solid rgba(255,255,255,0.1); padding: 16px 24px; border-radius: 12px; width: 280px; position: relative; box-shadow: 0 10px 20px rgba(0,0,0,0.3); z-index: 2; transition: 0.3s; cursor: pointer;}
.arch-node:hover { transform: translateY(-4px); border-color: var(--sky); box-shadow: 0 10px 30px rgba(14, 165, 233, 0.2); }
.node-icon { width: 48px; height: 48px; background: rgba(255,255,255,0.05); border-radius: 10px; display: grid; place-items: center; color: #fff;}
.node-info h4 { margin: 0; font-size: 1rem; color: #fff; }
.node-info span { font-size: 0.8rem; color: var(--txt-dim); font-family: 'Space Mono', monospace; margin-top: 4px; display: block;}
.status-indicator { position: absolute; top: -12px; right: -12px; display: flex; align-items: center; gap: 4px; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; background: #1e293b; border: 1px solid var(--line); box-shadow: 0 4px 6px rgba(0,0,0,0.2);}

.healthy { border-color: rgba(20, 184, 166, 0.4); }
.healthy .node-icon { color: var(--teal); background: rgba(20, 184, 166, 0.1);}
.healthy .status-indicator { color: var(--teal); border-color: rgba(20, 184, 166, 0.3); }

.warning { border-color: rgba(245, 158, 11, 0.4); }
.warning .node-icon { color: var(--amber); background: rgba(245, 158, 11, 0.1);}
.warning .status-indicator { color: var(--amber); border-color: rgba(245, 158, 11, 0.3); }

.arch-line { width: 2px; height: 40px; background: rgba(255,255,255,0.15); margin: 0 auto; position: relative; z-index: 1;}
.arch-line::after { content: ''; position: absolute; bottom: -4px; left: -4px; border-width: 6px 5px 0; border-style: solid; border-color: rgba(255,255,255,0.3) transparent transparent transparent; }

.arch-branches { display: flex; gap: 60px; justify-content: center; }

/* Modal and System Logs Panel */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); backdrop-filter: blur(4px); z-index: 100; display: flex; align-items: center; justify-content: center; animation: fadeIn 0.2s;}
.modal-content { width: 700px; max-width: 90%; margin: 0; box-shadow: 0 25px 50px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.15);}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.system-logs-panel { background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; overflow: hidden; margin-top: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);}
.logs-header { display: flex; justify-content: space-between; align-items: center; background: rgba(0,0,0,0.3); padding: 0 16px; border-bottom: 1px solid rgba(255,255,255,0.05); }
.logs-tabs { display: flex; }
.log-tab { background: transparent; border: none; color: var(--txt-dim); padding: 14px 16px; font-size: 0.85rem; font-family: 'Sora'; font-weight: 600; cursor: pointer; border-bottom: 2px solid transparent; transition: 0.2s;}
.log-tab:hover { color: #fff; background: rgba(255,255,255,0.02);}
.log-tab.active { color: var(--sky); border-bottom-color: var(--sky); }
.logs-actions { display: flex; align-items: center; gap: 8px; font-size: 0.8rem; font-weight: 700; color: var(--txt-dim);}
.pulse-dot { width: 8px; height: 8px; background: var(--teal); border-radius: 50%; box-shadow: 0 0 8px var(--teal); animation: pulse 2s infinite; }
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.3; } 100% { opacity: 1; } }
.logs-window { padding: 20px; font-family: 'Space Mono', monospace; font-size: 0.85rem; color: var(--txt-dim); height: 220px; overflow-y: auto; background: rgba(0,0,0,0.15);}
.log-line { margin-bottom: 8px; line-height: 1.4;}
.log-line span:first-child { color: #64748b; margin-right: 8px;}
.log-info { color: var(--sky); font-weight: 700; margin-right: 8px;}
.log-warn { color: var(--amber); font-weight: 700; margin-right: 8px;}
.log-success { color: var(--teal); font-weight: 700; margin-right: 8px;}

/* Users View */
.user-row { display: flex; align-items: center; gap: 12px; }
.avatar-small { width: 32px; height: 32px; background: rgba(14, 165, 233, 0.2); color: var(--sky); border-radius: 50%; display: grid; place-items: center; font-weight: 700; font-size: 0.8rem;}
.user-row b { display: block; font-size: 0.95rem; }
.user-row span { display: block; font-size: 0.8rem; color: var(--txt-dim); }

/* Billing View */
.billing-stats { display: flex; gap: 40px; margin-top: 10px; }
.stat-item { display: flex; flex-direction: column; gap: 8px; }
.stat-label { font-size: 0.85rem; color: var(--txt-dim); text-transform: uppercase; letter-spacing: 0.05em; font-weight: 700; }
.stat-value { font-size: 2rem; font-weight: 800; color: #fff; }
.text-sm { font-size: 0.85rem; }
.font-bold { font-weight: 700; }
.progress-bar { width: 100%; height: 8px; background: rgba(255,255,255,0.05); border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, var(--amber), #f59e0b); border-radius: 4px;}
.api-key-row { display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.02); padding: 16px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.05);}
.api-key-row h4 { margin: 0 0 4px 0; color: #fff; font-size: 0.95rem;}
.masked-key { font-family: 'Space Mono', monospace; font-size: 0.85rem; color: var(--txt-dim); }
.btn-outline { background: transparent; border: 1px solid rgba(255,255,255,0.1); color: #fff; padding: 6px 12px; border-radius: 6px; font-family: 'Sora'; font-size: 0.8rem; cursor: pointer; transition: 0.2s;}
.btn-outline:hover { background: rgba(255,255,255,0.1); }
.mt-4 { margin-top: 16px; }

/* Playground View */
.playground-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; height: 550px; }
.play-chat, .play-context { background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.2);}
.play-header { padding: 16px; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between; align-items: center; background: rgba(0,0,0,0.2);}
.play-header h4 { margin: 0; color: #fff; font-size: 0.95rem; }
.play-messages { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 16px;}
.play-msg { padding: 12px 16px; border-radius: 12px; font-size: 0.9rem; max-width: 85%; line-height: 1.5; }
.play-msg.user { background: rgba(14, 165, 233, 0.2); border: 1px solid rgba(14, 165, 233, 0.3); color: #fff; align-self: flex-end; border-bottom-right-radius: 2px;}
.play-msg.bot { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.05); color: #fff; align-self: flex-start; border-bottom-left-radius: 2px;}
.play-input { padding: 16px; border-top: 1px solid rgba(255,255,255,0.05); display: flex; gap: 12px; background: rgba(0,0,0,0.2);}
.chunk-list { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; }
.chunk-item { background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 16px; border-radius: 8px;}
.chunk-meta { font-family: 'Space Mono', monospace; font-size: 0.75rem; font-weight: 700; color: var(--txt-dim); margin-bottom: 12px; border-bottom: 1px dashed rgba(255,255,255,0.1); padding-bottom: 8px;}
.chunk-item p { margin: 0; font-size: 0.85rem; line-height: 1.6; color: #cbd5e1;}
.text-sky { color: var(--sky); }

/* Modals & Forms UI Additions */
.p-6 { padding: 32px; }
.mb-6 { margin-bottom: 24px; }
.mt-2 { margin-top: 8px; }
.mr-4 { margin-right: 16px; }
.m-0 { margin: 0; }
.flex-end { display: flex; justify-content: flex-end; }
.w-full { width: 100%; box-sizing: border-box;}
.block { display: block; }
.text-white { color: #fff !important; }
.drag-drop-zone { border: 2px dashed rgba(255,255,255,0.15); border-radius: 12px; padding: 40px 20px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; cursor: pointer; transition: 0.2s; background: rgba(0,0,0,0.2);}
.drag-drop-zone:hover { border-color: var(--sky); background: rgba(14, 165, 233, 0.05);}

/* Toast Notifications */
.toast-notification { position: fixed; bottom: 30px; right: 30px; background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); border: 1px solid rgba(20, 184, 166, 0.3); padding: 16px 24px; border-radius: 8px; color: #fff; font-weight: 600; display: flex; align-items: center; gap: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); animation: slideUp 0.3s; z-index: 9999;}
/* Celular y tableta */
.admin-backdrop, .admin-menu-btn { display: none; }
.header-title { display: flex; align-items: center; gap: 12px; }
@media (max-width: 900px) {
  .admin-layout { height: 100dvh; }
  .admin-sidebar {
    position: fixed; top: 0; bottom: 0; left: 0;
    width: min(280px, 86vw);
    background: rgba(15, 23, 42, 0.97);
    transform: translateX(-100%);
    transition: transform 0.25s ease;
    z-index: 60;
    overflow-y: auto;
  }
  .admin-sidebar.open { transform: translateX(0); box-shadow: 12px 0 32px rgba(0,0,0,0.5); }
  .admin-backdrop { display: block; position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 55; }
  .admin-menu-btn {
    display: grid; place-items: center; width: 38px; height: 38px;
    background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px;
    color: #fff; cursor: pointer;
  }

  .admin-header { height: 60px; padding: 0 16px; }
  .admin-content-scroll { padding: 20px 16px; }
  .admin-content-scroll section { padding: 0; }
  .page-title { margin-bottom: 20px; }
  .page-title h1 { font-size: 1.4rem; }
  .page-title p { font-size: 0.9rem; }
  .flex-between { flex-wrap: wrap; gap: 12px; }

  .settings-grid, .split-group { grid-template-columns: 1fr; }
  .playground-grid { grid-template-columns: 1fr; height: auto; }
  .play-chat { min-height: 420px; }
  .play-context { max-height: 480px; }

  .data-table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  .data-table { min-width: 640px; }
  .data-table th, .data-table td { padding: 12px 14px; }

  .arch-canvas { padding: 24px 12px; }
  .arch-node { width: 100%; max-width: 340px; }
  .arch-branches { flex-direction: column; align-items: center; gap: 16px; }

  .p-6 { padding: 20px; }
  .toast-notification { left: 16px; right: 16px; bottom: 16px; }
}

@keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
</style>
