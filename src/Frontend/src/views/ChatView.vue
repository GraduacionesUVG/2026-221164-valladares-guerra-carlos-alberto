<template>
  <div class="app-layout">
    <NavBar />
    
    <div class="chat-container">
      <!-- Sidebar (en celular se abre como panel lateral) -->
      <div v-if="sidebarOpen" class="sidebar-backdrop" @click="sidebarOpen = false"></div>
      <aside :class="['sidebar', { open: sidebarOpen }]">
        <div class="side-header flex-row">
          <h3>Mis conversaciones</h3>
          <button class="new-conv" :disabled="busy" @click="newConversation" title="Nueva conversación">
            <Plus :size="16" stroke-width="2.5" /> Nueva
          </button>
        </div>
        <div class="side-content conv-list">
          <div v-if="conversations.length === 0" class="conv-empty">Aún no tienes conversaciones.</div>
          <div
            v-for="conv in conversations"
            :key="conv.id"
            :class="['conv-item', { active: conv.id === activeId }]"
            @click="selectConversation(conv.id)"
          >
            <MessageSquare :size="16" class="conv-ic" />
            <span class="conv-title">{{ conv.title || 'Nueva conversación' }}</span>
            <button class="conv-del" title="Eliminar" @click.stop="removeConversation(conv.id)">
              <Trash2 :size="14" />
            </button>
          </div>
        </div>

        <div class="side-header">
          <h3>Sugerencias de Consulta</h3>
        </div>
        <div class="side-content">
          <button class="chip" @click="ask('¿Qué documentos debo llevar al conducir?')">
            <div class="emoji"><FileText :size="22" stroke-width="2.5" /></div>
            <div class="text">
              <b>Documentos</b>
              <span>Obligatorios al conducir</span>
            </div>
          </button>
          <button class="chip" @click="ask('¿Cuál es la multa por manejar sin licencia?')">
            <div class="emoji"><ShieldAlert :size="22" stroke-width="2.5" /></div>
            <div class="text">
              <b>Multas</b>
              <span>Sanciones por infracción</span>
            </div>
          </button>
          <button class="chip" @click="ask('¿Qué tipos de licencia de conducir hay en Guatemala?')">
            <div class="emoji"><Car :size="22" stroke-width="2.5" /></div>
            <div class="text">
              <b>Licencias</b>
              <span>Categorías vehiculares</span>
            </div>
          </button>
          <button class="chip" @click="ask('¿Qué debo hacer si tengo un accidente de tránsito?')">
            <div class="emoji"><AlertTriangle :size="22" stroke-width="2.5" /></div>
            <div class="text">
              <b>Accidentes</b>
              <span>Protocolo de colisión</span>
            </div>
          </button>
        </div>
      </aside>

      <!-- Main Chat Area -->
      <main class="chat-main">
        <div class="mobile-bar">
          <button class="mobile-bar-btn" @click="sidebarOpen = true">
            <PanelLeft :size="18" /> Conversaciones
          </button>
          <button class="mobile-bar-btn" :disabled="busy" @click="newConversation">
            <Plus :size="18" /> Nueva
          </button>
        </div>
        <div class="msgs-wrapper" ref="msgsContainer">
          <div class="chat-date">{{ messages.length ? 'Conversación' : 'Nueva conversación' }}</div>

          <div v-if="messages.length === 0 && !isTyping" class="msg-row bot">
            <div class="msg-av"><BotMessageSquare :size="24" stroke-width="2.5" /></div>
            <div class="msg-bubble">
              ¡Hola! Soy VialBot. Pregúntame lo que quieras sobre la Ley de Tránsito de Guatemala y su Reglamento: multas, licencias, documentos, accidentes o normas de circulación.
            </div>
          </div>

          <div v-for="msg in messages" :key="msg.id" :class="['msg-row', msg.role === 'assistant' ? 'bot' : 'user']">
            <div class="msg-av" v-if="msg.role === 'assistant'"><BotMessageSquare :size="24" stroke-width="2.5" /></div>
            <div class="msg-av" v-else><User :size="24" stroke-width="2.5" /></div>
            <div class="msg-bubble">
              <!-- Texto plano: el contenido nunca se interpreta como HTML -->
              <span class="msg-text">{{ msg.content }}</span>
              <div v-if="msg.sources && msg.sources.length" class="src">
                Fuentes: {{ uniqueReferences(msg.sources).join(' · ') }}
              </div>
            </div>
          </div>
          
          <div v-if="isTyping" class="msg-row bot">
            <div class="msg-av"><BotMessageSquare :size="24" stroke-width="2.5" /></div>
            <div class="msg-bubble typing">
              <span></span><span></span><span></span>
            </div>
          </div>
          
          <div style="height: 40px;"></div> <!-- Spacer -->
        </div>

        <div class="input-area">
          <div class="input-box">
            <input v-model="inputText" maxlength="1000" placeholder="Escribe tu consulta legal sobre tránsito..." @keydown.enter="send">
            <button :disabled="busy || !inputText.trim()" @click="send" class="send-btn">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
            </button>
          </div>
          <div class="disclaimer">VialBot ofrece orientación basada en la Ley de Tránsito y su Reglamento; no sustituye asesoría legal. Verifica información crítica con las autoridades.</div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import NavBar from '../components/NavBar.vue';
