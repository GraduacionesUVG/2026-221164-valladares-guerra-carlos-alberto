<template>
  <header class="hero-wrap">
    <div class="hero-text">
      <span class="tag"><span class="dot"></span>Asistente Ciudadano de Guatemala</span>
      <h1>Tus dudas de <span class="hl">tránsito</span>, resueltas al instante.</h1>
      <p class="sub">VialBot GT interpreta tus preguntas en lenguaje cotidiano y te da respuestas claras basadas en la Ley y Reglamento de Tránsito. Sin tecnicismos, rápido y fácil.</p>
      <div class="cta-row">
        <router-link to="/chat" class="btn primary"><MessageSquare :size="18" stroke-width="2.5" /> Hablar con VialBot</router-link>
        <a href="#arq" class="btn ghost">Ver cómo funciona</a>
      </div>
      <div class="stats">
        <div class="stat"><div class="n">132-96</div><div class="l">Base Legal Oficial</div></div>
        <div class="stat"><div class="n">247</div><div class="l">Artículos indexados</div></div>
        <div class="stat"><div class="n">24/7</div><div class="l">Siempre disponible</div></div>
      </div>
    </div>
    <div class="phone">
      <div class="screen">
        <div class="scr-top">
          <div class="av"><BotMessageSquare :size="24" stroke-width="2.5" color="#0a1628" /></div>
          <div class="top-text"><b>VialBot GT</b><br><span>● en línea</span></div>
        </div>
        <div class="scr-body" ref="scrBody"></div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { MessageSquare, BotMessageSquare } from '@lucide/vue';

const scrBody = ref(null);

const scripted = [
  {t:'u',x:'¿De cuánto es la multa por pasarme el semáforo en rojo?'},
  {t:'b',x:'¡Hola! Pasarse el alto es una infracción de tránsito. La multa es de Q.200.00 según el Artículo 181. 👇'},
  {t:'u',x:'¿Y si olvidé mi licencia en casa?'},
  {t:'b',x:'No portar tu licencia al conducir tiene una multa de Q.200.00 (Artículo 181). Siempre debes llevarla contigo.'},
];

let si = 0;
const playPhone = () => {
  if(!scrBody.value) return;
  if(si >= scripted.length) {
    setTimeout(() => {
      if(scrBody.value) scrBody.value.innerHTML = '';
      si = 0;
      playPhone();
    }, 2600);
    return;
  }
  const m = scripted[si];
  const d = document.createElement('div');
  d.className = 'bbl ' + (m.t === 'u' ? 'u' : 'b');
  d.textContent = m.x;
  d.style.animationDelay = '0s';
  scrBody.value.appendChild(d);
  scrBody.value.scrollTop = scrBody.value.scrollHeight;
  si++;
  setTimeout(playPhone, 1800);
};

onMounted(() => {
  playPhone();
});
</script>

<style scoped>
.hero-wrap {
  padding: 30px 6vw 80px; display: grid; grid-template-columns: 1fr 1fr; gap: 60px; align-items: center;
}
@media(max-width:900px){.hero-wrap{grid-template-columns:1fr;padding-top:20px}}

.tag {
  display: inline-flex; align-items: center; gap: 8px; font-weight: 600; font-size: 0.8rem;
  padding: 8px 16px; border-radius: 999px; background: var(--glass); border: 1px solid var(--line); color: var(--txt-main); margin-bottom: 24px;
}
.tag .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--teal); box-shadow: 0 0 12px var(--teal); animation: pulse 2s infinite; }
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}

