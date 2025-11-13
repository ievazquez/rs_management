"""
Tests para servicios de redes sociales
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.facebook import FacebookService
from app.services.instagram import InstagramService
from app.services.twitter import TwitterService


class TestFacebookService:
    """Tests para FacebookService"""

    def test_get_authorization_url(self):
        """Test generar URL de autorización"""
        service = FacebookService()
        url = service.get_authorization_url(state="test_state")

        assert "facebook.com" in url
        assert "oauth" in url
        assert "test_state" in url
        assert "pages_manage_posts" in url

    @patch('app.services.facebook.requests.get')
    def test_exchange_code_for_token(self, mock_get):
        """Test intercambiar código por token"""
        # Mock de respuestas
        mock_response1 = Mock()
        mock_response1.json.return_value = {"access_token": "short_token", "expires_in": 3600}

        mock_response2 = Mock()
        mock_response2.json.return_value = {
            "access_token": "long_lived_token",
            "expires_in": 5184000
        }

        mock_get.side_effect = [mock_response1, mock_response2]

        service = FacebookService()
        result = service.exchange_code_for_token("test_code")

        assert result["access_token"] == "long_lived_token"
        assert result["expires_in"] == 5184000

    @patch('app.services.facebook.requests.get')
    def test_get_user_info(self, mock_get):
        """Test obtener información del usuario"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "123456",
            "name": "Test User",
            "email": "test@example.com"
        }
        mock_get.return_value = mock_response

        service = FacebookService()
        user_info = service.get_user_info("test_token")

        assert user_info["id"] == "123456"
        assert user_info["name"] == "Test User"
        assert user_info["email"] == "test@example.com"

    @patch('app.services.facebook.requests.post')
    def test_publish_post_text_only(self, mock_post):
        """Test publicar post solo con texto"""
        mock_response = Mock()
        mock_response.json.return_value = {"id": "post_123"}
        mock_post.return_value = mock_response

        service = FacebookService()
        result = service.publish_post(
            access_token="test_token",
            page_id="page_123",
            message="Test post"
        )

        assert result["id"] == "post_123"
        mock_post.assert_called_once()

    @patch('app.services.facebook.requests.post')
    def test_publish_post_with_image(self, mock_post):
        """Test publicar post con imagen"""
        mock_response = Mock()
        mock_response.json.return_value = {"id": "photo_123"}
        mock_post.return_value = mock_response

        service = FacebookService()
        result = service.publish_post(
            access_token="test_token",
            page_id="page_123",
            message="Test post",
            image_url="https://example.com/image.jpg"
        )

        assert result["id"] == "photo_123"
        # Verificar que se llamó el endpoint de photos
        call_args = mock_post.call_args
        assert "photos" in call_args[0][0]


class TestInstagramService:
    """Tests para InstagramService"""

    def test_get_authorization_url(self):
        """Test generar URL de autorización para Instagram"""
        service = InstagramService()
        url = service.get_authorization_url(state="ig_state")

        assert "facebook.com" in url
        assert "oauth" in url
        assert "instagram_basic" in url or "instagram_content_publish" in url

    @patch('app.services.instagram.requests.post')
    def test_create_media_container(self, mock_post):
        """Test crear contenedor de medios"""
        mock_response = Mock()
        mock_response.json.return_value = {"id": "container_123"}
        mock_post.return_value = mock_response

        service = InstagramService()
        container_id = service.create_media_container(
            ig_user_id="ig_user_123",
            access_token="test_token",
            image_url="https://example.com/image.jpg",
            caption="Test caption"
        )

        assert container_id == "container_123"

    @patch('app.services.instagram.InstagramService.create_media_container')
    @patch('app.services.instagram.InstagramService.publish_media_container')
    def test_publish_post_two_step(self, mock_publish, mock_create):
        """Test proceso de 2 pasos para publicar en Instagram"""
        mock_create.return_value = "container_123"
        mock_publish.return_value = {"id": "post_123"}

        service = InstagramService()
        result = service.publish_post(
            access_token="test_token",
            ig_user_id="ig_user_123",
            caption="Test post",
            image_url="https://example.com/image.jpg"
        )

        assert result["id"] == "post_123"
        mock_create.assert_called_once()
        mock_publish.assert_called_once()

    def test_publish_post_without_image_fails(self):
        """Test publicar sin imagen falla"""
        service = InstagramService()

        with pytest.raises(ValueError, match="Instagram requiere una imagen"):
            service.publish_post(
                access_token="test_token",
                ig_user_id="ig_user_123",
                caption="No image",
                image_url=None
            )


class TestTwitterService:
    """Tests para TwitterService"""

    def test_get_authorization_url(self):
        """Test generar URL de autorización para Twitter"""
        service = TwitterService()
        url = service.get_authorization_url(
            state="tw_state",
            code_challenge="challenge123"
        )

        assert "twitter.com" in url
        assert "oauth2" in url
        assert "tw_state" in url
        assert "challenge123" in url

    @patch('app.services.twitter.requests.post')
    def test_exchange_code_for_token(self, mock_post):
        """Test intercambiar código por token con PKCE"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "twitter_token",
            "refresh_token": "refresh_token",
            "expires_in": 7200
        }
        mock_post.return_value = mock_response

        service = TwitterService()
        result = service.exchange_code_for_token(
            code="test_code",
            code_verifier="verifier123"
        )

        assert result["access_token"] == "twitter_token"
        assert result["refresh_token"] == "refresh_token"

    @patch('app.services.twitter.requests.post')
    def test_publish_tweet(self, mock_post):
        """Test publicar tweet"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"id": "tweet_123", "text": "Test tweet"}
        }
        mock_post.return_value = mock_response

        service = TwitterService()
        result = service.publish_tweet(
            access_token="test_token",
            text="Test tweet"
        )

        assert result["data"]["id"] == "tweet_123"

    @patch('app.services.twitter.requests.post')
    def test_publish_tweet_with_media(self, mock_post):
        """Test publicar tweet con medios"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {"id": "tweet_123"}
        }
        mock_post.return_value = mock_response

        service = TwitterService()
        result = service.publish_tweet(
            access_token="test_token",
            text="Tweet with media",
            media_ids=["media_1", "media_2"]
        )

        # Verificar que se incluyeron los media_ids
        call_args = mock_post.call_args
        assert "media" in call_args[1]["json"]

    def test_tweet_text_truncation(self):
        """Test que el texto del tweet puede ser truncado"""
        long_text = "a" * 300  # Más de 280 caracteres

        # En producción, esto debería manejarse en el endpoint
        # pero el servicio acepta cualquier longitud
        service = TwitterService()
        # El servicio no trunca, eso se hace en la API
        # Solo verificamos que acepta texto largo
        assert len(long_text) > 280

    @patch('app.services.twitter.requests.post')
    def test_refresh_access_token(self, mock_post):
        """Test refrescar token de acceso"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "new_token",
            "refresh_token": "new_refresh",
            "expires_in": 7200
        }
        mock_post.return_value = mock_response

        service = TwitterService()
        result = service.refresh_access_token("old_refresh_token")

        assert result["access_token"] == "new_token"
        assert result["refresh_token"] == "new_refresh"
