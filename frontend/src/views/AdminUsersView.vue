<script setup lang="ts">
import { Trash2 } from '@lucide/vue'
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import Pagination from '../components/Pagination.vue'
import { deleteUser, listUsers, updateUser } from '../api/admin'
import { useAuthStore } from '../stores/auth'
import type { AdminUserListParams } from '../types/api'
import type { AdminUser } from '../types/models'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const users = ref<AdminUser[]>([])
const count = ref(0)
const page = ref(Number(route.query.page) || 1)
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
    if ((err as { response?: { status?: number } }).response?.status === 403) accessDenied.value = true
  } finally {
    isLoading.value = false
  }
}

function goToPage(newPage: number) {
  page.value = newPage
  load()
}

let debounceTimer: ReturnType<typeof setTimeout> | undefined
watch(search, () => {
  page.value = 1
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(load, 300)
})

onMounted(load)

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
    <h1>{{ $t('admin.usersTitle') }}</h1>

    <p v-if="accessDenied" class="error">{{ $t('admin.accessDenied') }}</p>

    <template v-else>
      <div class="field" style="max-width: 320px">
        <label for="admin-search">{{ $t('admin.search') }}</label>
        <input id="admin-search" v-model="search" :placeholder="$t('admin.searchPlaceholder')" />
      </div>

      <p v-if="isLoading" class="muted">{{ $t('common.loading') }}</p>
      <p v-else-if="!users.length" class="muted">{{ $t('admin.noUsers') }}</p>

      <div v-else class="card table-wrapper">
        <table class="admin-table">
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
                  <button class="secondary" @click="toggleActive(user)">
                    {{ user.is_active ? $t('admin.active') : $t('admin.inactive') }}
                  </button>
                </td>
                <td>
                  <button class="secondary" @click="toggleStaff(user)">
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
                <td colspan="3" class="muted">{{ $t('admin.thisIsYou') }}</td>
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
.table-wrapper {
  overflow-x: auto;
  padding: 0;
}

.admin-table {
  width: 100%;
  border-collapse: collapse;
  white-space: nowrap;
}

.admin-table th,
.admin-table td {
  text-align: left;
  padding: 0.85rem 1.25rem;
}

.admin-table thead th {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--color-muted);
  border-bottom: 1px solid var(--color-border);
}

.admin-table tbody tr:not(:last-child) td {
  border-bottom: 1px solid var(--color-border);
}
</style>
