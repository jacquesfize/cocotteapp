from django.contrib import admin

from .models import BlogImage, BlogPost, BlogPostComment


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "created_at", "updated_at", "comments_enabled"]
    list_filter = ["comments_enabled"]
    search_fields = ["title", "author__username"]


@admin.register(BlogPostComment)
class BlogPostCommentAdmin(admin.ModelAdmin):
    list_display = ["post", "author_name", "user", "created_at", "is_hidden"]
    list_filter = ["is_hidden"]
    search_fields = ["author_name", "body", "post__title"]


@admin.register(BlogImage)
class BlogImageAdmin(admin.ModelAdmin):
    list_display = ["image", "owner", "created_at"]
