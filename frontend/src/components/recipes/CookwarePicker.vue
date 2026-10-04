<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import VueMultiselect from 'vue-multiselect'
import 'vue-multiselect/dist/vue-multiselect.css'
import '../../assets/multiselect.css'
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
      </template>
      <template #noOptions>{{ t('cookware.noOptions') }}</template>
    </VueMultiselect>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
  </div>
</template>
