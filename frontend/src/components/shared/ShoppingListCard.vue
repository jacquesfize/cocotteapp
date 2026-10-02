<script setup lang="ts">
import { ShoppingCart, Trash2 } from '@lucide/vue'
import { computed } from 'vue'
import ProgressBar from './ProgressBar.vue'
import { shoppingListProgress } from '../../utils/shoppingListProgress'
import type { ShoppingList } from '../../types/models'

const props = defineProps<{
  list: ShoppingList
}>()
defineEmits<{
  delete: [id: number]
}>()

const progress = computed(() => shoppingListProgress(props.list))
</script>

<template>
  <div class="card list-card">
    <span class="list-icon"><ShoppingCart :size="18" /></span>
    <div class="list-body">
      <h2 class="list-title">
        <!-- Lien "étiré" (::after, voir .card-link dans base.css) sur toute la carte : la carte
             reste cliquable partout sans imbriquer le bouton Supprimer dans un <a>. -->
        <RouterLink :to="{ name: 'shopping-list-detail', params: { id: list.id } }" class="card-link">
          {{ list.name }}
        </RouterLink>
      </h2>
      <p class="muted list-meta">
        {{ new Date(list.created_at).toLocaleDateString() }}
        <template v-if="progress.total">
          · {{ $t('shopping.progressCount', { owned: progress.owned, total: progress.total }) }}
        </template>
      </p>
      <ProgressBar
        v-if="progress.total"
        :percent="progress.percent"
        class="list-progress"
        height="0.3rem"
        max-width="220px"
        :transition="false"
      />
    </div>
    <button
      class="danger icon-btn list-delete"
      :aria-label="`${$t('shopping.delete')} — ${list.name}`"
      @click="$emit('delete', list.id)"
    >
      <Trash2 :size="16" />
    </button>
  </div>
</template>

<style scoped>
.list-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.75rem;
  padding: 1rem 1.25rem;
}

.list-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  flex-shrink: 0;
  border-radius: var(--radius-pill);
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}

.list-body {
  flex: 1;
  min-width: 0;
}

.list-title {
  margin: 0;
  font-size: 1.05rem;
}

.list-meta {
  margin: 0.2rem 0 0;
}

.list-progress {
  margin-top: 0.5rem;
}

/* Au-dessus du lien étiré pour rester cliquable. */
.list-delete {
  position: relative;
  z-index: 1;
  flex-shrink: 0;
  opacity: 0.6;
  transition: opacity 0.15s ease;
}

.list-card:hover .list-delete,
.list-delete:focus-visible {
  opacity: 1;
}

@media (max-width: 600px) {
  .list-delete {
    opacity: 1;
  }
}
</style>
