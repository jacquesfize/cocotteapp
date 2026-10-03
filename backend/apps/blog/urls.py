from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import BlogImageUploadView, BlogPostCommentHideView, BlogPostCommentListCreateView, BlogPostViewSet

router = DefaultRouter()
router.register("blog/posts", BlogPostViewSet, basename="blog-post")

urlpatterns = [
    path("blog/images/", BlogImageUploadView.as_view(), name="blog-image-upload"),
    path(
        "blog/posts/<int:post_id>/comments/",
        BlogPostCommentListCreateView.as_view(),
        name="blog-post-comments",
    ),
    path(
        "blog/posts/<int:post_id>/comments/<int:pk>/hide/",
        BlogPostCommentHideView.as_view(),
        name="blog-post-comment-hide",
    ),
] + router.urls
