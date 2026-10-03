import client from './client'
import type { BlogPostListParams, Paginated } from '../types/api'
import type { BlogAuthor, BlogImage, BlogPost, BlogPostComment, BlogPostInput, BlogPostSummary, CommentInput } from '../types/models'

export function listBlogPosts(params: BlogPostListParams = {}): Promise<Paginated<BlogPostSummary>> {
  return client.get('blog/posts/', { params }).then((r) => r.data)
}

export function listBlogAuthors(): Promise<BlogAuthor[]> {
  return client.get('blog/posts/authors/').then((r) => r.data)
}

export function getBlogPost(id: number | string): Promise<BlogPost> {
  return client.get(`blog/posts/${id}/`).then((r) => r.data)
}

export function createBlogPost(payload: BlogPostInput): Promise<BlogPost> {
  return client.post('blog/posts/', payload).then((r) => r.data)
}

export function updateBlogPost(id: number | string, payload: BlogPostInput): Promise<BlogPost> {
  return client.patch(`blog/posts/${id}/`, payload).then((r) => r.data)
}

export function deleteBlogPost(id: number | string) {
  return client.delete(`blog/posts/${id}/`)
}

export function uploadBlogCover(id: number | string, file: File): Promise<BlogPost> {
  const formData = new FormData()
  formData.append('cover_image', file)
  return client.patch(`blog/posts/${id}/cover/`, formData).then((r) => r.data)
}

export function deleteBlogCover(id: number | string): Promise<BlogPost> {
  return client.delete(`blog/posts/${id}/cover/`).then((r) => r.data)
}

export function uploadBlogImage(file: File): Promise<BlogImage> {
  const formData = new FormData()
  formData.append('image', file)
  return client.post('blog/images/', formData).then((r) => r.data)
}

export function listBlogPostComments(postId: number | string): Promise<Paginated<BlogPostComment>> {
  return client.get(`blog/posts/${postId}/comments/`).then((r) => r.data)
}

export function createBlogPostComment(postId: number | string, payload: CommentInput): Promise<BlogPostComment> {
  return client.post(`blog/posts/${postId}/comments/`, payload).then((r) => r.data)
}

export function hideBlogPostComment(postId: number | string, commentId: number | string): Promise<BlogPostComment> {
  return client.post(`blog/posts/${postId}/comments/${commentId}/hide/`).then((r) => r.data)
}