import { FileText, ShieldAlert, Car, AlertTriangle, BotMessageSquare, User, Plus, MessageSquare, Trash2, PanelLeft } from '@lucide/vue';
import api from '../services/api';

const conversations = ref([]);
const activeId = ref(null);
const messages = ref([]);
const inputText = ref('');
const busy = ref(false);
const isTyping = ref(false);
const msgsContainer = ref(null);
const sidebarOpen = ref(false);

const scrollBottom = () => {
  nextTick(() => {
    if (msgsContainer.value) {
      msgsContainer.value.scrollTop = msgsContainer.value.scrollHeight;
    }
  });
};

const uniqueReferences = (sources) => [...new Set(sources.map(s => s.reference))];

const loadConversations = async () => {
  const res = await api.get('/chat/conversations');
  conversations.value = res.data;
};

const selectConversation = async (id) => {
  sidebarOpen.value = false;
  activeId.value = id;
  const res = await api.get(`/chat/conversations/${id}/messages`);
  messages.value = res.data;
  scrollBottom();
};

const newConversation = async () => {
  sidebarOpen.value = false;
  // Si la conversación activa está vacía, se reutiliza
  if (activeId.value && messages.value.length === 0) return activeId.value;
  const res = await api.post('/chat/conversations');
  conversations.value.unshift(res.data);
  activeId.value = res.data.id;
  messages.value = [];
  return res.data.id;
};

const removeConversation = async (id) => {
  await api.delete(`/chat/conversations/${id}`);
  conversations.value = conversations.value.filter(c => c.id !== id);
  if (id === activeId.value) {
    activeId.value = null;
    messages.value = [];
    if (conversations.value.length) await selectConversation(conversations.value[0].id);
  }
};

const ask = (q) => {
  sidebarOpen.value = false;
  inputText.value = q;
  send();
};

const send = async () => {
  const q = inputText.value.trim();
  if (!q || busy.value) return;

  busy.value = true;
  inputText.value = '';
  messages.value.push({ id: `tmp-${Date.now()}`, role: 'user', content: q });
  isTyping.value = true;
  scrollBottom();

  try {
    const conversationId = activeId.value ?? await newConversation();
    const res = await api.post(`/chat/conversations/${conversationId}/messages`, { content: q });
    messages.value.push(res.data.reply);
    // El título de la conversación se genera con la primera consulta
    const conv = conversations.value.find(c => c.id === conversationId);
    if (conv && !conv.title) conv.title = q.length > 60 ? q.slice(0, 59) + '…' : q;
  } catch (error) {
    console.error(error);
    messages.value.push({ id: `err-${Date.now()}`, role: 'assistant', content: 'Error de conexión con el servidor. Intenta nuevamente.' });
  } finally {
    isTyping.value = false;
    busy.value = false;
    scrollBottom();
  }
};

onMounted(async () => {
  try {
    await loadConversations();
    if (conversations.value.length) await selectConversation(conversations.value[0].id);
  } catch (error) {
    console.error('Error cargando conversaciones', error);
  }
});
</script>

<style scoped>
.app-layout {
  height: 100vh;
  height: 100dvh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--ink);
}

