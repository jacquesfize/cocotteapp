<script setup lang="ts">
import { Tags, X } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import VueMultiselect from 'vue-multiselect'
import 'vue-multiselect/dist/vue-multiselect.css'
import '../../assets/multiselect.css'
import { createPersonalTag, findSimilarPersonalTags, listPersonalTags } from '../../api/personalTags'
import { setRecipeTags } from '../../api/recipes'
import PersonalTagChip from './PersonalTagChip.vue'
import SimilarTagsHint from './SimilarTagsHint.vue'
import type { PersonalTag } from '../../types/models'

// Étiquettes personnelles du visiteur sur une recette (la sienne ou celle d'un autre) : choisies
// parmi les siennes, ou créées à la volée en tapant un nom inconnu puis Entrée — après avoir vu
// les étiquettes existantes qui lui ressemblent, pour éviter les doublons.
const selected = defineModel<PersonalTag[]>({ required: true })

const props = defineProps<{
  recipeId: number
}>()

const { t } = useI18n()
const options = ref<PersonalTag[]>([])
const error = ref('')
const pendingName = ref('')
const similar = ref<PersonalTag[]>([])

onMounted(async () => {
  options.value = await listPersonalTags().catch(() => [])
})

async function save(tags: PersonalTag[]) {
  error.value = ''
  const previous = selected.value
  selected.value = tags
  try {
    selected.value = await setRecipeTags(props.recipeId, tags.map((tag) => tag.id))
  } catch {
    selected.value = previous
    error.value = t('personalTags.saveError')
  }
}

const model = computed<PersonalTag[]>({
  get: () => selected.value,
  set: (tags) => {
    save(tags)
  },
})

function cancelCreate() {
  pendingName.value = ''
  similar.value = []
}

function add(tag: PersonalTag) {
  cancelCreate()
  if (!selected.value.some((item) => item.id === tag.id)) save([...selected.value, tag])
}

async function create(name: string) {
  error.value = ''
  try {
    const tag = await createPersonalTag({ name })
    options.value = [...options.value, tag].sort((a, b) => a.name.localeCompare(b.name))
    add(tag)
  } catch {
    error.value = t('personalTags.createError')
  }
}

async function requestCreate(name: string) {
  const trimmed = name.trim()
  if (!trimmed) return
  const existing = options.value.find((tag) => tag.name.toLowerCase() === trimmed.toLowerCase())
  if (existing) return add(existing)
  const matches = await findSimilarPersonalTags(trimmed).catch(() => [])
  if (!matches.length) return create(trimmed)
  pendingName.value = trimmed
  similar.value = matches
}

defineExpose({ requestCreate })
</script>

<template>
  <section class="personal-tags-editor">
    <div class="header">
      <label for="personal-tags-input"><Tags :size="16" />{{ t('personalTags.recipeLabel') }}</label>
      <RouterLink :to="{ name: 'personal-tags' }" class="manage-link">{{ t('personalTags.manage') }}</RouterLink>
    </div>
    <div class="themed-multiselect">
      <VueMultiselect
        id="personal-tags-input"
        v-model="model"
        :options="options"
        :multiple="true"
        :taggable="true"
        track-by="id"
        label="name"
        :close-on-select="false"
        :show-labels="false"
        :placeholder="t('personalTags.placeholder')"
        :tag-placeholder="t('personalTags.createHint')"
        @tag="requestCreate"
      >
        <template #tag="{ option, remove }">
          <PersonalTagChip :tag="option" class="selected-tag">
            <button
              type="button"
              class="remove-tag"
              :aria-label="t('personalTags.remove', { name: option.name })"
              @mousedown.prevent
              @click="remove(option)"
            >
              <X :size="12" />
            </button>
          </PersonalTagChip>
        </template>
        <template #option="{ option }">
          <PersonalTagChip v-if="option.id" :tag="option" />
          <template v-else>{{ option.label }}</template>
        </template>
        <template #noOptions>{{ t('personalTags.noOptions') }}</template>
      </VueMultiselect>
    </div>
    <SimilarTagsHint v-if="similar.length" :tags="similar" @pick="add">
      <div class="row hint-actions">
        <button type="button" class="secondary" @click="create(pendingName)">
          {{ t('personalTags.createAnyway', { name: pendingName }) }}
        </button>
        <button type="button" class="secondary" @click="cancelCreate">{{ t('common.cancel') }}</button>
      </div>
    </SimilarTagsHint>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
  </section>
</template>

<style scoped>
.personal-tags-editor {
  margin: 1.5rem 0;
}

.header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.4rem;
}

.header label {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-weight: 600;
}

.manage-link {
  font-size: 0.85rem;
}

.selected-tag {
  margin: 0 0.3rem 0.4rem 0;
}

.remove-tag {
  display: inline-flex;
  min-height: auto;
  margin-left: 0.15rem;
  padding: 0.1rem;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.remove-tag:hover {
  background: color-mix(in srgb, currentColor 15%, transparent);
}

.hint-actions {
  gap: 0.5rem;
}
</style>
