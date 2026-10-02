<script setup lang="ts">
import { ShoppingCart, Trash2 } from '@lucide/vue'
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '../components/PageHeader.vue'
import Pagination from '../components/Pagination.vue'
import ProgressBar from '../components/shared/ProgressBar.vue'
import { deleteShoppingList, listShoppingLists } from '../api/shopping'
import type { ShoppingList } from '../types/models'

const route = useRoute()
const router = useRouter()

const shoppingLists = ref<ShoppingList[]>([])
const count = ref(0)
const page = ref(Number(route.query.page) || 1)

async function load() {
  const params: { page?: number } = {}
  if (page.value > 1) params.page = page.value
  const data = await listShoppingLists(params)
  shoppingLists.value = data.results
  count.value = data.count
  router.replace({ query: params as Record<string, number> })
}

function goToPage(newPage: number) {
  page.value = newPage
  load()
}

onMounted(load)

async function handleDelete(id: number) {
  await deleteShoppingList(id)
  if (page.value > 1 && shoppingLists.value.length === 1) page.value -= 1
  await load()
}

function ownedCount(list: ShoppingList) {
  return list.items.filter((item) => item.is_owned).length
}

function progressPercent(list: ShoppingList) {
  return list.items.length ? Math.round((ownedCount(list) / list.items.length) * 100) : 0
}
</script>

<template>
  <div>
    <PageHeader :icon="ShoppingCart" :title="$t('shopping.title')" />
    <p v-if="!shoppingLists.length" class="muted">{{ $t('shopping.noLists') }}</p>

    <div v-for="list in shoppingLists" :key="list.id" class="card list-card">
      <span class="list-icon"><ShoppingCart :size="18" /></span>
      <div class="list-body">
        <h2 class="list-title">
          <!-- Lien "étiré" (::after) sur toute la carte, comme RecipeCard.vue : la carte reste
               cliquable partout sans imbriquer le bouton Supprimer dans un <a>. -->
          <RouterLink :to="{ name: 'shopping-list-detail', params: { id: list.id } }" class="card-link">
            {{ list.name }}
          </RouterLink>
        </h2>
        <p class="muted list-meta">
          {{ new Date(list.created_at).toLocaleDateString() }}
          <template v-if="list.items.length">
            · {{ $t('shopping.progressCount', { owned: ownedCount(list), total: list.items.length }) }}
          </template>
        </p>
        <ProgressBar
          v-if="list.items.length"
          :percent="progressPercent(list)"
          class="list-progress"
          height="0.3rem"
          max-width="220px"
          :transition="false"
        />
      </div>
      <button
        class="danger icon-btn list-delete"
        :aria-label="`${$t('shopping.delete')} — ${list.name}`"
        @click="handleDelete(list.id)"
      >
        <Trash2 :size="16" />
      </button>
    </div>

    <Pagination :page="page" :count="count" @update:page="goToPage" />
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
  border-radius: 999px;
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

.card-link {
  color: inherit;
  text-decoration: none;
}

.card-link::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
}

.card-link:focus-visible {
  outline: none;
}

.card-link:focus-visible::after {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
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
