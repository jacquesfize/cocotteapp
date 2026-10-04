<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'
import AnnouncementBanner from './components/shared/AnnouncementBanner.vue'
import NavBar from './components/shared/NavBar.vue'
import OfflineIndicator from './components/shared/OfflineIndicator.vue'

const route = useRoute()
</script>

<template>
  <RouterView v-if="route.meta.embed" />
  <template v-else>
    <NavBar />
    <AnnouncementBanner />
    <OfflineIndicator />
    <main class="container">
      <RouterView />
    </main>
    <footer class="site-footer">
      <RouterLink :to="{ name: 'legal' }">{{ $t('legal.footerLegal') }}</RouterLink>
      <RouterLink :to="{ name: 'privacy' }">{{ $t('legal.footerPrivacy') }}</RouterLink>
    </footer>
  </template>
</template>

<style scoped>
.site-footer {
  display: flex;
  justify-content: center;
  gap: 1.25rem;
  padding: 1.5rem 1rem;
  font-size: 0.85rem;
}

@media (max-width: 600px) {
  /* The mobile tab bar is fixed to the viewport bottom (see NavBar.vue's .tabbar) and would
     otherwise cover the footer, same reason .container reserves this much space above it. */
  .site-footer {
    padding-bottom: calc(5.5rem + env(safe-area-inset-bottom, 0px));
  }
}

.site-footer a {
  color: var(--color-muted);
}
</style>
