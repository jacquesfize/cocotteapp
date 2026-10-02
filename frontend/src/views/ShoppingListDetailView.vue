<script setup lang="ts">
import { Check, CloudOff, Copy, Download, Share, ShoppingCart } from '@lucide/vue'
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
// La plupart des navigateurs desktop (Chrome/Firefox hors Windows) n'implémentent pas
// navigator.share : sans ce repli, le bouton ne faisait jamais qu'un téléchargement .txt, ce
// qui ne permet pas vraiment de "coller" la liste dans une appli de notes.
const canShare = !!navigator.share
const canCopy = !canShare && !!navigator.clipboard?.writeText
const justCopied = ref(false)
let copiedTimeout: ReturnType<typeof setTimeout> | undefined

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
  clearTimeout(copiedTimeout)
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
  if (navigator.share) {
    try {
      await navigator.share({ title: shoppingList.value?.name, text: content })
      return
    } catch (err) {
      if ((err as { name?: string })?.name === 'AbortError') {
        // User just cancelled the share sheet — not a failure, do nothing.
        return
      }
      // Any other error: fall through to the clipboard/download fallback below.
    }
  }
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(content)
      justCopied.value = true
      clearTimeout(copiedTimeout)
      copiedTimeout = setTimeout(() => {
        justCopied.value = false
      }, 2000)
      return
    } catch {
      // Clipboard write can fail (permission denied, non-secure context) — fall through.
    }
  }
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  downloadBlob(blob, `${shoppingList.value?.name}.txt`)
}
</script>

<template>
  <div v-if="shoppingList">
    <div class="row page-header">
      <PageHeader :icon="ShoppingCart">{{ shoppingList.name }}</PageHeader>
      <button @click="handleExport">
        <Check v-if="justCopied" :size="16" />
        <Share v-else-if="canShare" :size="16" />
        <Copy v-else-if="canCopy" :size="16" />
        <Download v-else :size="16" />
        {{ justCopied ? $t('shopping.copied') : canShare ? $t('shopping.share') : canCopy ? $t('shopping.copyToClipboard') : $t('shopping.export') }}
      </button>
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
