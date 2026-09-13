import client from './client'

export function importRecipeFromUrl(url: string): Promise<{ task_id: string }> {
  return client.post('import/url/', { url }).then((r) => r.data)
}
