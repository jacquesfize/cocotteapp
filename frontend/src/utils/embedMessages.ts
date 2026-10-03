/** postMessage contract between the recipe embed view (inside the iframe) and the blog post
 * page hosting it, so the iframe can grow to its content's height. Same-origin only. */
export const EMBED_HEIGHT_MESSAGE = 'cocotte:embed-height'

export interface EmbedHeightMessage {
  type: typeof EMBED_HEIGHT_MESSAGE
  height: number
}

export function isEmbedHeightMessage(data: unknown): data is EmbedHeightMessage {
  return (
    typeof data === 'object' &&
    data !== null &&
    (data as EmbedHeightMessage).type === EMBED_HEIGHT_MESSAGE &&
    typeof (data as EmbedHeightMessage).height === 'number'
  )
}
