<script setup lang="ts">
import { ShieldCheck } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { fetchLegalInfo } from '../api/auth'
import PageHeader from '../components/shared/PageHeader.vue'
import type { LegalInfo } from '../types/models'

// Mentions légales et politique de confidentialité : même gabarit, contenu propre à chaque page.
// Les coordonnées viennent de la configuration de l'instance (variables d'environnement).
const props = defineProps<{ page: 'legal' | 'privacy' }>()

const { t, tm, rt } = useI18n()
const info = ref<LegalInfo | null>(null)
const error = ref(false)

onMounted(async () => {
  try {
    info.value = await fetchLegalInfo()
  } catch {
    error.value = true
  }
})

const contact = computed(() => info.value?.privacy_contact_email || t('legal.notConfigured'))
const dataItems = computed(() => (tm('legal.dataItems') as string[]).map((item) => rt(item)))
const orFallback = (value?: string) => value || t('legal.notConfigured')
</script>

<template>
  <PageHeader :icon="ShieldCheck" :title="page === 'legal' ? $t('legal.legalTitle') : $t('legal.privacyTitle')" />
  <p v-if="error" class="error">{{ $t('legal.loadError') }}</p>

  <article v-else-if="info" class="card legal">
    <template v-if="props.page === 'legal'">
      <h2>{{ $t('legal.publisherTitle') }}</h2>
      <dl>
        <dt>{{ $t('legal.name') }}</dt>
        <dd>{{ orFallback(info.publisher_name) }}</dd>
        <dt>{{ $t('legal.address') }}</dt>
        <dd>{{ orFallback(info.publisher_address) }}</dd>
        <dt>{{ $t('legal.email') }}</dt>
        <dd>{{ orFallback(info.contact_email) }}</dd>
      </dl>
      <h2>{{ $t('legal.hostTitle') }}</h2>
      <dl>
        <dt>{{ $t('legal.name') }}</dt>
        <dd>{{ orFallback(info.host_name) }}</dd>
        <dt>{{ $t('legal.address') }}</dt>
        <dd>{{ orFallback(info.host_address) }}</dd>
      </dl>
    </template>

    <template v-else>
      <p class="muted">{{ $t('legal.version', { version: info.policy_version }) }}</p>
      <h2>{{ $t('legal.controllerTitle') }}</h2>
      <p>{{ $t('legal.controllerText', { contact }) }}</p>
      <h2>{{ $t('legal.dataTitle') }}</h2>
      <ul>
        <li v-for="item in dataItems" :key="item">{{ item }}</li>
      </ul>
      <h2>{{ $t('legal.purposesTitle') }}</h2>
      <p>{{ $t('legal.purposesText') }}</p>
      <h2>{{ $t('legal.healthTitle') }}</h2>
      <p>{{ $t('legal.healthText') }}</p>
      <h2>{{ $t('legal.retentionTitle') }}</h2>
      <p>{{ $t('legal.retentionText') }}</p>
      <p v-if="info.inactive_retention_days > 0">
        {{ $t('legal.retentionInactive', { days: info.inactive_retention_days }) }}
      </p>
      <h2>{{ $t('legal.recipientsTitle') }}</h2>
      <p>{{ $t('legal.recipientsText') }}</p>
      <h2>{{ $t('legal.rightsTitle') }}</h2>
      <p>{{ $t('legal.rightsText', { contact }) }}</p>
      <h2>{{ $t('legal.cookiesTitle') }}</h2>
      <p>{{ $t('legal.cookiesText') }}</p>
      <h2>{{ $t('legal.complaintTitle') }}</h2>
      <p>{{ $t('legal.complaintText') }}</p>
    </template>
  </article>
</template>

<style scoped>
.legal {
  max-width: 48rem;
}

.legal h2 {
  margin-top: 1.5rem;
}

.legal h2:first-child {
  margin-top: 0;
}

dt {
  font-weight: 600;
}

dd {
  margin: 0 0 0.5rem;
}
</style>
