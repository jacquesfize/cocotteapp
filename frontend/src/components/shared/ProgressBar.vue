<script setup lang="ts">
withDefaults(
  defineProps<{
    percent: number
    height?: string
    trackColor?: string
    maxWidth?: string
    transition?: boolean
  }>(),
  {
    height: '0.4rem',
    trackColor: 'var(--color-surface-muted)',
    maxWidth: undefined,
    transition: true,
  },
)
</script>

<template>
  <div
    class="progress-bar-track"
    :style="{ height, background: trackColor, maxWidth }"
  >
    <div
      class="progress-bar-fill"
      :class="{ 'progress-bar-fill--animated': transition }"
      :style="{ width: `${percent}%` }"
    />
  </div>
</template>

<style scoped>
.progress-bar-track {
  width: 100%;
  border-radius: var(--radius-pill);
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: var(--radius-pill);
}

.progress-bar-fill--animated {
  transition: width 0.2s ease;
}
</style>
