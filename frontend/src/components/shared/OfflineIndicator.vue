<script setup lang="ts">
import { WifiOff } from '@lucide/vue'
import { onBeforeUnmount, onMounted, ref } from 'vue'

const isOffline = ref(!navigator.onLine)

function updateStatus() {
  isOffline.value = !navigator.onLine
}

onMounted(() => {
  window.addEventListener('online', updateStatus)
  window.addEventListener('offline', updateStatus)
})

onBeforeUnmount(() => {
  window.removeEventListener('online', updateStatus)
  window.removeEventListener('offline', updateStatus)
})
</script>

<template>
  <div v-if="isOffline" class="offline-banner" role="status">
    <WifiOff :size="16" />
    <span>{{ $t('offline.banner') }}</span>
  </div>
</template>

<style scoped>
.offline-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
  font-size: 0.85rem;
  font-weight: 600;
  padding: 0.5rem 1rem;
  text-align: center;
}
</style>
