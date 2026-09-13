import client from './client'

export function listThematicPages() {
  return client.get('thematic-pages/').then((r) => r.data)
}
