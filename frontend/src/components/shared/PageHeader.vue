<script setup lang="ts">
import type { Component } from 'vue'

defineProps<{
  icon: Component
  title?: string
}>()
</script>

<template>
  <h1 class="page-heading">
    <component :is="icon" :size="24" class="page-heading-icon" aria-hidden="true" />
    <span><slot>{{ title }}</slot></span>
  </h1>
</template>

<style scoped>
/* "page-heading", not "page-header": several views already have an unrelated `.row.page-header`
   wrapper (title + action buttons) predating this component — reusing that name here would make
   both elements match a single `.page-header` selector (broke the docs-screenshot Playwright
   suite). */
.page-heading {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.page-heading-icon {
  flex-shrink: 0;
  color: var(--color-primary);
}
</style>
