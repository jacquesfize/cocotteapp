<script setup lang="ts">
import { Pencil } from '@lucide/vue'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import VueMultiselect from 'vue-multiselect'
import 'vue-multiselect/dist/vue-multiselect.css'
import '../../assets/multiselect.css'
import CookwareEditModal from './CookwareEditModal.vue'
import UnverifiedBadge from '../shared/UnverifiedBadge.vue'
import { createCookware, listCookware } from '../../api/cookware'
import type { Cookware } from '../../types/models'

// Matériel de la recette : choisi dans la bibliothèque (courte, chargée en entier et filtrée
// côté client), ou créé à la volée en tapant un nom inconnu puis Entrée — comme un ingrédient
// manquant dans IngredientPicker, mais sans formulaire (un matériel n'a qu'un nom).
const selected = defineModel<Cookware[]>({ required: true })

defineProps<{
  id?: string
}>()

const { t } = useI18n()
const options = ref<Cookware[]>([])
const error = ref('')

onMounted(async () => {
  options.value = await listCookware().catch(() => [])
})

async function create(name: string) {
  error.value = ''
  const trimmed = name.trim()
  if (!trimmed) return
  const existing = options.value.find((item) => item.name.toLowerCase() === trimmed.toLowerCase())
  try {
    const cookware = existing ?? (await createCookware({ name: trimmed }))
    if (!existing) options.value = [...options.value, cookware].sort((a, b) => a.name.localeCompare(b.name))
    if (!selected.value.some((item) => item.id === cookware.id)) selected.value = [...selected.value, cookware]
  } catch {
    error.value = t('cookware.createError')
  }
}

// Correction d'un matériel choisi, depuis sa pilule : proposée seulement si l'API l'autorise
// (`can_edit` : son auteur tant qu'il n'est pas vérifié, ou un admin).
const editing = ref<Cookware | null>(null)

function replaceIn(list: Cookware[], cookware: Cookware) {
  return list.map((item) => (item.id === cookware.id ? cookware : item))
}

function handleUpdated(cookware: Cookware) {
  editing.value = null
  options.value = replaceIn(options.value, cookware).sort((a, b) => a.name.localeCompare(b.name))
  selected.value = replaceIn(selected.value, cookware)
}

function handleDeleted(id: number) {
  editing.value = null
  options.value = options.value.filter((item) => item.id !== id)
  selected.value = selected.value.filter((item) => item.id !== id)
}

defineExpose({ create })
</script>

<template>
  <div class="themed-multiselect">
    <VueMultiselect
      :id="id"
      v-model="selected"
      :options="options"
      :multiple="true"
      :taggable="true"
      track-by="id"
      label="name"
      :close-on-select="false"
      :show-labels="false"
      :placeholder="t('cookware.placeholder')"
      :tag-placeholder="t('cookware.createHint')"
      @tag="create"
    >
      <template #option="{ option }">
        <span v-if="option.emoji" class="option-emoji" aria-hidden="true">{{ option.emoji }}</span>{{ option.name ?? option.label }}
        <UnverifiedBadge v-if="option.is_verified === false" />
      </template>
      <template #tag="{ option, remove }">
        <span class="multiselect__tag cookware-tag" @mousedown.prevent>
          <span>{{ option.name }}</span>
          <UnverifiedBadge v-if="option.is_verified === false" />
          <button
            v-if="option.can_edit"
            type="button"
            class="cookware-tag-edit"
            data-testid="cookware-picker-edit"
            :aria-label="t('cookware.editLabel', { name: option.name })"
            :title="t('cookware.editLabel', { name: option.name })"
            @mousedown.prevent.stop
            @click.stop="editing = option"
          >
            <Pencil :size="12" aria-hidden="true" />
          </button>
          <i
            tabindex="1"
            class="multiselect__tag-icon"
            @keydown.enter.prevent="remove(option)"
            @mousedown.prevent="remove(option)"
          ></i>
        </span>
      </template>
      <template #noOptions>{{ t('cookware.noOptions') }}</template>
    </VueMultiselect>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <CookwareEditModal
      v-if="editing"
      :cookware="editing"
      @updated="handleUpdated"
      @deleted="handleDeleted"
      @close="editing = null"
    />
  </div>
</template>

<style scoped>
.cookware-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}

/* Petit crayon dans la pilule : pas de fond ni de hauteur minimale de bouton standard. */
.cookware-tag-edit {
  padding: 0.15rem;
  min-height: auto;
  border-radius: var(--radius-pill);
  background: transparent;
  color: inherit;
}

.cookware-tag-edit:hover,
.cookware-tag-edit:focus-visible {
  background: var(--color-primary-dark);
}
</style>
