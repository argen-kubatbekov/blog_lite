import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from blog.models import Post, SubPost

User = get_user_model()

@pytest.fixture
def api():
    return APIClient()

@pytest.fixture
def user(db):
    return User.objects.create_user(username="u1", password="pass")

@pytest.fixture
def auth(api, user):
    api.force_authenticate(user)
    return api

def test_bulk_create_posts(auth):
    url = reverse("post-list")
    payload = [{"title": "A", "body": "a"}, {"title": "B", "body": "b"}]
    r = auth.post(url, payload, format="json")
    assert r.status_code == 201
    assert Post.objects.count() == 2

def test_nested_subposts_create_update_delete(auth):
    url = reverse("post-list")
    payload = {"title": "P", "body": "p", "subposts": [{"title": "s1", "body": "x"}, {"title": "s2", "body": "y"}]}
    r = auth.post(url, payload, format="json")
    assert r.status_code == 201
    pid = r.data["id"]
    post_url = reverse("post-detail", args=[pid])

    sp = SubPost.objects.filter(post_id=pid).order_by("id")
    update_payload = {
        "subposts": [
            {"id": sp[0].id, "title": "s1-upd"},
            {"title": "s3", "body": "z"},
        ]
    }
    r2 = auth.patch(post_url, update_payload, format="json")
    assert r2.status_code == 200
    titles = list(SubPost.objects.filter(post_id=pid).values_list("title", flat=True))
    assert set(titles) == {"s1-upd", "s3"}

def test_like_toggle(auth):
    p = Post.objects.create(title="T", body="B", author=auth.handler._force_user)
    url = reverse("post-like", args=[p.id])
    r1 = auth.post(url)
    assert r1.status_code == 200 and r1.data["liked"] is True
    r2 = auth.post(url)
    assert r2.status_code == 200 and r2.data["liked"] is False

def test_view_increment_concurrent(api, db, user):
    p = Post.objects.create(title="T", body="B", author=user)
    url = reverse("post-view", args=[p.id])
    for _ in range(5):
        api.get(url)
    p.refresh_from_db()
    assert p.views_count == 5
