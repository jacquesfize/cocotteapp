<script setup lang="ts">
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
  <footer class="site-footer">
    <RouterLink :to="{ name: 'legal' }">{{ $t('legal.footerLegal') }}</RouterLink>
    <RouterLink :to="{ name: 'privacy' }">{{ $t('legal.footerPrivacy') }}</RouterLink>
  </footer>
</template>

<style scoped>
.site-footer {
  display: flex;
  justify-content: center;
  gap: 1.25rem;
  padding: 1.5rem 1rem;
  font-size: 0.85rem;
}

.site-footer a {
  color: var(--color-muted);
}
</style>