.chat-container {
  flex: 1;
  display: flex;
  overflow: hidden;
  background: radial-gradient(circle at center 30%, #111a2f 0%, #0b1121 100%);
}

.sidebar {
  width: 320px;
  flex-shrink: 0;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(12px);
  border-right: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  flex-direction: column;
  z-index: 20;
}
.side-header {
  padding: 24px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.side-header h3 {
  font-size: 0.85rem;
  color: var(--txt-dim);
  text-transform: uppercase;
  letter-spacing: 0.15em;
  font-weight: 700;
}
.side-content {
  padding: 20px;
  overflow-y: auto;
}

.chip {
  display: flex; align-items: center; gap: 14px; width: 100%; text-align: left; 
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.02);
  border-radius: 16px; padding: 14px 16px; margin-bottom: 12px; cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); color: var(--txt-main);
}
.chip:hover { border-color: rgba(255,255,255,0.1); background: rgba(255,255,255,0.08); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
.chip .emoji { font-size: 1.2rem; background: rgba(255,255,255,0.05); width: 42px; height: 42px; display: grid; place-items: center; border-radius: 12px; color: var(--amber);}
.chip .text b { display: block; color: #fff; font-size: 0.95rem; font-weight: 600; }
.chip .text span { display: block; color: var(--txt-dim); font-size: 0.8rem; margin-top: 4px;}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
}

.chat-main::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300' viewBox='0 0 300 300'%3E%3Ctext x='30' y='50' font-size='24' opacity='0.06' transform='rotate(15 30 50)'%3E%F0%9F%9A%97%3C/text%3E%3Ctext x='180' y='80' font-size='28' opacity='0.06' transform='rotate(-20 180 80)'%3E%F0%9F%9A%A6%3C/text%3E%3Ctext x='90' y='200' font-size='26' opacity='0.06' transform='rotate(-10 90 200)'%3E%F0%9F%9B%91%3C/text%3E%3Ctext x='240' y='240' font-size='24' opacity='0.06' transform='rotate(25 240 240)'%3E%F0%9F%9A%8C%3C/text%3E%3Ctext x='140' y='140' font-size='22' opacity='0.06' transform='rotate(45 140 140)'%3E%F0%9F%9A%93%3C/text%3E%3Ctext x='30' y='260' font-size='24' opacity='0.06' transform='rotate(-15 30 260)'%3E%E2%9A%A0%EF%B8%8F%3C/text%3E%3Ctext x='260' y='40' font-size='26' opacity='0.06' transform='rotate(5 260 40)'%3E%F0%9F%8E%AB%3C/text%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 300px 300px;
  z-index: 0;
  pointer-events: none;
}

.msgs-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 40px 10%;
  display: flex;
  flex-direction: column;
  gap: 28px;
  scroll-behavior: smooth;
  z-index: 1;
}

.msgs-wrapper::-webkit-scrollbar { width: 8px; }
.msgs-wrapper::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 4px; }

.chat-date { text-align: center; font-size: 0.75rem; color: var(--txt-dim); font-weight: 600; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 0.05em; background: rgba(255,255,255,0.03); padding: 6px 16px; border-radius: 20px; align-self: center; border: 1px solid rgba(255,255,255,0.05);}

