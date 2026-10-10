<script setup lang="ts">
import { Newspaper, Pencil, Trash2 } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../../stores/auth'
import { formatLongDate } from '../../utils/dates'
import type { BlogPostSummary } from '../../types/models'

const props = defineProps<{
  post: BlogPostSummary
  // Shows Edit / Delete to the post's author and to staff (blog list); off on the home page.
  manageable?: boolean
  // Smaller tile, image on top (home page).
  compact?: boolean
}>()
const emit = defineEmits<{ delete: [post: BlogPostSummary] }>()

const { locale } = useI18n()
const authStore = useAuthStore()

const canManage = computed(
  () =>
    props.manageable &&
    Boolean(authStore.user) &&
    (authStore.user?.is_staff || props.post.author_id === authStore.user?.id),
)
</script>

<template>
  <article class="card blog-card" :class="{ compact }">
    <img v-if="post.cover_image" :src="post.cover_image" alt="" class="blog-card-cover" />
    <div v-else class="blog-card-cover blog-card-placeholder" aria-hidden="true"><Newspaper :size="28" /></div>
    <div class="blog-card-body">
      <h3>
        <!-- Lien "étiré" (::after, cf. .card-link) : toute la carte est cliquable sans imbriquer
             les boutons Modifier / Supprimer dans un <a>. -->
        <RouterLink :to="{ name: 'blog-detail', params: { id: post.id } }" class="card-link">
          {{ post.title }}
        </RouterLink>
      </h3>
      <p class="muted blog-card-meta">
        {{ $t('blog.byline', { author: post.author, date: formatLongDate(post.created_at, locale) }) }}
      </p>
      <p v-if="post.excerpt" class="blog-card-excerpt">{{ post.excerpt }}</p>
      <div v-if="canManage" class="row blog-card-actions">
        <RouterLink
          :to="{ name: 'blog-edit', params: { id: post.id } }"
          class="blog-card-action"
          :aria-label="$t('blog.editNamed', { title: post.title })"
        >
          <Pencil :size="16" /><span>{{ $t('common.edit') }}</span>
        </RouterLink>
        <button
          type="button"
          class="blog-card-action danger-action"
          :aria-label="$t('blog.deleteNamed', { title: post.title })"
          @click="emit('delete', post)"
        >
          <Trash2 :size="16" /><span>{{ $t('common.delete') }}</span>
        </button>
      </div>
    </div>
  </article>
</template>

<style scoped>
.blog-card {
  position: relative;
  display: flex;
  gap: 1rem;
  padding: 1rem;
}

.blog-card-cover {
  width: 160px;
  height: 120px;
  flex-shrink: 0;
  object-fit: cover;
  border-radius: 14px;
}

.blog-card-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.blog-card-body {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.blog-card-body h3 {
  margin: 0 0 0.25rem;
  font-size: 1.15rem;
}

.blog-card-meta {
  margin: 0 0 0.5rem;
}

.blog-card-excerpt {
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Au-dessus du lien étiré de la carte. */
.blog-card-actions {
  position: relative;
  z-index: 1;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.blog-card-action {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  min-height: 2.25rem;
  padding: 0.35rem 0.85rem;
  border-radius: var(--radius-pill);
  background: var(--color-surface-muted);
  color: var(--color-text);
  font-size: 0.85rem;
  font-weight: 600;
  text-decoration: none;
}

.blog-card-action:hover {
  background: var(--color-primary-soft);
}

.danger-action {
  color: var(--color-danger);
}

.compact {
  flex-direction: column;
  gap: 0.6rem;
  padding: 0;
  overflow: hidden;
  box-shadow: none;
  border: 1px solid var(--color-border);
}

.compact .blog-card-cover {
  width: 100%;
  height: 130px;
  border-radius: 0;
}

.compact .blog-card-body {
  padding: 0 0.85rem 0.85rem;
}

.compact h3 {
  font-size: 1rem;
}

.compact .blog-card-excerpt {
  font-size: 0.9rem;
  -webkit-line-clamp: 2;
}

@media (max-width: 600px) {
  .blog-card:not(.compact) {
    flex-direction: column;
  }

  .blog-card:not(.compact) .blog-card-cover {
    width: 100%;
    height: 160px;
  }
}
</style>
