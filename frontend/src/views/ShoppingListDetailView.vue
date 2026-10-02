<script setup lang="ts">
import { CloudOff, Download, ShoppingCart } from '@lucide/vue'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import PageHeader from '../components/PageHeader.vue'
import { exportShoppingList, getShoppingList, markOwned } from '../api/shopping'
import { isMarkOwnedQueued, isNetworkError, QUEUE_FLUSHED_EVENT, queueMarkOwned } from '../offline/sync'
import { downloadBlob } from '../utils/download'
import { formatQuantity, formatUnit } from '../utils/format'
import type { IngredientCategory, ShoppingList, ShoppingListItem } from '../types/models'

type ItemWithSync = ShoppingListItem & { pendingSync?: boolean }
type ListWithSync = Omit<ShoppingList, 'items'> & { items: ItemWithSync[] }

// Même ordre que le menu de catégorie des ingrédients (IngredientEditModal.vue) : produits
// frais d'abord, épicerie ensuite, "Autre" en dernier — plutôt qu'un tri alphabétique qui
// mélangerait les catégories de façon moins naturelle pour faire les courses.
const CATEGORY_ORDER: IngredientCategory[] = [
  'vegetable',
  'fruit',
  'legume',
  'grain',
  'nut_seed',
  'dairy',
  'meat_fish',
  'egg',
  'fat',
  'condiment',
  'other',
]

interface ItemGroup {
  category: IngredientCategory
  items: ItemWithSync[]
}

const props = defineProps<{
  id: string | number
}>()

const shoppingList = ref<ListWithSync | null>(null)

// Groupe les articles par catégorie d'ingrédient (légume, fruit, produit laitier...) dans
// l'ordre de CATEGORY_ORDER, pour que des produits similaires se retrouvent côte à côte au
// supermarché plutôt qu'en une seule liste plate.
const groupedItems = computed<ItemGroup[]>(() => {
  if (!shoppingList.value) return []
  const byCategory = new Map<IngredientCategory, ItemWithSync[]>()
  for (const item of shoppingList.value.items) {
    const category = item.ingredient.category
    const bucket = byCategory.get(category)
    if (bucket) {
      bucket.push(item)
    } else {
      byCategory.set(category, [item])
    }
  }
  return CATEGORY_ORDER.filter((category) => byCategory.has(category)).map((category) => ({
    category,
    items: byCategory.get(category)!,
  }))
})

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
  // Optimiste : l'état visuel change tout de suite, qu'on coche ou décoche.
  const newOwned = !item.is_owned
  item.is_owned = newOwned
  try {
    await markOwned(props.id, [item.ingredient.id], newOwned)
  } catch (error) {
    if (!isNetworkError(error)) {
      item.is_owned = !newOwned
      return
    }
    if (newOwned) {
      // Hors ligne en train de cocher : c'est le seul chemin d'écriture hors-ligne supporté
      // par l'app (voir docs/user-guide/offline-and-install.md) — on met de côté pour rejouer
      // au retour du réseau, la case reste cochée en attendant (icône "pendingSync").
      await queueMarkOwned(props.id, [item.ingredient.id])
      item.pendingSync = true
    } else {
      // Hors ligne en train de décocher : non supporté (la file ne rejoue que des mises à
      // "possédé"), donc on annule plutôt que de mettre en file une écriture qui rejouerait le
      // mauvais état une fois la connexion revenue. Échec silencieux et sans corruption plutôt
      // que d'étendre la surface d'écriture hors-ligne.
      item.is_owned = true
    }
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

    <div v-for="group in groupedItems" :key="group.category" class="card category-group">
      <h2 class="category-title">{{ $t(`ingredientCategory.${group.category}`) }}</h2>
      <div v-for="item in group.items" :key="item.id" class="item-row">
        <label class="row" style="align-items: center; gap: 0.75rem">
          <input
            type="checkbox"
            :checked="item.is_owned"
            :disabled="item.pendingSync"
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

.category-group {
  margin-bottom: 1rem;
}

.category-title {
  margin: 0 0 0.5rem;
  font-size: 1rem;
  color: var(--color-muted);
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
