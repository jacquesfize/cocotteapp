from rest_framework.pagination import PageNumberPagination


class BlogPostPagination(PageNumberPagination):
    page_size = 10
