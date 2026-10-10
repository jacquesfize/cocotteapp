<script setup lang="ts">
import { Globe } from '@lucide/vue'
import coverUrl from '../../assets/auth-cover.jpg'

defineProps<{ title: string }>()
</script>

<template>
  <div class="auth-split">
    <div class="auth-cover" aria-hidden="true">
      <img :src="coverUrl" alt="" />
    </div>

    <div class="auth-panel">
      <div class="auth-panel-inner">
        <div class="auth-brand">
          <img src="/favicon.svg" alt="" class="auth-logo" />
          <p class="auth-brand-name">{{ $t('app.title') }}</p>
        </div>

        <!-- Titre réservé aux lecteurs d'écran : les onglets de la vue l'affichent déjà. -->
        <h1 class="sr-only">{{ title }}</h1>

        <slot />

        <div class="auth-divider"><span>{{ $t('auth.or') }}</span></div>

        <RouterLink to="/recipes" class="auth-public-link">
          <Globe :size="18" />
          {{ $t('auth.browseWithoutAccount') }}
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: min(720px, calc(100vh - 8rem));
  background: var(--color-surface);
  border-radius: 0;
  overflow: hidden;
  box-shadow: var(--shadow-card);
}

.auth-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.auth-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2.5rem 1.5rem;
}

.auth-panel-inner {
  width: 100%;
  max-width: 360px;
}

.auth-brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1.75rem;
}

.auth-logo {
  width: 72px;
  height: 72px;
}

.auth-brand-name {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 800;
}

.auth-divider {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 1.5rem 0;
  color: var(--color-muted);
  font-size: 0.85rem;
}

.auth-divider::before,
.auth-divider::after {
  content: '';
  flex: 1;
  border-top: 1px solid var(--color-border);
}

.auth-public-link {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  min-height: 2.75rem;
  border: 1.5px solid var(--color-border);
  border-radius: 0;
  color: var(--color-text);
  text-decoration: none;
  font-weight: 600;
  transition: background-color 0.15s ease;
}

.auth-public-link:hover {
  background: var(--color-surface-muted);
}

@media (max-width: 760px) {
  .auth-split {
    grid-template-columns: 1fr;
    min-height: 0;
  }

  .auth-cover {
    display: none;
  }

  .auth-panel {
    padding: 2rem 1.25rem;
  }
}
</style>

<!-- Styles partagés par les formulaires glissés dans le slot (AuthView). -->
<style>
.auth-form .input-icon {
  position: relative;
  display: flex;
  align-items: center;
}

.auth-form .input-icon > svg {
  position: absolute;
  left: 0.9rem;
  color: var(--color-muted);
  pointer-events: none;
}

.auth-form .input-icon > input {
  width: 100%;
  padding-left: 2.75rem;
}

.auth-form .input-icon > input.has-toggle {
  padding-right: 3rem;
}

.auth-form .auth-links {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  margin: 0.25rem 0 1.25rem;
  font-size: 0.9rem;
  font-weight: 600;
}

.auth-form .auth-links a {
  text-decoration: none;
}

.auth-form button[type='submit'] {
  width: 100%;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
