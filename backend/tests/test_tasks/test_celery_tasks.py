"""
Tests para tareas de Celery
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from app.tasks.celery_tasks import publish_scheduled_post, check_scheduled_posts
from app.models.post import Post, PostStatus, PostPlatform, PlatformPostStatus
from app.models.social_account import SocialAccount, SocialPlatform


class TestPublishScheduledPost:
    """Tests para tarea de publicación programada"""

    @pytest.fixture
    def test_post_with_platforms(self, db_session, test_user):
        """Post de prueba con plataformas"""
        # Crear cuentas sociales
        fb_account = SocialAccount(
            user_id=test_user.id,
            platform=SocialPlatform.FACEBOOK,
            platform_user_id="fb123",
            platform_username="testfb",
            access_token="fb_token"
        )
        db_session.add(fb_account)
        db_session.commit()

        # Crear post
        post = Post(
            user_id=test_user.id,
            content="Test scheduled post",
            status=PostStatus.SCHEDULED,
            scheduled_at=datetime.utcnow() - timedelta(minutes=5)
        )
        db_session.add(post)
        db_session.commit()

        # Agregar plataforma
        platform = PostPlatform(
            post_id=post.id,
            social_account_id=fb_account.id,
            status=PlatformPostStatus.PENDING
        )
        db_session.add(platform)
        db_session.commit()
        db_session.refresh(post)

        return post

    def test_post_not_found(self, db_session):
        """Test con post inexistente"""
        # Simular la tarea
        result = publish_scheduled_post.apply(args=[99999])

        # Debe retornar error
        assert "error" in result.result

    @patch('app.tasks.celery_tasks.FacebookService')
    def test_publish_facebook_success(self, mock_fb_service, db_session, test_post_with_platforms):
        """Test publicar exitosamente en Facebook"""
        # Mock del servicio
        mock_service = Mock()
        mock_service.get_user_pages.return_value = {
            "data": [{"id": "page_123", "access_token": "page_token"}]
        }
        mock_service.publish_post.return_value = {"id": "fb_post_123"}
        mock_fb_service.return_value = mock_service

        # Ejecutar tarea
        result = publish_scheduled_post.apply(args=[test_post_with_platforms.id])

        # Verificar resultado
        assert result.result["success_count"] == 1
        assert result.result["failure_count"] == 0

        # Verificar estado del post
        db_session.refresh(test_post_with_platforms)
        assert test_post_with_platforms.status == PostStatus.PUBLISHED

    @patch('app.tasks.celery_tasks.FacebookService')
    def test_publish_facebook_failure(self, mock_fb_service, db_session, test_post_with_platforms):
        """Test fallo al publicar en Facebook"""
        # Mock que genera error
        mock_service = Mock()
        mock_service.get_user_pages.side_effect = Exception("API Error")
        mock_fb_service.return_value = mock_service

        # Ejecutar tarea
        result = publish_scheduled_post.apply(args=[test_post_with_platforms.id])

        # Verificar resultado
        assert result.result["success_count"] == 0
        assert result.result["failure_count"] == 1

        # Verificar estado del post
        db_session.refresh(test_post_with_platforms)
        assert test_post_with_platforms.status == PostStatus.FAILED


class TestCheckScheduledPosts:
    """Tests para verificar posts programados"""

    def test_no_scheduled_posts(self, db_session):
        """Test sin posts programados"""
        result = check_scheduled_posts.apply()

        assert result.result["found"] == 0
        assert len(result.result["tasks_launched"]) == 0

    def test_find_scheduled_posts(self, db_session, test_user):
        """Test encuentra posts programados"""
        # Crear posts programados que ya deberían publicarse
        past_time = datetime.utcnow() - timedelta(minutes=5)

        for i in range(3):
            post = Post(
                user_id=test_user.id,
                content=f"Scheduled post {i}",
                status=PostStatus.SCHEDULED,
                scheduled_at=past_time
            )
            db_session.add(post)

        db_session.commit()

        # Ejecutar tarea
        with patch('app.tasks.celery_tasks.publish_scheduled_post.delay') as mock_publish:
            mock_publish.return_value = Mock(id="task_123")

            result = check_scheduled_posts.apply()

            # Verificar que encontró los 3 posts
            assert result.result["found"] == 3
            assert len(result.result["tasks_launched"]) == 3

    def test_ignore_future_scheduled_posts(self, db_session, test_user):
        """Test ignora posts programados para el futuro"""
        # Post programado para el futuro
        future_time = datetime.utcnow() + timedelta(hours=2)

        post = Post(
            user_id=test_user.id,
            content="Future post",
            status=PostStatus.SCHEDULED,
            scheduled_at=future_time
        )
        db_session.add(post)
        db_session.commit()

        # Ejecutar tarea
        result = check_scheduled_posts.apply()

        # No debe encontrar posts
        assert result.result["found"] == 0

    def test_ignore_non_scheduled_posts(self, db_session, test_user):
        """Test ignora posts con otros estados"""
        # Posts con diferentes estados
        statuses = [PostStatus.DRAFT, PostStatus.PUBLISHED, PostStatus.FAILED]

        for status in statuses:
            post = Post(
                user_id=test_user.id,
                content=f"Post {status}",
                status=status
            )
            db_session.add(post)

        db_session.commit()

        # Ejecutar tarea
        result = check_scheduled_posts.apply()

        # No debe encontrar posts
        assert result.result["found"] == 0
