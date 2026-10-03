import { mergeAttributes, Node } from '@tiptap/vue-3'

/** Keyboard shortcut opening the "insert a recipe" dialog, in TipTap notation (Mod = Ctrl or ⌘). */
export const RECIPE_EMBED_SHORTCUT = 'Mod-Alt-r'

export function recipeEmbedSrc(recipeId: number | string): string {
  return `/embed/recipes/${recipeId}`
}

export interface RecipeEmbedOptions {
  /** Called by the keyboard shortcut: the editor component opens its recipe picker. */
  onRequestInsert: (() => void) | null
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    recipeEmbed: {
      insertRecipeEmbed: (attrs: { recipeId: number; title: string }) => ReturnType
    }
  }
}

/**
 * A Cocotte recipe embedded in a blog post, stored in the HTML as
 * `<iframe data-cocotte-recipe="42" src="/embed/recipes/42">` — the only kind of iframe the
 * backend sanitizer keeps (see `apps/blog/sanitize.py`). An atom node: it's inserted, moved and
 * deleted as a whole, never edited from inside.
 */
export const RecipeEmbed = Node.create<RecipeEmbedOptions>({
  name: 'recipeEmbed',
  group: 'block',
  atom: true,
  draggable: true,

  addOptions() {
    return { onRequestInsert: null }
  },

  addAttributes() {
    return {
      recipeId: {
        default: null,
        parseHTML: (element) => element.getAttribute('data-cocotte-recipe'),
        renderHTML: (attributes) => ({ 'data-cocotte-recipe': attributes.recipeId }),
      },
      title: {
        default: '',
        parseHTML: (element) => element.getAttribute('title') ?? '',
        renderHTML: (attributes) => ({ title: attributes.title }),
      },
    }
  },

  parseHTML() {
    return [{ tag: 'iframe[data-cocotte-recipe]' }]
  },

  renderHTML({ node, HTMLAttributes }) {
    return [
      'iframe',
      mergeAttributes(HTMLAttributes, { src: recipeEmbedSrc(node.attrs.recipeId), loading: 'lazy' }),
    ]
  },

  addCommands() {
    return {
      insertRecipeEmbed:
        (attrs) =>
        ({ commands }) =>
          commands.insertContent({ type: this.name, attrs }),
    }
  },

  addKeyboardShortcuts() {
    return {
      [RECIPE_EMBED_SHORTCUT]: () => {
        if (!this.options.onRequestInsert) return false
        this.options.onRequestInsert()
        return true
      },
    }
  },
})
