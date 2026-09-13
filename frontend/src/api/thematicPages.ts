import client from './client'
import type { ThematicPage } from '../types/models'

export function listThematicPages(): Promise<ThematicPage[]> {
  return client.get('thematic-pages/').then((r) => r.data)
}
