"""
Servicio de integración con Twitter/X
Maneja OAuth 2.0 y publicaciones usando Twitter API v2
"""
import requests
from typing import Dict, Optional
from requests_oauthlib import OAuth1Session
from ..config import settings


class TwitterService:
    """Servicio para integración con Twitter API v2"""

    BASE_URL = "https://api.twitter.com/2"
    AUTH_URL = "https://twitter.com/i/oauth2/authorize"
    TOKEN_URL = "https://api.twitter.com/2/oauth2/token"

    def __init__(self):
        self.client_id = settings.TWITTER_CLIENT_ID
        self.client_secret = settings.TWITTER_CLIENT_SECRET
        self.redirect_uri = settings.TWITTER_REDIRECT_URI
        self.api_key = settings.TWITTER_API_KEY
        self.api_secret = settings.TWITTER_API_SECRET

    def get_authorization_url(self, state: str = "", code_challenge: str = "") -> str:
        """
        Genera URL de autorización OAuth 2.0 para Twitter

        Args:
            state: Parámetro de estado para CSRF protection
            code_challenge: PKCE code challenge

        Returns:
            URL de autorización
        """
        scopes = ["tweet.read", "tweet.write", "users.read", "offline.access"]

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])

        return f"{self.AUTH_URL}?{query_string}"

    def exchange_code_for_token(
        self,
        code: str,
        code_verifier: str
    ) -> Dict:
        """
        Intercambia código de autorización por token de acceso

        Args:
            code: Código de autorización de OAuth
            code_verifier: PKCE code verifier

        Returns:
            Diccionario con access_token, refresh_token y expires_in
        """
        data = {
            "code": code,
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code_verifier": code_verifier
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = requests.post(
            self.TOKEN_URL,
            data=data,
            headers=headers,
            auth=(self.client_id, self.client_secret)
        )
        response.raise_for_status()

        return response.json()

    def refresh_access_token(self, refresh_token: str) -> Dict:
        """
        Refresca el token de acceso usando el refresh token

        Args:
            refresh_token: Refresh token

        Returns:
            Nuevo access_token y refresh_token
        """
        data = {
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "client_id": self.client_id
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        response = requests.post(
            self.TOKEN_URL,
            data=data,
            headers=headers,
            auth=(self.client_id, self.client_secret)
        )
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
        url = f"{self.BASE_URL}/users/me"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        params = {
            "user.fields": "id,name,username"
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        return response.json()

    def publish_tweet(
        self,
        access_token: str,
        text: str,
        media_ids: Optional[list] = None
    ) -> Dict:
        """
        Publica un tweet

        Args:
            access_token: Token de acceso
            text: Contenido del tweet (máximo 280 caracteres)
            media_ids: IDs de medios subidos previamente (opcional)

        Returns:
            Respuesta de la API con el ID del tweet

        Raises:
            Exception: Si la publicación falla
        """
        url = f"{self.BASE_URL}/tweets"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        data = {"text": text}

        if media_ids:
            data["media"] = {"media_ids": media_ids}

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        return response.json()

    def upload_media(self, access_token: str, image_url: str) -> str:
        """
        Sube una imagen a Twitter y obtiene su media_id

        Nota: Twitter API v2 requiere usar v1.1 para subir medios
        Esta es una implementación simplificada

        Args:
            access_token: Token de acceso
            image_url: URL de la imagen

        Returns:
            Media ID
        """
        # Descargar imagen
        image_response = requests.get(image_url)
        image_response.raise_for_status()

        # Subir a Twitter (usando API v1.1)
        upload_url = "https://upload.twitter.com/1.1/media/upload.json"

        # Crear sesión OAuth 1.0a para upload
        oauth = OAuth1Session(
            self.api_key,
            client_secret=self.api_secret,
            resource_owner_key=access_token,
            resource_owner_secret=""  # No disponible en OAuth 2.0
        )

        files = {"media": image_response.content}
        response = oauth.post(upload_url, files=files)
        response.raise_for_status()

        return response.json()["media_id_string"]

    def delete_tweet(self, tweet_id: str, access_token: str) -> bool:
        """
        Elimina un tweet

        Args:
            tweet_id: ID del tweet
            access_token: Token de acceso

        Returns:
            True si se eliminó exitosamente
        """
        url = f"{self.BASE_URL}/tweets/{tweet_id}"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.delete(url, headers=headers)
        response.raise_for_status()

        return response.json().get("data", {}).get("deleted", False)
