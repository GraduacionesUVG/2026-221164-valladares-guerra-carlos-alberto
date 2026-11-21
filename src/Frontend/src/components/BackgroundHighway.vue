<template>
  <div class="highway-bg">
    <!-- Grid sutil para dar perspectiva -->
    <div class="grid-ground"></div>
    
    <!-- Centro de carretera y carriles -->
    <div class="road-surface"></div>
    <div class="road-center"></div>
    <div class="lane-divider-left"></div>
    <div class="lane-divider-right"></div>

    <!-- Centro de carretera y carriles -->
    <div class="road-surface"></div>
    <div class="road-center"></div>
    <div class="lane-divider-left"></div>
    <div class="lane-divider-right"></div>

    <!-- Intersección y Pasos de Cebra Peatonales (4 vías) -->
    <div class="intersection"></div>
    <div class="crosswalk-left"></div>
    <div class="crosswalk-right"></div>
    <div class="crosswalk-top"></div>
    <div class="crosswalk-bottom"></div>

    <!-- Peatones Inteligentes -->
    <div v-for="p in pedestrians" :key="p.id"
         class="pedestrian"
         :style="{ transform: `translate3d(${p.x}px, ${p.y}vh, 0)`, background: p.color }">
    </div>

    <!-- Semáforos Individuales -->
    <!-- Semáforo Vertical Down -->
    <div class="traffic-light vertical-down">
      <div class="light-bulb red" :class="{ active: vLight === 'red' }"></div>
      <div class="light-bulb yellow" :class="{ active: vLight === 'yellow' }"></div>
      <div class="light-bulb green" :class="{ active: vLight === 'green' }"></div>
    </div>
    
    <!-- Semáforo Vertical Up -->
    <div class="traffic-light vertical-up">
      <div class="light-bulb red" :class="{ active: vLight === 'red' }"></div>
      <div class="light-bulb yellow" :class="{ active: vLight === 'yellow' }"></div>
      <div class="light-bulb green" :class="{ active: vLight === 'green' }"></div>
    </div>

    <!-- Semáforo Transversal -->
    <div class="traffic-light transversal">
      <div class="light-bulb red" :class="{ active: tLight === 'red' }"></div>
      <div class="light-bulb yellow" :class="{ active: tLight === 'yellow' }"></div>
      <div class="light-bulb green" :class="{ active: tLight === 'green' }"></div>
    </div>

    <!-- Bus Transversal Inteligente -->
    <div class="bus" :style="{ transform: `translate3d(${busX}px, 0, 0)` }"></div>

    <!-- Motor de Físicas: Autos Bajando -->
    <div v-for="car in downCars" :key="car.id" 
         class="car down" 
         :style="{ transform: `translate3d(0, ${car.y}vh, 0)`, left: car.x, background: car.color, height: car.height + 'px' }">
    </div>

    <!-- Motor de Físicas: Autos Subiendo -->
    <div v-for="car in upCars" :key="car.id" 
         class="car up" 
         :style="{ transform: `translate3d(0, ${car.y}vh, 0)`, left: car.x, background: car.color, height: car.height + 'px', border: car.color === '#1a1a1a' ? '1px solid #333' : 'none' }">
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const vLight = ref('green'); 
const tLight = ref('red'); 
const busX = ref(-1200); 
const downCars = ref([]);
const upCars = ref([]);
const pedestrians = ref([]);

const L1_X = 'calc(50% - 38px)';
const L2_X = 'calc(50% - 68px)';
const R1_X = 'calc(50% + 22px)';
const R2_X = 'calc(50% + 52px)';

const DOWN_COLORS = ['#ff3333', '#cc0000', '#0066ff'];
const UP_COLORS = ['#ffffff', '#1a1a1a', '#aaddff'];

let reqId;
let lightTimer = 0;
let lastTime = performance.now();

let busSpeed = 7;
const busMaxSpeed = 7;
const busAccel = 0.1;
const busDecel = 0.3;

