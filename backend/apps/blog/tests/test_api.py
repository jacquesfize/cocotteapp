from io import BytesIO

import pytest
from django.core.cache import cache
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.blog.factories import BlogPostCommentFactory, BlogPostFactory
from apps.blog.models import BlogPost


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()


def _fake_image_file():
    buffer = BytesIO()
    Image.new("RGB", (10, 10), color="red").save(buffer, format="JPEG")
    buffer.seek(0)
    buffer.name = "test.jpg"
    return buffer


@pytest.mark.django_db
def test_anonymous_can_list_and_read_posts():
    post = BlogPostFactory(title="Les courges", content="<p>" + "Une courge. " * 40 + '</p><img src="/media/blog/c.jpg">')

    client = APIClient()
    listing = client.get("/api/blog/posts/")
    detail = client.get(f"/api/blog/posts/{post.id}/")

    assert listing.status_code == 200
    item = listing.data["results"][0]
    assert item["title"] == "Les courges"
    assert item["author"] == post.author.username
    assert "content" not in item
    assert item["excerpt"].endswith("…") and len(item["excerpt"]) <= 221
    assert item["cover_image"] == "/media/blog/c.jpg"
    assert detail.status_code == 200
    assert detail.data["content"].startswith("<p>Une courge.")


@pytest.mark.django_db
def test_excerpt_separates_blocks_and_decodes_entities():
    BlogPostFactory(content="<p>Fin.</p><h2>Titre</h2><p>Sel &amp; poivre</p>")

    response = APIClient().get("/api/blog/posts/")

    assert response.data["results"][0]["excerpt"] == "Fin. Titre Sel & poivre"


@pytest.mark.django_db
def test_posts_can_be_filtered_by_author():
    mine = BlogPostFactory()
    BlogPostFactory()

    response = APIClient().get(f"/api/blog/posts/?author={mine.author_id}")

    assert [p["id"] for p in response.data["results"]] == [mine.id]


@pytest.mark.django_db
def test_search_looks_in_title_content_and_author():
    by_title = BlogPostFactory(title="Courges rôties", content="<p>x</p>")
    by_content = BlogPostFactory(title="Autre", content="<p>Une soupe de courges</p>")
    by_author = BlogPostFactory(title="Encore", author=UserFactory(username="courgette"))
    BlogPostFactory(title="Rien à voir", content="<p>Tarte</p>")

    response = APIClient().get("/api/blog/posts/?search=courge")

    assert {p["id"] for p in response.data["results"]} == {by_title.id, by_content.id, by_author.id}


@pytest.mark.django_db
def test_authors_lists_each_user_with_posts_once():
    alice = UserFactory(username="alice")
    BlogPostFactory(author=alice)
    BlogPostFactory(author=alice)
    bob = UserFactory(username="bob")
    BlogPostFactory(author=bob)
    UserFactory(username="sans-article")

    response = APIClient().get("/api/blog/posts/authors/")

    assert response.status_code == 200
    assert response.data == [{"id": alice.id, "username": "alice"}, {"id": bob.id, "username": "bob"}]


@pytest.mark.django_db
def test_anonymous_cannot_create_post():
    response = APIClient().post("/api/blog/posts/", {"title": "x", "content": "<p>x</p>"}, format="json")

    assert response.status_code == 401


@pytest.mark.django_db
def test_user_creates_post_as_author_with_sanitized_content():
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user)

    response = client.post(
        "/api/blog/posts/",
        {
            "title": "  Mon menu de la semaine ",
            "content": (
                '<p onclick="steal()">Salut<script>alert(1)</script></p>'
                '<iframe src="/embed/recipes/12" data-cocotte-recipe="12" title="Curry"></iframe>'
                '<iframe src="https://evil.example/"></iframe>'
                '<img src="javascript:alert(1)"><a href="javascript:alert(1)">lien</a>'
            ),
            "comments_enabled": False,
        },
        format="json",
    )

    assert response.status_code == 201
    post = BlogPost.objects.get()
    assert post.author == user
    assert post.title == "Mon menu de la semaine"
    assert post.comments_enabled is False
    assert "script" not in post.content
    assert "onclick" not in post.content
    assert "evil.example" not in post.content
    assert "javascript" not in post.content
    assert '<iframe src="/embed/recipes/12" data-cocotte-recipe="12" title="Curry"></iframe>' in post.content


@pytest.mark.django_db
def test_only_author_or_staff_can_edit_or_delete_post():
    post = BlogPostFactory()
    client = APIClient()

    client.force_authenticate(UserFactory())
    assert client.patch(f"/api/blog/posts/{post.id}/", {"title": "Piraté"}, format="json").status_code == 403
    assert client.delete(f"/api/blog/posts/{post.id}/").status_code == 403

    client.force_authenticate(post.author)
    response = client.patch(f"/api/blog/posts/{post.id}/", {"title": "Corrigé"}, format="json")
    assert response.status_code == 200
    assert response.data["title"] == "Corrigé"

    client.force_authenticate(UserFactory(is_staff=True))
    assert client.delete(f"/api/blog/posts/{post.id}/").status_code == 204
    assert not BlogPost.objects.exists()


