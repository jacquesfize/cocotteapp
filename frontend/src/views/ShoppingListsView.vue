<script setup lang="ts">
import { ShoppingCart, Trash2 } from '@lucide/vue'
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '../components/PageHeader.vue'
import Pagination from '../components/Pagination.vue'
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
</script>

<template>
  <div>
    <PageHeader :icon="ShoppingCart" :title="$t('shopping.title')" />
    <p v-if="!shoppingLists.length" class="muted">{{ $t('shopping.noLists') }}</p>
    <div v-for="list in shoppingLists" :key="list.id" class="card list-row">
      <RouterLink :to="{ name: 'shopping-list-detail', params: { id: list.id } }">
        {{ list.name }} — {{ new Date(list.created_at).toLocaleDateString() }}
      </RouterLink>
      <button
        class="danger icon-btn"
        :aria-label="$t('shopping.delete')"
        @click="handleDelete(list.id)"
      >
        <Trash2 :size="16" />
      </button>
    </div>

    <Pagination :page="page" :count="count" @update:page="goToPage" />
  </div>
</template>

<style scoped>
.list-row {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}
</style>