.msg-row {
  display: flex;
  gap: 16px;
  max-width: 800px;
  width: 100%;
  margin: 0 auto;
  animation: fadeIn 0.4s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.msg-row.user {
  flex-direction: row-reverse;
}
.msg-av {
  width: 40px; height: 40px; border-radius: 12px;
  display: grid; place-items: center; font-size: 1.2rem; flex-shrink: 0;
  box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}
.msg-row.bot .msg-av {
  background: linear-gradient(135deg, var(--amber), var(--amber-deep)); color: #0a1628;
}
.msg-row.user .msg-av {
  background: rgba(255,255,255,0.05); color: #fff; border: 1px solid rgba(255,255,255,0.1);
}

.msg-bubble {
  padding: 18px 24px;
  font-size: 1.05rem;
  line-height: 1.6;
  border-radius: 24px;
  color: #fff;
  max-width: 85%;
}
.msg-row.user .msg-bubble {
  background: linear-gradient(135deg, #1e293b, #0f172a);
  border: 1px solid rgba(255,255,255,0.05);
  border-top-right-radius: 6px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}
.msg-row.bot .msg-bubble {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-top-left-radius: 6px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.msg-bubble :deep(b) { color: var(--amber); }

.src {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed rgba(255,255,255,0.1);
  font-size: 0.8rem;
  color: var(--teal);
  font-family: 'Space Mono', monospace;
  display: flex;
  align-items: center;
  gap: 6px;
}
.src::before {
  content: "⚡";
  font-size: 0.9rem;
}

.typing { display: flex; gap: 6px; padding: 24px 24px;}
.typing span { width: 8px; height: 8px; border-radius: 50%; background: var(--amber); animation: bounce 1.2s infinite; opacity: 0.7;}
.typing span:nth-child(2){animation-delay:.2s}.typing span:nth-child(3){animation-delay:.4s}

.input-area {
  padding: 24px 10%;
  background: linear-gradient(to top, rgba(11, 17, 33, 1) 50%, rgba(11, 17, 33, 0));
  position: relative;
  z-index: 10;
}
.input-box {
  max-width: 800px;
  margin: 0 auto;
  position: relative;
  display: flex;
  align-items: center;
  background: rgba(30, 41, 59, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 20px;
  padding: 8px 8px 8px 24px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
  transition: border-color 0.3s;
}
.input-box:focus-within {
  border-color: rgba(255,255,255,0.25);
}
.input-box input {
  flex: 1;
  background: transparent;
  border: none;
  padding: 12px 0;
  color: #fff;
  font-family: 'Sora', sans-serif;
  font-size: 1.05rem;
  outline: none;
}
.input-box input::placeholder {
  color: var(--txt-dim);
}
.send-btn {
  background: var(--amber);
  border: none;
  border-radius: 14px;
  width: 48px; height: 48px;
  display: grid; place-items: center;
  cursor: pointer;
  color: #0a1628;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  margin-left: 12px;
}
.send-btn:hover:not(:disabled) { 
  transform: translateY(-2px) scale(1.05); 
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
}
.send-btn:disabled { 
  opacity: 0.3; 
  cursor: not-allowed; 
  background: var(--txt-dim);
}

.disclaimer {
  text-align: center;
  font-size: 0.75rem;
  color: rgba(255,255,255,0.3);
  margin-top: 16px;
  font-weight: 500;
}

/* Conversaciones */
.flex-row { display: flex; align-items: center; justify-content: space-between; }
.new-conv { display: flex; align-items: center; gap: 4px; background: rgba(245, 158, 11, 0.15); color: var(--amber); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 10px; padding: 6px 10px; font-size: 0.8rem; font-weight: 600; cursor: pointer; }
.new-conv:hover:not(:disabled) { background: rgba(245, 158, 11, 0.25); }
.conv-list { max-height: 34vh; overflow-y: auto; gap: 6px; }
.conv-empty { color: var(--txt-dim); font-size: 0.85rem; padding: 4px 2px; }
.conv-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 12px; cursor: pointer; color: var(--txt-dim); border: 1px solid transparent; }
.conv-item:hover { background: rgba(255,255,255,0.04); }
.conv-item.active { background: rgba(255,255,255,0.07); border-color: rgba(255,255,255,0.08); color: #fff; }
.conv-ic { flex-shrink: 0; }
.conv-title { flex: 1; font-size: 0.88rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.conv-del { background: none; border: none; color: var(--txt-dim); cursor: pointer; opacity: 0; padding: 2px; }
.conv-item:hover .conv-del { opacity: 1; }
.conv-del:hover { color: #ef4444; }
.msg-text { white-space: pre-line; }

/* Celular y tableta: la barra lateral se vuelve un panel deslizable */
.mobile-bar, .sidebar-backdrop { display: none; }
@media (max-width: 900px) {
  .sidebar {
    position: fixed; top: 60px; bottom: 0; left: 0;
    width: min(320px, 86vw);
    background: rgba(15, 23, 42, 0.97);
    transform: translateX(-100%);
    transition: transform 0.25s ease;
    z-index: 40;
    overflow-y: auto;
  }
  .sidebar.open { transform: translateX(0); box-shadow: 12px 0 32px rgba(0,0,0,0.5); }
  .sidebar-backdrop { display: block; position: fixed; inset: 60px 0 0 0; background: rgba(0,0,0,0.5); z-index: 30; }
  .conv-del { opacity: 1; }

  .mobile-bar {
    display: flex; justify-content: space-between; gap: 8px;
    padding: 10px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    background: rgba(15, 23, 42, 0.6);
    position: relative; z-index: 2;
  }
  .mobile-bar-btn {
    display: flex; align-items: center; gap: 6px;
    background: rgba(255,255,255,0.05); color: var(--txt-main);
    border: 1px solid rgba(255,255,255,0.1); border-radius: 10px;
    padding: 8px 12px; font-family: 'Sora', sans-serif; font-size: 0.85rem; font-weight: 600; cursor: pointer;
  }
  .mobile-bar-btn:disabled { opacity: 0.5; }

  .msgs-wrapper { padding: 20px 16px; gap: 20px; }
  .input-area { padding: 12px 16px calc(12px + env(safe-area-inset-bottom)); }
}
@media (max-width: 600px) {
  .msg-row { gap: 10px; }
  .msg-av { width: 32px; height: 32px; border-radius: 10px; }
  .msg-av :deep(svg) { width: 18px; height: 18px; }
  .msg-bubble { padding: 12px 16px; font-size: 1rem; max-width: calc(100% - 42px); border-radius: 18px; }
  .chat-date { margin-bottom: 4px; }
  .input-box { padding: 6px 6px 6px 16px; border-radius: 16px; }
  .input-box input { font-size: 16px; min-width: 0; }
  .send-btn { width: 42px; height: 42px; margin-left: 8px; }
  .disclaimer { margin-top: 8px; font-size: 0.68rem; }
}

@keyframes bounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-6px);opacity:1}}
</style>
