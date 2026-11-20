<template>
  <nav>
    <router-link to="/" class="brand">
      <div class="sig"><BotMessageSquare :size="16" stroke-width="2.5" /></div>
      <div>VialBot GT<small>Asistente de Tránsito</small></div>
    </router-link>

    <div class="nav-links">
      <router-link to="/">Inicio</router-link>
      <router-link v-if="authStore.isAuthenticated" to="/chat">Chat</router-link>
      <router-link v-if="authStore.isAdmin" to="/dashboard">Dashboard</router-link>
    </div>

    <div class="nav-actions" style="display: flex; gap: 12px; align-items: center;">
      <router-link v-if="!authStore.isAuthenticated" to="/auth/login" class="btn primary" style="padding: 8px 18px; font-size: 0.85rem;">Iniciar Sesión</router-link>
      <button v-else @click="handleLogout" class="btn ghost" style="padding: 8px 18px; font-size: 0.85rem;">Cerrar Sesión</button>
    </div>

    <!-- Menú para pantallas angostas -->
    <button class="nav-toggle" :aria-expanded="menuOpen" aria-label="Abrir menú" @click="menuOpen = !menuOpen">
      <X v-if="menuOpen" :size="22" />
      <Menu v-else :size="22" />
    </button>
    <div v-if="menuOpen" class="nav-mobile" @click="menuOpen = false">
      <router-link to="/">Inicio</router-link>
      <router-link v-if="authStore.isAuthenticated" to="/chat">Chat</router-link>
      <router-link v-if="authStore.isAdmin" to="/dashboard">Dashboard</router-link>
      <router-link v-if="!authStore.isAuthenticated" to="/auth/login" class="btn primary">Iniciar Sesión</router-link>
      <button v-else @click="handleLogout" class="btn ghost">Cerrar Sesión</button>
    </div>
  </nav>
</template>

<script setup>
import { ref } from 'vue';
import { BotMessageSquare, Menu, X } from '@lucide/vue';
import { useAuthStore } from '../stores/authStore';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();
const menuOpen = ref(false);

const handleLogout = () => {
  authStore.logout();
  router.push('/auth/login');
};
</script>
