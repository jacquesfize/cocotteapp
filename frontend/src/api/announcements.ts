import client from './client'
import type { Announcement } from '../types/models'

export function listAnnouncements(): Promise<Announcement[]> {
  return client.get('announcements/').then((r) => r.data)
}