h1 { font-size: clamp(2.5rem, 5vw, 4rem); line-height: 1.1; font-weight: 800; letter-spacing: -0.04em; color: #fff;}
h1 .hl { background: linear-gradient(135deg, var(--amber), var(--sky)); -webkit-background-clip: text; background-clip: text; color: transparent; }
.sub { margin-top: 24px; color: var(--txt-dim); font-size: 1.15rem; line-height: 1.6; max-width: 520px; }

.cta-row { margin-top: 36px; display: flex; gap: 16px; flex-wrap: wrap; }

.stats { margin-top: 50px; display: flex; gap: 40px; flex-wrap: wrap; }
.stat .n { font-size: 2.2rem; font-weight: 800; letter-spacing: -0.03em; background: linear-gradient(120deg, #fff, var(--sky)); -webkit-background-clip: text; color: transparent; }
.stat .l { font-size: 0.8rem; color: var(--txt-dim); font-weight: 500; margin-top: 4px; }

/* Dark Road Phone */
.phone {
  justify-self: center; width: 320px; height: 640px; border-radius: 42px; padding: 12px;
  background: linear-gradient(160deg, #1b2c4a, #0c1a30); border: 1px solid var(--line);
  box-shadow: 0 40px 90px rgba(0,0,0,0.55), inset 0 0 0 1px rgba(255,255,255,0.04); position: relative;
  animation: float 6s ease-in-out infinite;
}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}
.phone::before { content:""; position: absolute; top: 22px; left: 50%; transform: translateX(-50%); width: 80px; height: 6px; border-radius: 99px; background: #0a1628; z-index:10;}

.screen { height: 100%; border-radius: 30px; background: var(--ink); overflow: hidden; display: flex; flex-direction: column; position:relative;}
.screen::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300' viewBox='0 0 300 300'%3E%3Ctext x='30' y='50' font-size='24' opacity='0.06' transform='rotate(15 30 50)'%3E%F0%9F%9A%97%3C/text%3E%3Ctext x='180' y='80' font-size='28' opacity='0.06' transform='rotate(-20 180 80)'%3E%F0%9F%9A%A6%3C/text%3E%3Ctext x='90' y='200' font-size='26' opacity='0.06' transform='rotate(-10 90 200)'%3E%F0%9F%9B%91%3C/text%3E%3Ctext x='240' y='240' font-size='24' opacity='0.06' transform='rotate(25 240 240)'%3E%F0%9F%9A%8C%3C/text%3E%3Ctext x='140' y='140' font-size='22' opacity='0.06' transform='rotate(45 140 140)'%3E%F0%9F%9A%93%3C/text%3E%3Ctext x='30' y='260' font-size='24' opacity='0.06' transform='rotate(-15 30 260)'%3E%E2%9A%A0%EF%B8%8F%3C/text%3E%3Ctext x='260' y='40' font-size='26' opacity='0.06' transform='rotate(5 260 40)'%3E%F0%9F%8E%AB%3C/text%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 300px 300px;
  z-index: 0;
  pointer-events: none;
}
.scr-top {
  padding: 38px 20px 16px; background: linear-gradient(180deg, #13243f, transparent);
  display: flex; align-items: center; gap: 12px; border-bottom: 1px solid var(--line); position: relative; z-index: 5;
}
.scr-top .av { width: 40px; height: 40px; border-radius: 12px; background: linear-gradient(135deg, var(--amber), var(--amber-deep)); display: grid; place-items: center; color: #0a1628; font-size: 1.2rem; font-weight: 800;}
.top-text b { font-size: 0.9rem; color: #fff;}
.top-text span { font-size: 0.7rem; color: var(--teal); font-weight: 600;}

.scr-body { flex: 1; padding: 20px 16px; display: flex; flex-direction: column; gap: 12px; overflow-y: auto; position: relative; z-index: 1; }

:deep(.bbl) {
  max-width: 85%; padding: 12px 16px; border-radius: 18px; font-size: 0.85rem; line-height: 1.5; opacity: 0; transform: translateY(10px); animation: rise 0.4s forwards cubic-bezier(0.2, 0.8, 0.2, 1);
}
:deep(.bbl.u) { align-self: flex-end; background: linear-gradient(135deg, var(--amber), var(--amber-deep)); color: #0a1628; border-bottom-right-radius: 4px; font-weight: 600;}
:deep(.bbl.b) { align-self: flex-start; background: var(--glass); color: #fff; border: 1px solid var(--line); border-bottom-left-radius: 4px; }
@keyframes rise{to{opacity:1;transform:translateY(0)}}
</style>
