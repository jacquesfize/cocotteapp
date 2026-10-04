import type { TagColor } from '../types/models'

// Même palette fermée que TagColor côté backend (apps/recipes/models.py), dans le même ordre.
// Chaque teinte n'est qu'une base : base.css (.personal-tag) en dérive fond, bordure et texte
// selon le thème clair ou sombre.
export const TAG_COLORS: Record<TagColor, string> = {
  gray: '#8a817c',
  red: '#d64545',
  orange: '#e07a1f',
  yellow: '#c9a400',
  green: '#3f9d4b',
  teal: '#1f9e94',
  blue: '#3b7dd8',
  purple: '#8a5cd1',
  pink: '#d6539b',
}

export const TAG_COLOR_NAMES = Object.keys(TAG_COLORS) as TagColor[]

export function tagHueStyle(color: TagColor | undefined) {
  return { '--tag-hue': TAG_COLORS[color ?? 'gray'] ?? TAG_COLORS.gray }
}
