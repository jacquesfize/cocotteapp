<script setup lang="ts">
import { X } from '@lucide/vue'
import { onBeforeUnmount, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

defineProps<{ title: string }>()
const emit = defineEmits<{ close: [] }>()
const { t } = useI18n()

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') emit('close')
}

onMounted(() => window.addEventListener('keydown', handleKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', handleKeydown))
</script>

<template>
  <div class="base-modal-overlay" @mousedown.self="emit('close')">
    <div class="card base-modal" role="dialog" aria-modal="true" :aria-label="title">
      <div class="row base-modal-header">
        <h2>{{ title }}</h2>
        <button
          type="button"
          class="secondary icon-btn base-modal-close"
          :aria-label="t('common.close')"
          @click="emit('close')"
        >
          <X :size="16" />
        </button>
      </div>
      <slot />
    </div>
  </div>
</template>

<style scoped>
.base-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  background: rgba(36, 31, 29, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.base-modal {
  width: 100%;
  max-width: 520px;
  max-height: 90vh;
  overflow-y: auto;
}

.base-modal-header {
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.base-modal-header h2 {
  margin: 0;
}
</style>