function initCars() {
  for (let l = 1; l <= 2; l++) {
     let y = -20;
     for (let i=0; i<6; i++) {
        downCars.value.push({
           id: `d${l}-${i}`, lane: l, y, speed: 0.3,
           maxSpeed: 0.25 + Math.random() * 0.2,
           accel: 0.002 + Math.random() * 0.002, decel: 0.015,
           color: DOWN_COLORS[Math.floor(Math.random()*DOWN_COLORS.length)],
           height: 35 + Math.random() * 15, x: l === 1 ? L1_X : L2_X
        });
        y -= (15 + Math.random() * 40); // Espaciado inicial orgánico
     }
  }
  for (let l = 1; l <= 2; l++) {
     let y = 120;
     for (let i=0; i<6; i++) {
        upCars.value.push({
           id: `u${l}-${i}`, lane: l, y, speed: 0.3,
           maxSpeed: 0.25 + Math.random() * 0.2,
           accel: 0.002 + Math.random() * 0.002, decel: 0.015,
           color: UP_COLORS[Math.floor(Math.random()*UP_COLORS.length)],
           height: 35 + Math.random() * 15, x: l === 1 ? R1_X : R2_X
        });
        y += (15 + Math.random() * 40);
     }
  }
}

function initPedestrians() {
   pedestrians.value = [];
   // Peatones Verticales
   for(let i=0; i<6; i++) {
       let isLeft = Math.random() > 0.5;
       let isDown = Math.random() > 0.5;
       pedestrians.value.push({
          id: `pv-${i}`, axis: 'y', dir: isDown ? 1 : -1,
          x: isLeft ? -115 + Math.random() * 10 : 105 + Math.random() * 10,
          y: isDown ? -10 - Math.random() * 50 : 110 + Math.random() * 50,
          speed: 0.1 + Math.random() * 0.05, 
          color: ['#aaaaaa', '#ffffff', '#888888', '#cccccc'][Math.floor(Math.random()*4)]
       });
   }
   // Peatones Horizontales
   for(let i=0; i<6; i++) {
       let isTop = Math.random() > 0.5;
       let isRight = Math.random() > 0.5;
       pedestrians.value.push({
          id: `ph-${i}`, axis: 'x', dir: isRight ? 1 : -1,
          x: isRight ? -250 - Math.random() * 150 : 250 + Math.random() * 150,
          y: isTop ? 42 + Math.random() * 2 : 57 + Math.random() * 2,
          speed: 1.0 + Math.random() * 0.5, 
          color: ['#aaaaaa', '#ffffff', '#888888', '#cccccc'][Math.floor(Math.random()*4)]
       });
   }
}

function updateLight(dt) {
  lightTimer += dt;
  if (lightTimer > 16000) lightTimer -= 16000;
  
  // Ciclo perfecto de 16 segundos para sincronización global
  if (lightTimer < 6000) {
     vLight.value = 'green';
     tLight.value = 'red';
  }
  else if (lightTimer < 8000) {
     vLight.value = 'yellow';
     tLight.value = 'red';
  }
  else if (lightTimer < 14000) {
     vLight.value = 'red';
     tLight.value = 'green';
  }
  else {
     vLight.value = 'red';
     tLight.value = 'yellow';
  }
}

