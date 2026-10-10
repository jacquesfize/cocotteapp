<script setup lang="ts">
import { Shield, Trash2 } from '@lucide/vue'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import PageHeader from '../../components/shared/PageHeader.vue'
import Pagination from '../../components/shared/Pagination.vue'
import AsyncState from '../../components/shared/AsyncState.vue'
import { usePaginatedQuery } from '../../composables/usePaginatedQuery'
import { deleteUser, listUsers, updateUser } from '../../api/admin'
import { getErrorStatus } from '../../utils/apiError'
import { useAuthStore } from '../../stores/auth'
import type { AdminUserListParams } from '../../types/api'
import type { AdminUser } from '../../types/models'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const users = ref<AdminUser[]>([])
const count = ref(0)
const search = ref((route.query.search as string) || '')
const isLoading = ref(false)
const accessDenied = ref(false)

async function load() {
  isLoading.value = true
  try {
    const params: AdminUserListParams = {}
    if (search.value) params.search = search.value
    if (page.value > 1) params.page = page.value
    const data = await listUsers(params)
    users.value = data.results
    count.value = data.count
    accessDenied.value = false
    router.replace({ query: params as Record<string, string> })
  } catch (err) {
    if (getErrorStatus(err) === 403) accessDenied.value = true
  } finally {
    isLoading.value = false
  }
}

const { page, goToPage } = usePaginatedQuery(load, { search })

async function toggleActive(user: AdminUser) {
  user.is_active = await updateUser(user.id, { is_active: !user.is_active }).then((u) => u.is_active)
}

async function toggleStaff(user: AdminUser) {
  user.is_staff = await updateUser(user.id, { is_staff: !user.is_staff }).then((u) => u.is_staff)
}

async function handleDelete(user: AdminUser) {
  if (!confirm(t('admin.deleteUserConfirm', { username: user.username }))) return
  await deleteUser(user.id)
  await load()
}
</script>

<template>
  <div>
    <PageHeader :icon="Shield" :title="$t('admin.usersTitle')" />

    <p v-if="accessDenied" class="error">{{ $t('admin.accessDenied') }}</p>

    <template v-else>
      <div class="field" style="max-width: 320px">
        <label for="admin-search">{{ $t('admin.search') }}</label>
        <input id="admin-search" v-model="search" :placeholder="$t('admin.searchPlaceholder')" />
      </div>

      <AsyncState
        v-if="isLoading || !users.length"
        :loading="isLoading"
        :loading-text="$t('common.loading')"
        :empty-text="$t('admin.noUsers')"
      />

      <div v-else class="card admin-table-wrapper">
        <table class="admin-table admin-table--scroll">
          <thead>
            <tr>
              <th>{{ $t('admin.username') }}</th>
              <th>{{ $t('admin.email') }}</th>
              <th>{{ $t('admin.recipeCount') }}</th>
              <th>{{ $t('admin.active') }}</th>
              <th>{{ $t('admin.staff') }}</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>{{ user.username }}</td>
              <td>{{ user.email }}</td>
              <td>{{ user.recipe_count }}</td>
              <template v-if="user.id !== authStore.user?.id">
                <td>
                  <button
                    type="button"
                    class="status-toggle"
                    :class="{ 'is-on': user.is_active }"
                    :aria-pressed="user.is_active"
                    :title="$t('admin.toggleActiveHint')"
                    @click="toggleActive(user)"
                  >
                    <span class="status-toggle-dot" aria-hidden="true" />
                    {{ user.is_active ? $t('admin.active') : $t('admin.inactive') }}
                  </button>
                </td>
                <td>
                  <button
                    type="button"
                    class="status-toggle"
                    :class="{ 'is-on': user.is_staff }"
                    :aria-pressed="user.is_staff"
                    :title="$t('admin.toggleStaffHint')"
                    @click="toggleStaff(user)"
                  >
                    <span class="status-toggle-dot" aria-hidden="true" />
                    {{ user.is_staff ? $t('admin.staff') : $t('admin.notStaff') }}
                  </button>
                </td>
                <td>
                  <button
                    class="danger icon-btn"
                    :aria-label="$t('admin.deleteUser')"
                    @click="handleDelete(user)"
                  >
                    <Trash2 :size="16" />
                  </button>
                </td>
              </template>
              <template v-else>
                <td colspan="3" class="muted this-is-you">{{ $t('admin.thisIsYou') }}</td>
              </template>
            </tr>
          </tbody>
        </table>
      </div>

      <Pagination :page="page" :count="count" @update:page="goToPage" />
    </template>
  </div>
</template>

<style scoped>
.admin-table-wrapper {
  overflow-x: auto;
}

.admin-table--scroll {
  white-space: nowrap;
}

/* La ligne de l'admin connecté porte une phrase, pas des boutons : elle doit pouvoir passer
   à la ligne au lieu de déborder de la table (nowrap hérité de .admin-table--scroll). */
.this-is-you {
  white-space: normal;
  min-width: 14rem;
  max-width: 22rem;
  font-size: 0.9rem;
}

/* Interrupteur d'état (actif / staff) : bordure + pastille pour qu'il se lise comme un
   bouton cliquable et non comme un simple badge, aria-pressed reflétant l'état. */
.status-toggle {
  min-height: 2.25rem;
  padding: 0.35rem 0.85rem;
  border: 1.5px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-muted);
  font-size: 0.9rem;
}

.status-toggle:hover {
  background: var(--color-surface-muted);
  border-color: var(--color-primary);
}

.status-toggle:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.status-toggle.is-on {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}

.status-toggle.is-on:hover {
  background: var(--color-primary-soft-hover);
}

.status-toggle-dot {
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 999px;
  background: var(--color-muted);
}

.status-toggle.is-on .status-toggle-dot {
  background: var(--color-primary);
}
</style>
