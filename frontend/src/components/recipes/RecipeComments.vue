<script setup lang="ts">
import CommentThread from '../shared/CommentThread.vue'
import { createRecipeComment, hideRecipeComment, listRecipeComments } from '../../api/recipes'

const props = defineProps<{
  recipeId: number | string
  canModerate: boolean
}>()
</script>

<template>
  <CommentThread
    :load="() => listRecipeComments(props.recipeId)"
    :create="(payload) => createRecipeComment(props.recipeId, payload)"
    :hide="(commentId) => hideRecipeComment(props.recipeId, commentId)"
    :can-moderate="canModerate"
    :placeholder="$t('comments.commentPlaceholder')"
  />
</template>
