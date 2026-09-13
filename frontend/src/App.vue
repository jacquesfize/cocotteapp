<script setup>
import { RouterView } from 'vue-router'
import NavBar from './components/NavBar.vue'
import OfflineIndicator from './components/OfflineIndicator.vue'
</script>

<template>
  <NavBar />
  <OfflineIndicator />
  <main class="container">
    <RouterView />
  </main>
</template>
