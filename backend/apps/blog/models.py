from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver


class BlogPost(models.Model):
    """A blog post written by any user. `content` is HTML produced by the frontend's WYSIWYG
    editor, always stored sanitized (see `sanitize.clean_post_html`); embedded Cocotte recipes
    are kept as `<iframe data-cocotte-recipe="…">` pointing at the frontend's embed view."""

    title = models.CharField(max_length=200)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blog_posts")
    content = models.TextField(blank=True)
    cover_image = models.ImageField(
        upload_to="blog/covers/",
        blank=True,
        null=True,
        help_text="Image d'illustration (en tête de l'article et sur les cartes). À défaut, la "
        "première image du contenu sert de vignette.",
    )
    comments_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


@receiver(post_delete, sender=BlogPost)
def delete_cover_image_file(sender, instance, **kwargs):
    """Removes the cover image file along with its post, however the post is deleted (API,
    Django admin, or cascade when its author's account is deleted)."""
    if instance.cover_image:
        instance.cover_image.delete(save=False)


class BlogPostComment(models.Model):
    """Same rules as `recipes.RecipeComment`: no account required, `user` only stamped when the
    poster is authenticated, `is_hidden` toggled by the post's author or staff."""

    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name="comments")
    author_name = models.CharField(max_length=80)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="blog_comments",
    )
    body = models.TextField()
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author_name} - {self.post.title}"


class BlogImage(models.Model):
    """An image uploaded from the blog editor, referenced by URL from a post's HTML content."""

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blog_images")
    image = models.ImageField(upload_to="blog/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.image.name
