"""
Tests para modelos de base de datos
"""
import pytest
from datetime import datetime
from app.models.user import User
from app.models.social_account import SocialAccount, SocialPlatform
from app.models.post import Post, PostStatus, PostPlatform, PlatformPostStatus
from app.utils.auth import get_password_hash, verify_password


class TestUserModel:
    """Tests para el modelo User"""

    def test_create_user(self, db_session):
        """Test crear usuario"""
        user = User(
            email="newuser@example.com",
            username="newuser",
            hashed_password=get_password_hash("password123"),
            full_name="New User"
        )
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.username == "newuser"
        assert user.is_active is True
        assert user.is_verified is False
        assert user.created_at is not None

    def test_password_hashing(self):
        """Test hash y verificación de contraseña"""
        password = "securepassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_user_relationships(self, db_session, test_user):
        """Test relaciones del usuario"""
        # Crear cuenta social
        social_account = SocialAccount(
            user_id=test_user.id,
            platform=SocialPlatform.FACEBOOK,
            platform_user_id="123456",
            platform_username="testfb",
            access_token="fake_token"
        )
        db_session.add(social_account)

        # Crear post
        post = Post(
            user_id=test_user.id,
            content="Test post",
            status=PostStatus.DRAFT
        )
        db_session.add(post)
        db_session.commit()

        # Verificar relaciones
        assert len(test_user.social_accounts) == 1
        assert len(test_user.posts) == 1
        assert test_user.social_accounts[0].platform == SocialPlatform.FACEBOOK
        assert test_user.posts[0].content == "Test post"


class TestSocialAccountModel:
    """Tests para el modelo SocialAccount"""

    def test_create_social_account(self, db_session, test_user):
        """Test crear cuenta social"""
        account = SocialAccount(
            user_id=test_user.id,
            platform=SocialPlatform.INSTAGRAM,
            platform_user_id="ig123",
            platform_username="test_ig",
            access_token="ig_token",
            refresh_token="ig_refresh"
        )
        db_session.add(account)
        db_session.commit()

        assert account.id is not None
        assert account.platform == SocialPlatform.INSTAGRAM
        assert account.is_active is True
        assert account.user_id == test_user.id

    def test_multiple_platforms_per_user(self, db_session, test_user):
        """Test múltiples plataformas por usuario"""
        platforms = [
            SocialPlatform.FACEBOOK,
            SocialPlatform.INSTAGRAM,
            SocialPlatform.TWITTER
        ]

        for platform in platforms:
            account = SocialAccount(
                user_id=test_user.id,
                platform=platform,
                platform_user_id=f"{platform}_123",
                access_token=f"{platform}_token"
            )
            db_session.add(account)

        db_session.commit()

        accounts = db_session.query(SocialAccount).filter(
            SocialAccount.user_id == test_user.id
        ).all()

        assert len(accounts) == 3
        assert set(a.platform for a in accounts) == set(platforms)


class TestPostModel:
    """Tests para el modelo Post"""

    def test_create_post(self, db_session, test_user):
        """Test crear publicación"""
        post = Post(
            user_id=test_user.id,
            content="Test content",
            image_url="https://example.com/image.jpg",
            status=PostStatus.DRAFT
        )
        db_session.add(post)
        db_session.commit()

        assert post.id is not None
        assert post.status == PostStatus.DRAFT
        assert post.content == "Test content"
        assert post.created_at is not None

    def test_post_with_platforms(self, db_session, test_user):
        """Test post con múltiples plataformas"""
        # Crear cuentas sociales
        fb_account = SocialAccount(
            user_id=test_user.id,
            platform=SocialPlatform.FACEBOOK,
            platform_user_id="fb123",
            access_token="fb_token"
        )
        tw_account = SocialAccount(
            user_id=test_user.id,
            platform=SocialPlatform.TWITTER,
            platform_user_id="tw123",
            access_token="tw_token"
        )
        db_session.add_all([fb_account, tw_account])
        db_session.commit()

        # Crear post
        post = Post(
            user_id=test_user.id,
            content="Multi-platform post",
            status=PostStatus.SCHEDULED
        )
        db_session.add(post)
        db_session.commit()

        # Agregar plataformas
        fb_platform = PostPlatform(
            post_id=post.id,
            social_account_id=fb_account.id,
            status=PlatformPostStatus.PENDING
        )
        tw_platform = PostPlatform(
            post_id=post.id,
            social_account_id=tw_account.id,
            status=PlatformPostStatus.PENDING
        )
        db_session.add_all([fb_platform, tw_platform])
        db_session.commit()

        # Verificar
        assert len(post.platforms) == 2
        assert all(p.status == PlatformPostStatus.PENDING for p in post.platforms)

    def test_post_cascade_delete(self, db_session, test_user):
        """Test eliminación en cascada"""
        post = Post(
            user_id=test_user.id,
            content="Test",
            status=PostStatus.DRAFT
        )
        db_session.add(post)
        db_session.commit()
        post_id = post.id

        # Eliminar usuario debe eliminar post
        db_session.delete(test_user)
        db_session.commit()

        deleted_post = db_session.query(Post).filter(Post.id == post_id).first()
        assert deleted_post is None