@pytest.mark.django_db
def test_author_sets_and_removes_a_cover_image():
    post = BlogPostFactory(content='<p>x</p><img src="/media/blog/inline.jpg">')
    client = APIClient()
    client.force_authenticate(post.author)

    response = client.patch(f"/api/blog/posts/{post.id}/cover/", {"cover_image": _fake_image_file()}, format="multipart")

    assert response.status_code == 200
    assert response.data["cover_image"].startswith("/media/blog/covers/")
    listing = client.get("/api/blog/posts/")
    assert listing.data["results"][0]["cover_image"] == response.data["cover_image"]

    response = client.delete(f"/api/blog/posts/{post.id}/cover/")

    assert response.status_code == 200
    assert response.data["cover_image"] is None
    # Without a cover, the card falls back to the first image of the content.
    assert client.get("/api/blog/posts/").data["results"][0]["cover_image"] == "/media/blog/inline.jpg"


@pytest.mark.django_db
def test_deleting_a_post_deletes_its_cover_image_file():
    post = BlogPostFactory()
    client = APIClient()
    client.force_authenticate(post.author)
    client.patch(f"/api/blog/posts/{post.id}/cover/", {"cover_image": _fake_image_file()}, format="multipart")
    post.refresh_from_db()
    storage, name = post.cover_image.storage, post.cover_image.name
    assert storage.exists(name)

    assert client.delete(f"/api/blog/posts/{post.id}/").status_code == 204

    assert not storage.exists(name)


@pytest.mark.django_db
def test_only_author_or_staff_can_set_the_cover_image():
    post = BlogPostFactory()
    client = APIClient()
    client.force_authenticate(UserFactory())

    response = client.patch(f"/api/blog/posts/{post.id}/cover/", {"cover_image": _fake_image_file()}, format="multipart")

    assert response.status_code == 403


@pytest.mark.django_db
def test_anonymous_can_comment_a_post():
    post = BlogPostFactory()

    response = APIClient().post(
        f"/api/blog/posts/{post.id}/comments/",
        {"author_name": "Camille", "body": "Merci !"},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["author_name"] == "Camille"
    assert "is_hidden" not in response.data
    assert post.comments.get().user is None


@pytest.mark.django_db
def test_authenticated_comment_defaults_author_name_to_username():
    user = UserFactory(username="chef42")
    post = BlogPostFactory()
    client = APIClient()
    client.force_authenticate(user)

    response = client.post(f"/api/blog/posts/{post.id}/comments/", {"body": "Top"}, format="json")

    assert response.status_code == 201
    assert response.data["author_name"] == "chef42"
    assert post.comments.get().user == user


@pytest.mark.django_db
def test_cannot_comment_when_comments_are_disabled():
    post = BlogPostFactory(comments_enabled=False)

    response = APIClient().post(
        f"/api/blog/posts/{post.id}/comments/",
        {"author_name": "Camille", "body": "Merci !"},
        format="json",
    )

    assert response.status_code == 403
    assert not post.comments.exists()


@pytest.mark.django_db
def test_hidden_comments_only_listed_for_post_author_or_staff():
    post = BlogPostFactory()
    BlogPostCommentFactory(post=post, author_name="Visible")
    BlogPostCommentFactory(post=post, author_name="Caché", is_hidden=True)
    client = APIClient()

    response = client.get(f"/api/blog/posts/{post.id}/comments/")
    assert [c["author_name"] for c in response.data["results"]] == ["Visible"]

    client.force_authenticate(post.author)
    response = client.get(f"/api/blog/posts/{post.id}/comments/")
    assert {c["author_name"] for c in response.data["results"]} == {"Visible", "Caché"}
    assert all("is_hidden" in c for c in response.data["results"])


@pytest.mark.django_db
def test_only_post_author_or_staff_can_hide_a_comment():
    comment = BlogPostCommentFactory()
    url = f"/api/blog/posts/{comment.post_id}/comments/{comment.id}/hide/"
    client = APIClient()

    client.force_authenticate(UserFactory())
    assert client.post(url).status_code == 403

    client.force_authenticate(comment.post.author)
    response = client.post(url)
    assert response.status_code == 200
    assert response.data["is_hidden"] is True


@pytest.mark.django_db
def test_user_uploads_blog_image_and_gets_a_relative_url():
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user)

    response = client.post("/api/blog/images/", {"image": _fake_image_file()}, format="multipart")

    assert response.status_code == 201
    assert response.data["image"].startswith("/media/blog/")
    assert user.blog_images.count() == 1


@pytest.mark.django_db
def test_anonymous_cannot_upload_blog_image():
    response = APIClient().post("/api/blog/images/", {"image": _fake_image_file()}, format="multipart")

    assert response.status_code == 401
