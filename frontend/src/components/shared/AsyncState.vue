<script setup lang="ts">
withDefaults(
  defineProps<{
    loading?: boolean
    loadingText?: string
    emptyText?: string
  }>(),
  {
    loading: false,
    loadingText: undefined,
    emptyText: undefined,
  },
)
</script>

<template>
  <p class="muted">{{ loading ? loadingText : emptyText }}</p>
</template>
