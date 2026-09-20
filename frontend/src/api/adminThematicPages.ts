import client from './client'
import type { AdminThematicPageInput } from '../types/api'
import type { AdminThematicPage } from '../types/models'

export function listThematicPages(): Promise<AdminThematicPage[]> {
  return client.get('admin/thematic-pages/').then((r) => r.data)
}

export function getThematicPage(id: number | string): Promise<AdminThematicPage> {
  return client.get(`admin/thematic-pages/${id}/`).then((r) => r.data)
}

export function createThematicPage(payload: AdminThematicPageInput): Promise<AdminThematicPage> {
  return client.post('admin/thematic-pages/', payload).then((r) => r.data)
}

export function updateThematicPage(
  id: number | string,
  payload: Partial<AdminThematicPageInput>,
): Promise<AdminThematicPage> {
  return client.patch(`admin/thematic-pages/${id}/`, payload).then((r) => r.data)
}

export function uploadThematicPageImage(id: number | string, file: File): Promise<AdminThematicPage> {
  const formData = new FormData()
  formData.append('image', file)
  return client.patch(`admin/thematic-pages/${id}/image/`, formData).then((r) => r.data)
}

export function removeThematicPageImage(id: number | string): Promise<AdminThematicPage> {
  return client.delete(`admin/thematic-pages/${id}/image/`).then((r) => r.data)
}

export function deleteThematicPage(id: number | string) {
  return client.delete(`admin/thematic-pages/${id}/`)
}
