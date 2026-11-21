<template>
  <div class="road-dashes"></div>

  <div class="content page-wrap">
    <NavBar />
    
    <div class="main-content">
      <HeroSection />
      <ArchitectureFlow />
    </div>

    <Footer />
  </div>
</template>

<script setup>
import NavBar from '../components/NavBar.vue';
import HeroSection from '../components/HeroSection.vue';
import ArchitectureFlow from '../components/ArchitectureFlow.vue';
import Footer from '../components/Footer.vue';
</script>

<style scoped>
.page-wrap {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.main-content {
  flex: 1;
}
</style>
