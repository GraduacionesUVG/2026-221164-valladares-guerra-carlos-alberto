<template>
  <BackgroundHighway v-if="['/', '/auth/login', '/auth/signup'].includes(route.path)" />
  <router-view></router-view>
</template>

<script setup>
import { useRoute } from 'vue-router';
import BackgroundHighway from './components/BackgroundHighway.vue';

const route = useRoute();
</script>

<style>
/* Sin transiciones feas que rompen el layout */
</style>
