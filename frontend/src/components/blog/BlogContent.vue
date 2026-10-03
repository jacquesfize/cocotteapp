<script setup lang="ts">
import { ref } from 'vue'
import { useEmbedAutoHeight } from '../../composables/useEmbedAutoHeight'

// `html` comes from the API, where it is sanitized on save (apps/blog/sanitize.py): the only
// iframes it can contain point at our own /embed/recipes/:id view.
defineProps<{
  html: string
}>()

const root = ref<HTMLElement | null>(null)
useEmbedAutoHeight(root)
</script>

<template>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <div ref="root" class="blog-prose" v-html="html" />
</template>
