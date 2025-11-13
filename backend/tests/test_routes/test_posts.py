"""
Tests para endpoints de publicaciones
"""
import pytest
from datetime import datetime, timedelta
from app.models.post import Post, PostStatus
from app.models.social_account import SocialAccount, SocialPlatform


class TestPostEndpoints:
    """Tests para endpoints de publicaciones"""

    @pytest.fixture
    def social_account(self, db_session, test_user):
        """Cuenta social de prueba"""
        account = SocialAccount(
            user_id=test_user.id,
            platform=SocialPlatform.FACEBOOK,
            platform_user_id="fb123",
            platform_username="testfb",
            access_token="fb_token"
        )
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)
        return account

    def test_create_post_draft(self, client, auth_headers, social_account):
        """Test crear borrador de publicación"""
        response = client.post(
            "/api/posts/",
            headers=auth_headers,
            json={
                "content": "Test post content",
                "image_url": "https://example.com/image.jpg",
                "platform_account_ids": [social_account.id]
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Test post content"
        assert data["status"] == "draft"
        assert len(data["platforms"]) == 1

    def test_create_scheduled_post(self, client, auth_headers, social_account):
        """Test crear publicación programada"""
        future_time = datetime.utcnow() + timedelta(hours=2)

        response = client.post(
            "/api/posts/",
            headers=auth_headers,
            json={
                "content": "Scheduled post",
                "platform_account_ids": [social_account.id],
                "scheduled_at": future_time.isoformat()
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "scheduled"
        assert data["scheduled_at"] is not None

    def test_create_post_past_date(self, client, auth_headers, social_account):
        """Test crear post con fecha pasada falla"""
        past_time = datetime.utcnow() - timedelta(hours=2)

        response = client.post(
            "/api/posts/",
            headers=auth_headers,
            json={
                "content": "Past post",
                "platform_account_ids": [social_account.id],
                "scheduled_at": past_time.isoformat()
            }
        )

        assert response.status_code == 400

    def test_create_post_no_accounts(self, client, auth_headers):
        """Test crear post sin cuentas sociales falla"""
        response = client.post(
            "/api/posts/",
            headers=auth_headers,
            json={
                "content": "No accounts",
                "platform_account_ids": []
            }
        )

        assert response.status_code == 422

    def test_create_post_invalid_account(self, client, auth_headers):
        """Test crear post con cuenta inválida"""
        response = client.post(
            "/api/posts/",
            headers=auth_headers,
            json={
                "content": "Invalid account",
                "platform_account_ids": [99999]
            }
        )

        assert response.status_code == 400

    def test_get_user_posts(self, client, auth_headers, db_session, test_user, social_account):
        """Test obtener publicaciones del usuario"""
        # Crear posts de prueba
        for i in range(3):
            post = Post(
                user_id=test_user.id,
                content=f"Post {i}",
                status=PostStatus.DRAFT
            )
            db_session.add(post)
        db_session.commit()

        response = client.get("/api/posts/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_post_by_id(self, client, auth_headers, db_session, test_user):
        """Test obtener publicación por ID"""
        post = Post(
            user_id=test_user.id,
            content="Specific post",
            status=PostStatus.DRAFT
        )
        db_session.add(post)
        db_session.commit()

        response = client.get(f"/api/posts/{post.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == post.id
        assert data["content"] == "Specific post"

    def test_get_nonexistent_post(self, client, auth_headers):
        """Test obtener post inexistente"""
        response = client.get("/api/posts/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_update_post(self, client, auth_headers, db_session, test_user, social_account):
        """Test actualizar publicación"""
        post = Post(
            user_id=test_user.id,
            content="Original content",
            status=PostStatus.DRAFT
        )
        db_session.add(post)
        db_session.commit()

        response = client.put(
            f"/api/posts/{post.id}",
            headers=auth_headers,
            json={
                "content": "Updated content",
                "image_url": "https://example.com/new.jpg"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated content"
        assert data["image_url"] == "https://example.com/new.jpg"

    def test_update_published_post_fails(self, client, auth_headers, db_session, test_user):
        """Test actualizar post publicado falla"""
        post = Post(
            user_id=test_user.id,
            content="Published",
            status=PostStatus.PUBLISHED,
            published_at=datetime.utcnow()
        )
        db_session.add(post)
        db_session.commit()

        response = client.put(
            f"/api/posts/{post.id}",
            headers=auth_headers,
            json={"content": "Try to update"}
        )

        assert response.status_code == 400

    def test_delete_post(self, client, auth_headers, db_session, test_user):
        """Test eliminar publicación"""
        post = Post(
            user_id=test_user.id,
            content="To delete",
            status=PostStatus.DRAFT
        )
        db_session.add(post)
        db_session.commit()
        post_id = post.id

        response = client.delete(f"/api/posts/{post_id}", headers=auth_headers)

        assert response.status_code == 200

        # Verificar que fue eliminado
        deleted = db_session.query(Post).filter(Post.id == post_id).first()
        assert deleted is None

    def test_get_posts_pagination(self, client, auth_headers, db_session, test_user):
        """Test paginación de posts"""
        # Crear 25 posts
        for i in range(25):
            post = Post(
                user_id=test_user.id,
                content=f"Post {i}",
                status=PostStatus.DRAFT
            )
            db_session.add(post)
        db_session.commit()

        # Primera página (20 items por defecto)
        response1 = client.get("/api/posts/?skip=0&limit=20", headers=auth_headers)
        assert response.status_code == 200
        assert len(response1.json()) == 20

        # Segunda página
        response2 = client.get("/api/posts/?skip=20&limit=20", headers=auth_headers)
        assert response2.status_code == 200
        assert len(response2.json()) == 5

    def test_create_post_unauthorized(self, client):
        """Test crear post sin autenticación"""
        response = client.post(
            "/api/posts/",
            json={
                "content": "Unauthorized",
                "platform_account_ids": [1]
            }
        )

        assert response.status_code == 401
