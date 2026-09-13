import client from './client'
import type { AdminUserListParams, Paginated } from '../types/api'
import type { AdminUser } from '../types/models'

export function listUsers(params: AdminUserListParams = {}): Promise<Paginated<AdminUser>> {
  return client.get('admin/users/', { params }).then((r) => r.data)
}

export function updateUser(
  id: number | string,
  payload: Partial<Pick<AdminUser, 'is_active' | 'is_staff'>>,
): Promise<AdminUser> {
  return client.patch(`admin/users/${id}/`, payload).then((r) => r.data)
}

export function deleteUser(id: number | string) {
  return client.delete(`admin/users/${id}/`)
}
