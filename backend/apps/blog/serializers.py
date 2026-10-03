import re

from rest_framework import serializers

from .models import BlogImage, BlogPost, BlogPostComment
from .sanitize import clean_post_html, html_to_text

EXCERPT_LENGTH = 220
FIRST_IMG_SRC = re.compile(r'<img[^>]*\ssrc="([^"]+)"')


class BlogPostListSerializer(serializers.ModelSerializer):
    """Lightweight representation for the post list: an excerpt and a cover image (the post's
    first image) instead of the full HTML content."""

    author = serializers.CharField(source="author.username", read_only=True)
    excerpt = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "author",
            "author_id",
            "excerpt",
            "cover_image",
            "comments_enabled",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_excerpt(self, obj):
        text = " ".join(html_to_text(obj.content).split())
        if len(text) <= EXCERPT_LENGTH:
            return text
        return text[:EXCERPT_LENGTH].rsplit(" ", 1)[0] + "…"

    def get_cover_image(self, obj):
        if obj.cover_image:
            return obj.cover_image.url
        match = FIRST_IMG_SRC.search(obj.content)
        return match.group(1) if match else None


class BlogPostSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username", read_only=True)
    # Set through `PATCH/DELETE /api/blog/posts/{id}/cover/` (multipart), read-only here.
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "author",
            "author_id",
            "content",
            "cover_image",
            "comments_enabled",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "author", "author_id", "created_at", "updated_at"]

    def get_cover_image(self, obj):
        return obj.cover_image.url if obj.cover_image else None

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Le titre ne peut pas être vide.")
        return value

    def validate_content(self, value):
        return clean_post_html(value)


class BlogPostCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(max_length=80, required=False, allow_blank=True)
    body = serializers.CharField(max_length=2000)
    username = serializers.SerializerMethodField()

    class Meta:
        model = BlogPostComment
        fields = ["id", "post", "author_name", "username", "body", "is_hidden", "created_at"]
        read_only_fields = ["id", "post", "username", "is_hidden", "created_at"]

    def get_username(self, obj):
        return obj.user.username if obj.user_id else None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.context.get("can_moderate"):
            self.fields.pop("is_hidden", None)

    def validate_body(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Le commentaire ne peut pas être vide.")
        return value

    def validate_author_name(self, value):
        return value.strip()

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not attrs.get("author_name"):
            if user is not None and user.is_authenticated:
                attrs["author_name"] = user.username
            else:
                raise serializers.ValidationError({"author_name": "Merci d'indiquer un nom."})
        return attrs

    def create(self, validated_data):
        user = getattr(self.context.get("request"), "user", None)
        if user is not None and user.is_authenticated:
            validated_data["user"] = user
        return super().create(validated_data)


def validate_image_size(value):
    max_size = 8 * 1024 * 1024
    if value.size > max_size:
        raise serializers.ValidationError("L'image ne doit pas dépasser 8 Mo.")
    return value


class BlogCoverUploadSerializer(serializers.Serializer):
    cover_image = serializers.ImageField(validators=[validate_image_size])


class BlogImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogImage
        fields = ["id", "image", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_image(self, value):
        return validate_image_size(value)

    def to_representation(self, instance):
        # Relative URL (`/media/blog/…`): it's what the sanitizer accepts in a post's `<img src>`,
        # and it keeps working behind any domain or reverse proxy.
        data = super().to_representation(instance)
        data["image"] = instance.image.url
        return data
