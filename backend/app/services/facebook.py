"""
Servicio de integración con Facebook
Maneja OAuth y publicaciones en Facebook usando Graph API
"""
import requests
from typing import Dict, Optional
from datetime import datetime, timedelta
from ..config import settings


class FacebookService:
    """Servicio para integración con Facebook Graph API"""

    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self):
        self.app_id = settings.FACEBOOK_APP_ID
        self.app_secret = settings.FACEBOOK_APP_SECRET
        self.redirect_uri = settings.FACEBOOK_REDIRECT_URI

    def get_authorization_url(self, state: str = "") -> str:
        """
        Genera URL de autorización OAuth para Facebook

        Args:
            state: Parámetro de estado para CSRF protection

        Returns:
            URL de autorización
        """
        scopes = [
            "public_profile",
            "email",
            "pages_show_list",
            "pages_read_engagement",
            "pages_manage_posts",
            "pages_read_user_content"
        ]

        params = {
            "client_id": self.app_id,
            "redirect_uri": self.redirect_uri,
            "scope": ",".join(scopes),
            "response_type": "code",
            "state": state
        }

        url = "https://www.facebook.com/v18.0/dialog/oauth"
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])

        return f"{url}?{query_string}"

    def exchange_code_for_token(self, code: str) -> Dict:
        """
        Intercambia código de autorización por token de acceso

        Args:
            code: Código de autorización de OAuth

        Returns:
            Diccionario con access_token y expires_in

        Raises:
            Exception: Si la solicitud falla
        """
        url = f"{self.BASE_URL}/oauth/access_token"
        params = {
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "redirect_uri": self.redirect_uri,
            "code": code
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()

        # Obtener token de larga duración
        long_lived_token = self.get_long_lived_token(data["access_token"])

        return long_lived_token

    def get_long_lived_token(self, short_lived_token: str) -> Dict:
        """
        Convierte un token de corta duración a uno de larga duración (60 días)

        Args:
            short_lived_token: Token de acceso de corta duración

        Returns:
            Diccionario con access_token y expires_in
        """
        url = f"{self.BASE_URL}/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "fb_exchange_token": short_lived_token
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        return response.json()

    def get_user_info(self, access_token: str) -> Dict:
        """
        Obtiene información del usuario

        Args:
            access_token: Token de acceso

        Returns:
            Información del usuario
        """
        url = f"{self.BASE_URL}/me"
        params = {
            "fields": "id,name,email",
            "access_token": access_token
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        return response.json()

    def get_user_pages(self, access_token: str) -> Dict:
        """
        Obtiene las páginas de Facebook del usuario

        Args:
            access_token: Token de acceso del usuario

        Returns:
            Lista de páginas
        """
        url = f"{self.BASE_URL}/me/accounts"
        params = {
            "access_token": access_token
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        return response.json()

    def publish_post(
        self,
        access_token: str,
        page_id: str,
        message: str,
        image_url: Optional[str] = None
    ) -> Dict:
        """
        Publica un post en una página de Facebook

        Args:
            access_token: Token de acceso de la página
            page_id: ID de la página
            message: Contenido del post
            image_url: URL de imagen (opcional)

        Returns:
            Respuesta de la API con el ID del post

        Raises:
            Exception: Si la publicación falla
        """
        url = f"{self.BASE_URL}/{page_id}/feed"
        data = {
            "message": message,
            "access_token": access_token
        }

        if image_url:
            # Para imágenes, usar el endpoint de photos
            url = f"{self.BASE_URL}/{page_id}/photos"
            data["url"] = image_url
            data["caption"] = message

        response = requests.post(url, data=data)
        response.raise_for_status()

        return response.json()

    def delete_post(self, post_id: str, access_token: str) -> bool:
        """
        Elimina un post de Facebook

        Args:
            post_id: ID del post
            access_token: Token de acceso

        Returns:
            True si se eliminó exitosamente
        """
        url = f"{self.BASE_URL}/{post_id}"
        params = {"access_token": access_token}

        response = requests.delete(url, params=params)
        response.raise_for_status()

        return response.json().get("success", False)