function updateBus(f) {
  let targetStop = 2000; 
  
  // Frena si el semáforo transversal NO es verde (y aún no cruza)
  let stopLine = -275;
  if (tLight.value !== 'green' && busX.value < stopLine) {
     // Zona de dilema: si está en amarillo y a menos de 200px, cruza
     if (!(tLight.value === 'yellow' && stopLine - busX.value < 200)) {
         targetStop = stopLine; // Frena ANTES del paso peatonal izquierdo
     }
  }
  
  let distToStop = targetStop - busX.value;
  let idealSpeed = busMaxSpeed;
  
  if (distToStop < 400) { 
     idealSpeed = (distToStop - 10) * 0.05; 
     if (idealSpeed < 0) idealSpeed = 0;
  }

  if (busSpeed > idealSpeed) {
     busSpeed -= busDecel * f;
     if (busSpeed < idealSpeed) busSpeed = idealSpeed;
  } else {
     busSpeed += busAccel * f;
     if (busSpeed > idealSpeed) busSpeed = idealSpeed;
  }
  
  busX.value += busSpeed * f;
  
  // Reaparecer lejos para el siguiente ciclo
  if (busX.value > 1500) {
     busX.value = -1200 - (Math.random() * 500);
     busSpeed = busMaxSpeed;
  }
}

function updatePedestrians(f) {
   pedestrians.value.forEach(p => {
       let canWalk = true;
       let currentSpeed = p.speed;

       if (p.axis === 'y') {
           const isCrossing = p.y > 45 && p.y < 55;
           if (tLight.value !== 'red') {
               if (isCrossing) currentSpeed = p.speed * 1.5; 
               else {
                   if (p.dir === 1 && p.y > 43 && p.y < 45) { canWalk = false; p.y = 43; } 
                   else if (p.dir === -1 && p.y < 57 && p.y > 55) { canWalk = false; p.y = 57; }
               }
           }
           if (canWalk) p.y += p.dir * currentSpeed * f;
           if (p.y > 120) { p.y = -10 - Math.random() * 30; p.dir = 1; } 
           else if (p.y < -20) { p.y = 110 + Math.random() * 30; p.dir = -1; }
       } else {
           const isCrossing = p.x > -100 && p.x < 100;
           if (vLight.value !== 'red') {
               if (isCrossing) currentSpeed = p.speed * 1.5; 
               else {
                   if (p.dir === 1 && p.x > -120 && p.x < -100) { canWalk = false; p.x = -120; } 
                   else if (p.dir === -1 && p.x < 120 && p.x > 100) { canWalk = false; p.x = 120; }
               }
           }
           if (canWalk) p.x += p.dir * currentSpeed * f;
           if (p.x > 400) { p.x = -200 - Math.random() * 100; p.dir = 1; } 
           else if (p.x < -400) { p.x = 200 + Math.random() * 100; p.dir = -1; }
       }
   });
}

