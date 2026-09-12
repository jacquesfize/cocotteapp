<script setup>
import { onMounted, ref } from 'vue'
import { exportShoppingList, getShoppingList, markOwned } from '../api/shopping'

const props = defineProps({
  id: { type: [String, Number], required: true },
})

const shoppingList = ref(null)

async function load() {
  shoppingList.value = await getShoppingList(props.id)
}

onMounted(load)

async function toggleOwned(item) {
  await markOwned(props.id, [item.ingredient.id])
  item.is_owned = true
}

async function handleExport() {
  const { content } = await exportShoppingList(props.id)
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${shoppingList.value.name}.txt`
  link.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div v-if="shoppingList">
    <div class="row page-header">
      <h1>{{ shoppingList.name }}</h1>
      <button @click="handleExport">{{ $t('shopping.export') }}</button>
    </div>
    <p class="muted">{{ $t('shopping.checkOwned') }}</p>

    <div class="card">
      <div v-for="item in shoppingList.items" :key="item.id" class="item-row">
        <label class="row" style="align-items: center; gap: 0.75rem">
          <input
            type="checkbox"
            :checked="item.is_owned"
            :disabled="item.is_owned"
            style="width: auto"
            @change="toggleOwned(item)"
          />
          <span :class="{ owned: item.is_owned }">
            {{ item.quantity }} {{ item.unit }} — {{ item.ingredient.name }}
          </span>
        </label>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-header {
  justify-content: space-between;
  align-items: center;
}

.item-row {
  padding: 0.35rem 0;
}

.owned {
  text-decoration: line-through;
  color: var(--color-muted);
}
</style>
