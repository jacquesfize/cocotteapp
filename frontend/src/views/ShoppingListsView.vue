<script setup lang="ts">
import { ShoppingCart } from '@lucide/vue'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '../components/PageHeader.vue'
import Pagination from '../components/Pagination.vue'
import ShoppingListCard from '../components/shared/ShoppingListCard.vue'
import AsyncState from '../components/shared/AsyncState.vue'
import { usePaginatedQuery } from '../composables/usePaginatedQuery'
import { deleteShoppingList, listShoppingLists } from '../api/shopping'
import type { ShoppingList } from '../types/models'

const router = useRouter()

const shoppingLists = ref<ShoppingList[]>([])
const count = ref(0)

async function load() {
  const params: { page?: number } = {}
  if (page.value > 1) params.page = page.value
  const data = await listShoppingLists(params)
  shoppingLists.value = data.results
  count.value = data.count
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
    <AsyncState v-if="!shoppingLists.length" :empty-text="$t('shopping.noLists')" />

    <ShoppingListCard v-for="list in shoppingLists" :key="list.id" :list="list" @delete="handleDelete" />

    <Pagination :page="page" :count="count" @update:page="goToPage" />
  </div>
</template>
