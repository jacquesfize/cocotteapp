from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.audit import StaffAuditMixin, record_staff_action
from apps.accounts.models import AuditLog
from apps.recipes.permissions import IsAuthorOrReadOnly
from apps.recipes.throttles import CommentCreateAnonThrottle

from .models import BlogPost, BlogPostComment
from .pagination import BlogPostPagination
from .permissions import IsPostAuthorOrStaff
from .serializers import (
    BlogCoverUploadSerializer,
    BlogImageSerializer,
    BlogPostCommentSerializer,
    BlogPostListSerializer,
    BlogPostSerializer,
)


def _can_moderate(user, post):
    return bool(user and user.is_authenticated and (user.is_staff or post.author_id == user.id))


class BlogPostViewSet(StaffAuditMixin, viewsets.ModelViewSet):
    """`/api/blog/posts/` — anyone can read, any logged-in user can write a post, only its author
    (or staff) can edit or delete it. `?author=<id>` lists one user's posts, `?search=` looks in
    the title, the content and the author's username."""

    queryset = BlogPost.objects.select_related("author")
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["author"]
    search_fields = ["title", "content", "author__username"]
    pagination_class = BlogPostPagination

    def get_serializer_class(self):
        if self.action == "list":
            return BlogPostListSerializer
        return BlogPostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=["patch", "delete"], parser_classes=[MultiPartParser, FormParser])
    def cover(self, request, pk=None):
        """`PATCH /api/blog/posts/{id}/cover/` (multipart `cover_image`) sets the post's cover
        image, `DELETE` removes it. Author or staff only, like any other edit of the post."""
        post = self.get_object()
        if post.cover_image:
            post.cover_image.delete(save=False)
        if request.method == "DELETE":
            post.cover_image = None
        else:
            serializer = BlogCoverUploadSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            post.cover_image = serializer.validated_data["cover_image"]
        post.save()
        return Response(BlogPostSerializer(post, context=self.get_serializer_context()).data)

    @action(detail=False, methods=["get"], pagination_class=None)
    def authors(self, request):
        """`GET /api/blog/posts/authors/` — users who wrote at least one post, for the author
        filter of the blog list."""
        authors = (
            get_user_model()
            .objects.filter(blog_posts__isnull=False)
            .distinct()
            .order_by("username")
            .values("id", "username")
        )
        return Response(list(authors))


class BlogPostCommentListCreateView(generics.ListCreateAPIView):
    """`GET`/`POST /api/blog/posts/{post_id}/comments/` — same rules as recipe comments (no
    account required, hidden comments only listed for the post's author or staff), except that
    posting is refused while the author has disabled comments on the post."""

    serializer_class = BlogPostCommentSerializer
    permission_classes = [AllowAny]

    def get_throttles(self):
        if self.request.method == "POST":
            return [CommentCreateAnonThrottle()]
        return []

    def get_post(self):
        if not hasattr(self, "_post"):
            self._post = get_object_or_404(BlogPost, pk=self.kwargs["post_id"])
        return self._post

    def get_queryset(self):
        post = self.get_post()
        queryset = post.comments.all()
        if not _can_moderate(self.request.user, post):
            queryset = queryset.filter(is_hidden=False)
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["can_moderate"] = _can_moderate(self.request.user, self.get_post())
        return context

    def create(self, request, *args, **kwargs):
        if not self.get_post().comments_enabled:
            return Response(
                {"detail": "Les commentaires sont désactivés pour cet article."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(post=self.get_post())


class BlogPostCommentHideView(APIView):
    """`POST /api/blog/posts/{post_id}/comments/{id}/hide/` — toggles `is_hidden`, restricted to
    the post's author or staff."""

    permission_classes = [IsPostAuthorOrStaff]

    def post(self, request, post_id, pk):
        comment = get_object_or_404(BlogPostComment, pk=pk, post_id=post_id)
        self.check_object_permissions(request, comment)
        comment.is_hidden = not comment.is_hidden
        comment.save(update_fields=["is_hidden"])
        record_staff_action(
            request,
            AuditLog.Action.HIDE_COMMENT if comment.is_hidden else AuditLog.Action.UNHIDE_COMMENT,
            comment,
        )
        serializer = BlogPostCommentSerializer(comment, context={"request": request, "can_moderate": True})
        return Response(serializer.data)


class BlogImageUploadView(generics.CreateAPIView):
    """`POST /api/blog/images/` — uploads an image from the blog editor and returns its URL, to
    be inserted as an `<img>` in the post's content."""

    serializer_class = BlogImageSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
