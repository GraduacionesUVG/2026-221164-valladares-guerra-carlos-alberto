<template>
  <footer>
    <div class="brand">
      <div class="sig"><BotMessageSquare :size="20" /></div>
      <div>VialBot GT</div>
    </div>
    <div>Asistente Conversacional Inteligente para Gestión de Consultas de Tránsito y Educación Vial · Guatemala</div>
    <div style="margin-top:6px">Universidad del Valle de Guatemala · Carlos Valladares · Prototipo visual 2026</div>
    <div class="warn">
      <AlertTriangle :size="16" style="display:inline-block; vertical-align:middle; margin-bottom:2px; margin-right:4px;" />
      Demostración académica. Las respuestas son generadas con fines ilustrativos y no constituyen asesoría legal oficial. Para trámites reales consulte siempre fuentes oficiales del Departamento de Tránsito de la PNC.
    </div>
  </footer>
</template>

<script setup>
import { BotMessageSquare, AlertTriangle } from '@lucide/vue';
</script>
