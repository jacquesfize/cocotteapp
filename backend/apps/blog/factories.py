import factory

from apps.accounts.factories import UserFactory

from .models import BlogPost, BlogPostComment


class BlogPostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BlogPost

    title = factory.Sequence(lambda n: f"Article {n}")
    author = factory.SubFactory(UserFactory)
    content = "<p>Bonjour à tous !</p>"


class BlogPostCommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BlogPostComment

    post = factory.SubFactory(BlogPostFactory)
    author_name = factory.Sequence(lambda n: f"Invité {n}")
    body = factory.Sequence(lambda n: f"Super article #{n} !")