function updatePhysics() {
  let now = performance.now();
  let dt = now - lastTime;
  // Prevenir saltos gigantes si el tab se minimiza
  if (dt > 100) dt = 16; 
  lastTime = now;
  
  const f = dt / 16; 
  
  updateLight(dt);
  updateBus(f);
  updatePedestrians(f);

  // ACTUALIZAR AUTOS BAJANDO
  [1, 2].forEach(lane => {
    let cars = downCars.value.filter(c => c.lane === lane).sort((a,b) => b.y - a.y);
    for (let i = 0; i < cars.length; i++) {
      let car = cars[i];
      let targetStop = 300; // No hay tope por defecto
      
      // Semáforo con Zona de Dilema
      let stopLine = 36;
      if (vLight.value !== 'green' && car.y < stopLine) {
        if (!(vLight.value === 'yellow' && stopLine - car.y < 15)) {
           targetStop = stopLine;
        }
      }
      
      // Auto de enfrente
      if (i > 0) {
        let carAhead = cars[i-1];
        let stopBehindAhead = carAhead.y - 7; // Distancia de seguridad de 7vh
        if (stopBehindAhead < targetStop) {
          targetStop = stopBehindAhead;
        }
      }
      
      let distToStop = targetStop - car.y;
      let idealSpeed = car.maxSpeed;
      
      if (distToStop < 25) { 
         idealSpeed = (distToStop - 2) * 0.04; 
         if (idealSpeed < 0) idealSpeed = 0;
      }

      if (car.speed > idealSpeed) {
         car.speed -= car.decel * f;
         if (car.speed < idealSpeed) car.speed = idealSpeed;
      } else {
         car.speed += car.accel * f;
         if (car.speed > idealSpeed) car.speed = idealSpeed;
      }
      
      car.y += car.speed * f;
      
      // Reaparición dinámica infinita
      if (car.y > 130) {
         let minY = -20;
         cars.forEach(c => { if(c.y < minY) minY = c.y; });
         car.y = minY - (25 + Math.random() * 50); // Cola infinita aleatoria
         car.speed = car.maxSpeed;
      }
    }
  });

  // ACTUALIZAR AUTOS SUBIENDO
  [1, 2].forEach(lane => {
    let cars = upCars.value.filter(c => c.lane === lane).sort((a,b) => a.y - b.y);
    for (let i = 0; i < cars.length; i++) {
      let car = cars[i];
      let targetStop = -300;
      
      // Semáforo con Zona de Dilema
      let stopLine = 60;
      if (vLight.value !== 'green' && car.y > stopLine) {
        if (!(vLight.value === 'yellow' && car.y - stopLine < 15)) {
           targetStop = stopLine;
        }
      }
      
      // Auto de enfrente
      if (i > 0) {
        let carAhead = cars[i-1];
        let stopBehindAhead = carAhead.y + 7; 
        if (stopBehindAhead > targetStop) {
          targetStop = stopBehindAhead;
        }
      }
      
      let distToStop = car.y - targetStop;
      let idealSpeed = car.maxSpeed;
      
      if (distToStop < 25) { 
         idealSpeed = (distToStop - 2) * 0.04; 
         if (idealSpeed < 0) idealSpeed = 0;
      }

      if (car.speed > idealSpeed) {
         car.speed -= car.decel * f;
         if (car.speed < idealSpeed) car.speed = idealSpeed;
      } else {
         car.speed += car.accel * f;
         if (car.speed > idealSpeed) car.speed = idealSpeed;
      }
      
      car.y -= car.speed * f;
      
      if (car.y < -30) {
         let maxY = 130;
         cars.forEach(c => { if(c.y > maxY) maxY = c.y; });
         car.y = maxY + (25 + Math.random() * 50);
         car.speed = car.maxSpeed;
      }
    }
  });

  reqId = requestAnimationFrame(updatePhysics);
}

onMounted(() => {
  initCars();
  initPedestrians();
  lastTime = performance.now();
  reqId = requestAnimationFrame(updatePhysics);
});

onUnmounted(() => {
  cancelAnimationFrame(reqId);
});
</script>

<style scoped>
.highway-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: #0b1120;
  overflow: hidden;
}

