<script setup lang="ts">
import { Clock, Users, Utensils } from '@lucide/vue'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { getRecipe } from '../../api/recipes'
import { formatDuration } from '../../utils/format'
import { EMBED_HEIGHT_MESSAGE } from '../../utils/embedMessages'
import { recipeImageUrl } from '../../utils/recipeImageUrl'
import type { Recipe } from '../../types/models'

// Compact recipe card rendered inside a blog post's <iframe> (route meta `embed`: no navbar,
// no footer). Links open in the top window, not inside the iframe.
const props = defineProps<{
  id: string | number
}>()

const recipe = ref<Recipe | null>(null)
const notFound = ref(false)
const root = ref<HTMLElement | null>(null)
let observer: ResizeObserver | null = null

function postHeight() {
  if (!root.value || window.parent === window) return
  window.parent.postMessage(
    { type: EMBED_HEIGHT_MESSAGE, height: root.value.getBoundingClientRect().height },
    window.location.origin,
  )
}

onMounted(async () => {
  if (typeof ResizeObserver !== 'undefined' && root.value) {
    observer = new ResizeObserver(postHeight)
    observer.observe(root.value)
  }
  try {
    recipe.value = await getRecipe(props.id)
  } catch {
    notFound.value = true
  }
})

onBeforeUnmount(() => observer?.disconnect())
</script>

<template>
  <div ref="root" class="recipe-embed">
    <a
      v-if="recipe"
      class="embed-card"
      :href="`/recipes/${recipe.id}`"
      target="_top"
      data-testid="recipe-embed-card"
    >
      <img v-if="recipeImageUrl(recipe)" :src="recipeImageUrl(recipe)!" alt="" class="embed-image" />
      <span v-else class="embed-image embed-image-placeholder"><Utensils :size="28" /></span>
      <span class="embed-body">
        <span class="embed-kicker">{{ $t('blog.embed.kicker') }}</span>
        <strong class="embed-title">{{ recipe.title }}</strong>
        <span class="embed-meta">
          <span><Clock :size="14" /> {{ formatDuration(recipe.total_time_minutes) }}</span>
          <span><Users :size="14" /> {{ $t('blog.embed.servings', recipe.servings) }}</span>
        </span>
        <span class="embed-cta">{{ $t('blog.embed.view') }} →</span>
      </span>
    </a>
    <p v-else-if="notFound" class="embed-card embed-missing">{{ $t('blog.embed.unavailable') }}</p>
    <p v-else class="embed-card embed-missing">{{ $t('common.loading') }}</p>
  </div>
</template>

<style scoped>
.recipe-embed {
  padding: 2px;
}

.embed-card {
  display: flex;
  gap: 1rem;
  align-items: stretch;
  padding: 0.75rem;
  margin: 0;
  border: 1px solid var(--color-border);
  border-radius: 0;
  background: var(--color-surface);
  color: var(--color-text);
  text-decoration: none;
}

.embed-card:hover {
  border-color: var(--color-primary);
}

.embed-image {
  width: 110px;
  height: 110px;
  flex-shrink: 0;
  object-fit: cover;
  border-radius: 0;
}

.embed-image-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}

.embed-body {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  min-width: 0;
}

.embed-kicker {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-primary);
}

.embed-title {
  font-size: 1.05rem;
  line-height: 1.3;
}

.embed-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  font-size: 0.85rem;
  color: var(--color-muted);
}

.embed-meta span {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.embed-cta {
  margin-top: auto;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-primary-dark);
}

.embed-missing {
  justify-content: center;
  color: var(--color-muted);
}
</style>
