"""
Servicio de integración con Instagram
Maneja OAuth y publicaciones en Instagram usando Graph API
"""
import requests
from typing import Dict, Optional
from ..config import settings


class InstagramService:
    """Servicio para integración con Instagram Graph API"""

    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self):
        self.app_id = settings.INSTAGRAM_APP_ID
        self.app_secret = settings.INSTAGRAM_APP_SECRET
        self.redirect_uri = settings.INSTAGRAM_REDIRECT_URI

    def get_authorization_url(self, state: str = "") -> str:
        """
        Genera URL de autorización OAuth para Instagram
        Instagram usa Facebook OAuth con permisos específicos

        Args:
            state: Parámetro de estado para CSRF protection

        Returns:
            URL de autorización
        """
        scopes = [
            "instagram_basic",
            "instagram_content_publish",
            "pages_show_list",
            "pages_read_engagement"
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
        Convierte un token de corta duración a uno de larga duración

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

    def get_instagram_business_account(self, page_id: str, access_token: str) -> Dict:
        """
        Obtiene la cuenta de Instagram Business asociada a una página de Facebook

        Args:
            page_id: ID de la página de Facebook
            access_token: Token de acceso

        Returns:
            Información de la cuenta de Instagram
        """
        url = f"{self.BASE_URL}/{page_id}"
        params = {
            "fields": "instagram_business_account",
            "access_token": access_token
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        return response.json()

    def get_user_pages(self, access_token: str) -> Dict:
        """
        Obtiene las páginas de Facebook del usuario
        (necesarias para obtener cuentas de Instagram)

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

    def create_media_container(
        self,
        ig_user_id: str,
        access_token: str,
        image_url: str,
        caption: str
    ) -> str:
        """
        Crea un contenedor de medios para Instagram

        Args:
            ig_user_id: ID del usuario de Instagram Business
            access_token: Token de acceso
            image_url: URL de la imagen
            caption: Caption del post

        Returns:
            ID del contenedor de medios
        """
        url = f"{self.BASE_URL}/{ig_user_id}/media"
        data = {
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token
        }

        response = requests.post(url, data=data)
        response.raise_for_status()

        return response.json()["id"]

    def publish_media_container(
        self,
        ig_user_id: str,
        creation_id: str,
        access_token: str
    ) -> Dict:
        """
        Publica un contenedor de medios creado previamente

        Args:
            ig_user_id: ID del usuario de Instagram Business
            creation_id: ID del contenedor de medios
            access_token: Token de acceso

        Returns:
            Respuesta de la API con el ID del post
        """
        url = f"{self.BASE_URL}/{ig_user_id}/media_publish"
        data = {
            "creation_id": creation_id,
            "access_token": access_token
        }

        response = requests.post(url, data=data)
        response.raise_for_status()

        return response.json()

    def publish_post(
        self,
        access_token: str,
        ig_user_id: str,
        caption: str,
        image_url: str
    ) -> Dict:
        """
        Publica un post en Instagram (proceso de 2 pasos)

        Args:
            access_token: Token de acceso
            ig_user_id: ID del usuario de Instagram Business
            caption: Caption del post
            image_url: URL de la imagen (requerida para Instagram)

        Returns:
            Respuesta de la API con el ID del post

        Raises:
            Exception: Si la publicación falla
        """
        if not image_url:
            raise ValueError("Instagram requiere una imagen para publicar")

        # Paso 1: Crear contenedor de medios
        creation_id = self.create_media_container(
            ig_user_id, access_token, image_url, caption
        )

        # Paso 2: Publicar el contenedor
        return self.publish_media_container(ig_user_id, creation_id, access_token)

    def delete_post(self, post_id: str, access_token: str) -> bool:
        """
        Elimina un post de Instagram

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
