<template>
  <section id="arq">
    <div class="eyebrow">¿Cómo funciona?</div>
    <div class="h2">Inteligencia Artificial fácil de entender</div>
    <p class="lead">No usamos respuestas pregrabadas. VialBot analiza tu pregunta, busca en el reglamento oficial, y redacta una respuesta personalizada al instante.</p>
    
    <div class="flow">
      <div class="node">
        <div class="ic"><Smartphone :size="32" stroke-width="2" /></div><h4>1. Preguntas</h4>
        <p>Escribes tu duda como si le hablaras a un amigo, sin usar palabras difíciles.</p>
      </div>
      <div class="node">
        <div class="ic"><BrainCircuit :size="32" stroke-width="2" /></div><h4>2. El Bot Entiende</h4>
        <p>Nuestro modelo entiende tu forma de hablar y detecta qué tema de tránsito necesitas.</p>
      </div>
      <div class="node">
        <div class="ic"><BookOpenText :size="32" stroke-width="2" /></div><h4>3. Busca en la Ley</h4>
        <p>Busca entre los 247 artículos de la Ley de Tránsito y su Reglamento en milisegundos.</p>
      </div>
      <div class="node">
        <div class="ic"><Sparkles :size="32" stroke-width="2" /></div><h4>4. Te Responde</h4>
        <p>Te da una respuesta clara, amable y te dice en qué artículo se basó.</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { Smartphone, BrainCircuit, BookOpenText, Sparkles } from '@lucide/vue';
// ArchitectureFlow component
</script>

<style scoped>
.flow {
  margin-top: 50px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px;
}
@media(max-width:900px){.flow{grid-template-columns:1fr 1fr;}}
@media(max-width:500px){.flow{grid-template-columns:1fr;}}

.node {
  background: var(--glass); border: 1px solid var(--line); border-radius: 24px; padding: 30px 24px; position: relative; transition: all 0.3s ease;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}
.node .ic { font-size: 2.5rem; margin-bottom: 16px; background: rgba(255,255,255,0.05); width: 64px; height: 64px; display: grid; place-items: center; border-radius: 20px; border: 1px solid var(--line); transition: all 0.3s ease;}
.node h4 { font-size: 1.1rem; font-weight: 700; margin-bottom: 8px; color: #fff;}
.node p { font-size: 0.9rem; color: var(--txt-dim); line-height: 1.6; }

/* Colores dinámicos por paso - Más intensos */
.node:nth-child(1) { background: linear-gradient(145deg, rgba(59, 130, 246, 0.25), var(--glass)); border-color: rgba(59, 130, 246, 0.4); }
.node:nth-child(1) .ic { color: #60a5fa; border-color: rgba(59, 130, 246, 0.5); background: rgba(59, 130, 246, 0.2); }
.node:nth-child(1):hover { border-color: #60a5fa; box-shadow: 0 20px 40px rgba(59, 130, 246, 0.3); transform: translateY(-8px); }

.node:nth-child(2) { background: linear-gradient(145deg, rgba(168, 85, 247, 0.25), var(--glass)); border-color: rgba(168, 85, 247, 0.4); }
.node:nth-child(2) .ic { color: #c084fc; border-color: rgba(168, 85, 247, 0.5); background: rgba(168, 85, 247, 0.2); }
.node:nth-child(2):hover { border-color: #c084fc; box-shadow: 0 20px 40px rgba(168, 85, 247, 0.3); transform: translateY(-8px); }

.node:nth-child(3) { background: linear-gradient(145deg, rgba(245, 158, 11, 0.25), var(--glass)); border-color: rgba(245, 158, 11, 0.4); }
.node:nth-child(3) .ic { color: #fbbf24; border-color: rgba(245, 158, 11, 0.5); background: rgba(245, 158, 11, 0.2); }
.node:nth-child(3):hover { border-color: #fbbf24; box-shadow: 0 20px 40px rgba(245, 158, 11, 0.3); transform: translateY(-8px); }

.node:nth-child(4) { background: linear-gradient(145deg, rgba(16, 185, 129, 0.25), var(--glass)); border-color: rgba(16, 185, 129, 0.4); }
.node:nth-child(4) .ic { color: #34d399; border-color: rgba(16, 185, 129, 0.5); background: rgba(16, 185, 129, 0.2); }
.node:nth-child(4):hover { border-color: #34d399; box-shadow: 0 20px 40px rgba(16, 185, 129, 0.3); transform: translateY(-8px); }

.node::after { content: "→"; position: absolute; right: -18px; top: 50%; transform: translateY(-50%); color: var(--amber); font-size: 1.5rem; z-index: 3; font-weight: 800;}
.node:last-child::after { display: none; }
@media(max-width:900px){.node::after{display:none}}
</style>
