<script setup lang="ts">
import { CalendarDays, ShoppingCart } from '@lucide/vue'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '../../components/shared/PageHeader.vue'
import Pagination from '../../components/shared/Pagination.vue'
import ShoppingListCard from '../../components/shared/ShoppingListCard.vue'
import AsyncState from '../../components/shared/AsyncState.vue'
import { usePaginatedQuery } from '../../composables/usePaginatedQuery'
import { deleteShoppingList, listShoppingLists } from '../../api/shopping'
import type { ShoppingList } from '../../types/models'

const router = useRouter()

const shoppingLists = ref<ShoppingList[]>([])
const count = ref(0)
// Évite de montrer l'état vide (et son lien vers l'agenda) avant la première réponse.
const isLoaded = ref(false)

async function load() {
  const params: { page?: number } = {}
  if (page.value > 1) params.page = page.value
  const data = await listShoppingLists(params)
  shoppingLists.value = data.results
  count.value = data.count
  isLoaded.value = true
  router.replace({ query: params as Record<string, number> })
}

const { page, goToPage } = usePaginatedQuery(load)

async function handleDelete(id: number) {
  await deleteShoppingList(id)
  if (page.value > 1 && shoppingLists.value.length === 1) page.value -= 1
  await load()
}
</script>

<template>
  <div>
    <PageHeader :icon="ShoppingCart" :title="$t('shopping.title')" />
    <!-- Les listes sont générées depuis l'agenda : l'état vide y renvoie directement. -->
    <div v-if="isLoaded && !shoppingLists.length" class="card empty-lists" data-testid="shopping-empty">
      <AsyncState :empty-text="$t('shopping.noLists')" />
      <RouterLink :to="{ name: 'planning' }" class="planning-link">
        <CalendarDays :size="16" aria-hidden="true" />{{ $t('shopping.goToPlanning') }}
      </RouterLink>
    </div>

    <ShoppingListCard v-for="list in shoppingLists" :key="list.id" :list="list" @delete="handleDelete" />

    <Pagination :page="page" :count="count" @update:page="goToPage" />
  </div>
</template>

<style scoped>
.empty-lists {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.75rem;
}

.empty-lists p {
  margin: 0;
}

/* Lien présenté comme un bouton principal (même gabarit que les boutons pilule globaux). */
.planning-link {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  min-height: 2.75rem;
  padding: 0.65rem 1.25rem;
  border-radius: 999px;
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-weight: 600;
  text-decoration: none;
}

.planning-link:hover {
  background: var(--color-primary-dark);
  color: var(--color-on-primary);
}

.planning-link:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
</style>
