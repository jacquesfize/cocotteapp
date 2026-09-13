import client from './client'

export function listUsers(params = {}) {
  return client.get('admin/users/', { params }).then((r) => r.data)
}

export function updateUser(id, payload) {
  return client.patch(`admin/users/${id}/`, payload).then((r) => r.data)
}

export function deleteUser(id) {
  return client.delete(`admin/users/${id}/`)
}
