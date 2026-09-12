<script setup>
import { onMounted, ref } from 'vue'
import { deleteShoppingList, listShoppingLists } from '../api/shopping'

const shoppingLists = ref([])

async function load() {
  const data = await listShoppingLists()
  shoppingLists.value = data.results
}

onMounted(load)

async function handleDelete(id) {
  await deleteShoppingList(id)
  await load()
}
</script>

<template>
  <div>
    <h1>{{ $t('shopping.title') }}</h1>
    <p v-if="!shoppingLists.length" class="muted">{{ $t('shopping.noLists') }}</p>
    <div v-for="list in shoppingLists" :key="list.id" class="card list-row">
      <RouterLink :to="{ name: 'shopping-list-detail', params: { id: list.id } }">
        {{ list.name }} — {{ new Date(list.created_at).toLocaleDateString() }}
      </RouterLink>
      <button class="secondary" @click="handleDelete(list.id)">{{ $t('shopping.delete') }}</button>
    </div>
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
