import client from './client'

export function importRecipeFromUrl(url) {
  return client.post('import/url/', { url }).then((r) => r.data)
}
