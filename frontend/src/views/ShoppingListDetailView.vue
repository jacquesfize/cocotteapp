<script setup lang="ts">
import { Apple, Bean, Beef, Carrot, CloudOff, Download, Droplet, Egg, Milk, Nut, Package, ShoppingCart, Sparkles, Wheat } from '@lucide/vue'
import { computed, onBeforeUnmount, onMounted, ref, type Component } from 'vue'
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

// Une icône par catégorie pour un repérage visuel plus rapide au supermarché qu'un simple
// intitulé — une seule teinte (l'accent du thème) plutôt qu'une couleur par catégorie, pour
// rester cohérent avec le reste de l'app (accent personnalisable, voir utils/theme.ts) et le
// mode sombre.
const CATEGORY_ICON: Record<IngredientCategory, Component> = {
  vegetable: Carrot,
  fruit: Apple,
  legume: Bean,
  grain: Wheat,
  nut_seed: Nut,
  dairy: Milk,
  meat_fish: Beef,
  egg: Egg,
  fat: Droplet,
  condiment: Sparkles,
  other: Package,
}

interface ItemGroup {
  category: IngredientCategory
  items: ItemWithSync[]
  ownedCount: number
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
  return CATEGORY_ORDER.filter((category) => byCategory.has(category)).map((category) => {
    const items = byCategory.get(category)!
    return { category, items, ownedCount: items.filter((item) => item.is_owned).length }
  })
})

const totalCount = computed(() => shoppingList.value?.items.length ?? 0)
const ownedCount = computed(() => shoppingList.value?.items.filter((item) => item.is_owned).length ?? 0)
const progressPercent = computed(() => (totalCount.value ? Math.round((ownedCount.value / totalCount.value) * 100) : 0))

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

    <div class="progress-summary">
      <p class="muted">
        {{ $t('shopping.checkOwned') }}
        <template v-if="totalCount">
          — {{ $t('shopping.progressCount', { owned: ownedCount, total: totalCount }) }}
        </template>
      </p>
      <div v-if="totalCount" class="progress-track" role="progressbar" :aria-valuenow="progressPercent" aria-valuemin="0" aria-valuemax="100">
        <div class="progress-fill" :style="{ width: `${progressPercent}%` }" />
      </div>
    </div>

    <div v-for="group in groupedItems" :key="group.category" class="card category-group">
      <div class="category-header">
        <span class="category-icon">
          <component :is="CATEGORY_ICON[group.category]" :size="18" />
        </span>
        <h2 class="category-title">{{ $t(`ingredientCategory.${group.category}`) }}</h2>
        <span class="category-count">{{ group.ownedCount }}/{{ group.items.length }}</span>
      </div>
      <div v-for="item in group.items" :key="item.id" class="item-row">
        <label class="item-label">
          <input
            type="checkbox"
            class="item-checkbox"
            :checked="item.is_owned"
            :disabled="item.pendingSync"
            @change="toggleOwned(item)"
          />
          <span class="item-text" :class="{ owned: item.is_owned }">
            <span class="item-qty">{{ formatQuantity(item.quantity, item.unit) }} {{ formatUnit(item.unit, item.quantity) }}</span>
            {{ item.ingredient.name }}
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

.progress-summary {
  margin-bottom: 1.25rem;
}

.progress-summary .muted {
  margin: 0 0 0.5rem;
}

.progress-track {
  height: 0.4rem;
  border-radius: 999px;
  background: var(--color-surface-muted);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 999px;
  transition: width 0.2s ease;
}

.category-group {
  margin-bottom: 1rem;
  padding: 1rem 1.25rem;
}

.category-header {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin: 0 0 0.6rem;
}

.category-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  flex-shrink: 0;
  border-radius: 999px;
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}

.category-title {
  margin: 0;
  font-size: 1rem;
  flex: 1;
}

.category-count {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-muted);
}

.item-row + .item-row {
  border-top: 1px solid var(--color-border);
}

.item-label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0;
  cursor: pointer;
  border-radius: 10px;
  transition: background-color 0.15s ease;
}

.item-label:hover {
  background: var(--color-surface-muted);
}

.item-checkbox {
  width: 1.25rem;
  height: 1.25rem;
  min-height: 0;
  flex-shrink: 0;
}

.item-text {
  flex: 1;
  transition: opacity 0.15s ease;
}

.item-qty {
  display: inline-block;
  margin-right: 0.4rem;
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
  background: var(--color-surface-muted);
  color: var(--color-muted);
  font-size: 0.8rem;
  font-weight: 600;
  white-space: nowrap;
}

.owned {
  text-decoration: line-through;
  color: var(--color-muted);
  opacity: 0.6;
}

.owned .item-qty {
  background: transparent;
}

.pending-sync {
  display: inline-flex;
  color: var(--color-muted);
}
</style>