.grid-ground {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(circle at 50% 50%, #000, transparent 70%);
  -webkit-mask-image: radial-gradient(circle at 50% 50%, #000, transparent 70%);
}

.road-surface {
  position: absolute;
  left: calc(50% - 85px);
  width: 170px;
  top: 0; bottom: 0;
  background: rgba(255, 255, 255, 0.015);
  border-left: 2px solid rgba(255,255,255,0.05);
  border-right: 2px solid rgba(255,255,255,0.05);
}

.road-center {
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 4px;
  transform: translateX(-50%);
  background: repeating-linear-gradient(to bottom, rgba(255,199,58,0.5) 0 30px, transparent 30px 70px);
}

.lane-divider-left {
  position: absolute;
  left: calc(50% - 45px);
  top: 0; bottom: 0;
  width: 2px;
  background: repeating-linear-gradient(to bottom, rgba(255,255,255,0.15) 0 20px, transparent 20px 40px);
}

.lane-divider-right {
  position: absolute;
  left: calc(50% + 45px);
  top: 0; bottom: 0;
  width: 2px;
  background: repeating-linear-gradient(to bottom, rgba(255,255,255,0.15) 0 20px, transparent 20px 40px);
}

.intersection {
  position: absolute;
  top: 45vh;
  left: 0;
  right: 0;
  height: 10vh;
  background: rgba(255,255,255,0.02);
  border-top: 2px dashed rgba(255,255,255,0.15);
  border-bottom: 2px dashed rgba(255,255,255,0.15);
  z-index: 1;
}
.crosswalk-left {
  position: absolute;
  top: 45vh;
  left: calc(50% - 130px);
  width: 30px;
  height: 10vh;
  background: repeating-linear-gradient(0deg, rgba(255,255,255,0.15) 0 10px, transparent 10px 20px);
  z-index: 2;
}
.crosswalk-right {
  position: absolute;
  top: 45vh;
  left: calc(50% + 100px);
  width: 30px;
  height: 10vh;
  background: repeating-linear-gradient(0deg, rgba(255,255,255,0.15) 0 10px, transparent 10px 20px);
  z-index: 2;
}
.crosswalk-top {
  position: absolute;
  top: 41.5vh;
  left: calc(50% - 100px);
  width: 200px;
  height: 3.5vh;
  background: repeating-linear-gradient(90deg, rgba(255,255,255,0.15) 0 10px, transparent 10px 20px);
  z-index: 2;
}
.crosswalk-bottom {
  position: absolute;
  top: 56.5vh;
  left: calc(50% - 100px);
  width: 200px;
  height: 3.5vh;
  background: repeating-linear-gradient(90deg, rgba(255,255,255,0.15) 0 10px, transparent 10px 20px);
  z-index: 2;
}

/* Semáforos Inteligentes Individuales */
.traffic-light {
  position: absolute;
  width: 14px;
  height: 40px;
  background: #111;
  border-radius: 6px;
  border: 1px solid #333;
  z-index: 20;
  display: flex;
  flex-direction: column;
  justify-content: space-around;
  align-items: center;
  padding: 4px 0;
  box-shadow: 0 5px 15px rgba(0,0,0,0.5);
}
.traffic-light.vertical-down {
  left: calc(50% - 120px); 
  top: 39vh;
}
.traffic-light.vertical-up {
  left: calc(50% + 100px); 
  top: 59vh;
}
.traffic-light.transversal {
  left: calc(50% - 135px); 
  top: calc(47vh + 35px); 
  transform: rotate(-90deg);
}
.light-bulb {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #333;
  transition: 0.2s;
}
.light-bulb.red.active { background: #ff0000; box-shadow: 0 0 20px #ff0000; }
.light-bulb.yellow.active { background: #ffaa00; box-shadow: 0 0 15px #ffaa00; }
.light-bulb.green.active { background: #00ff00; box-shadow: 0 0 15px #00ff00; }

/* Bus Transversal Reactivo */
.bus {
  position: absolute;
  top: 47vh;
  left: 50%;
  width: 140px;
  height: 32px;
  background: #2563eb;
  border-radius: 10px;
  box-shadow: 0 15px 30px rgba(37, 99, 235, 0.6);
  z-index: 15;
  will-change: transform;
}
.bus::after {
  content: "";
  position: absolute;
  top: 6px; left: 12px; right: 12px; bottom: 6px;
  background: repeating-linear-gradient(90deg, #93c5fd 0 15px, transparent 15px 20px);
  border-radius: 4px;
}

/* Vehículos (Controlados por Motor JS) */
.car {
  position: absolute;
  top: 0;
  width: 16px;
  border-radius: 8px;
  z-index: 10;
  will-change: transform;
  /* Box-shadow global para que brillen */
  box-shadow: 0 5px 20px rgba(255,255,255,0.4);
}
/* Efectos de luz según dirección */
.car.down { box-shadow: 0 -10px 20px rgba(255,0,0,0.6); }
.car.up { box-shadow: 0 10px 20px rgba(255,255,255,0.6); }

/* Peatones */
.pedestrian {
  position: absolute;
  left: 50%;
  top: 0;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  z-index: 12;
  will-change: transform;
  box-shadow: 0 0 5px rgba(255,255,255,0.5);
}
</style>
