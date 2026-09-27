<script setup lang="ts">
import { CloudOff, Download, ShoppingCart } from '@lucide/vue'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import PageHeader from '../components/PageHeader.vue'
import { exportShoppingList, getShoppingList, markOwned } from '../api/shopping'
import { isMarkOwnedQueued, isNetworkError, QUEUE_FLUSHED_EVENT, queueMarkOwned } from '../offline/sync'
import { downloadBlob } from '../utils/download'
import { formatQuantity, formatUnit } from '../utils/format'
import type { ShoppingList,ShoppingListItem } from '../types/models'

type ItemWithSync = ShoppingListItem & { pendingSync?: boolean }
type ListWithSync = Omit<ShoppingList, 'items'> & { items: ItemWithSync[] }

const props = defineProps<{
  id: string | number
}>()

const shoppingList = ref<ListWithSync | null>(null)

async function load() {
  shoppingList.value = (await getShoppingList(props.id)) as ListWithSync
  for (const item of shoppingList.value.items) {
    item.pendingSync = !item.is_owned && (await isMarkOwnedQueued(props.id, item.ingredient.id))
  }
}

function handleQueueFlushed() {
  load()
}

onMounted(() => {
  load()
  window.addEventListener(QUEUE_FLUSHED_EVENT, handleQueueFlushed)
})

onBeforeUnmount(() => {
  window.removeEventListener(QUEUE_FLUSHED_EVENT, handleQueueFlushed)
})

async function toggleOwned(item: ItemWithSync) {
  // Optimiste : on coche tout de suite, la case reste cochée même si la requête part
  // en file d'attente (pratique au supermarché avec un réseau capricieux).
  item.is_owned = true
  try {
    await markOwned(props.id, [item.ingredient.id])
  } catch (error) {
    if (!isNetworkError(error)) {
      item.is_owned = false
      return
    }
    await queueMarkOwned(props.id, [item.ingredient.id])
    item.pendingSync = true
  }
}

async function handleExport() {
  const { content } = await exportShoppingList(props.id)
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  downloadBlob(blob, `${shoppingList.value?.name}.txt`)
}
</script>

<template>
  <div v-if="shoppingList">
    <div class="row page-header">
      <PageHeader :icon="ShoppingCart">{{ shoppingList.name }}</PageHeader>
      <button @click="handleExport"><Download :size="16" />{{ $t('shopping.export') }}</button>
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
            {{ formatQuantity(item.quantity, item.unit) }} {{ formatUnit(item.unit, item.quantity) }} — {{ item.ingredient.name }}
          </span>
          <span v-if="item.pendingSync" class="pending-sync" :title="$t('offline.pendingSync')">
            <CloudOff :size="14" />
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

.pending-sync {
  display: inline-flex;
  color: var(--color-muted);
}
</style>
