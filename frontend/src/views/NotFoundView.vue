<script setup lang="ts">
import { BookOpen, Home, SearchX } from '@lucide/vue'
import PageHeader from '../components/shared/PageHeader.vue'

// Page affichée pour toute URL inconnue (route catch-all), au lieu d'une redirection silencieuse.
</script>

<template>
  <div>
    <PageHeader :icon="SearchX" :title="$t('notFound.title')" />
    <div class="card not-found" data-testid="not-found">
      <p class="not-found-code" aria-hidden="true">404</p>
      <p>{{ $t('notFound.message') }}</p>
      <div class="not-found-links">
        <RouterLink :to="{ name: 'home' }" class="not-found-link is-primary">
          <Home :size="16" aria-hidden="true" />{{ $t('notFound.home') }}
        </RouterLink>
        <RouterLink :to="{ name: 'recipes' }" class="not-found-link">
          <BookOpen :size="16" aria-hidden="true" />{{ $t('notFound.recipes') }}
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
.not-found {
  text-align: center;
  padding: 2rem 1.25rem;
}

.not-found-code {
  margin: 0 0 0.5rem;
  font-size: 3rem;
  font-weight: 800;
  line-height: 1;
  color: var(--color-primary);
}

.not-found-links {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.75rem;
  margin-top: 1.25rem;
}

/* Liens présentés comme les boutons pilule globaux (principal / secondaire). */
.not-found-link {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  min-height: 2.75rem;
  padding: 0.65rem 1.25rem;
  border-radius: 999px;
  font-weight: 600;
  text-decoration: none;
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}

.not-found-link:hover {
  background: var(--color-primary-soft-hover);
}

.not-found-link.is-primary {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.not-found-link.is-primary:hover {
  background: var(--color-primary-dark);
}

.not-found-link:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
</style>
