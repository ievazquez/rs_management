"""
Rutas para gestión de cuentas sociales
Endpoints para conectar, desconectar y gestionar cuentas de redes sociales
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from ..database import get_db
from ..models.user import User
from ..models.social_account import SocialAccount, SocialPlatform
from ..schemas.social import SocialAccountResponse, SocialConnectionRequest
from ..utils.auth import get_current_active_user
from ..services import FacebookService, InstagramService, TwitterService

router = APIRouter(prefix="/api/social", tags=["social"])


@router.get("/accounts", response_model=List[SocialAccountResponse])
async def get_connected_accounts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las cuentas sociales conectadas del usuario

    Args:
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Lista de cuentas sociales conectadas
    """
    accounts = db.query(SocialAccount).filter(
        SocialAccount.user_id == current_user.id,
        SocialAccount.is_active == True
    ).all()

    return accounts


@router.get("/auth-url/{platform}")
async def get_oauth_url(
    platform: SocialPlatform,
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene URL de autorización OAuth para una plataforma

    Args:
        platform: Plataforma social
        current_user: Usuario autenticado

    Returns:
        URL de autorización
    """
    state = f"{current_user.id}_{platform.value}"

    if platform == SocialPlatform.FACEBOOK:
        service = FacebookService()
        url = service.get_authorization_url(state)
    elif platform == SocialPlatform.INSTAGRAM:
        service = InstagramService()
        url = service.get_authorization_url(state)
    elif platform == SocialPlatform.TWITTER:
        service = TwitterService()
        # Para Twitter, necesitarías generar code_challenge (PKCE)
        # Esto es un ejemplo simplificado
        url = service.get_authorization_url(state, code_challenge="challenge")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plataforma no soportada"
        )

    return {"authorization_url": url, "state": state}


@router.post("/connect", response_model=SocialAccountResponse)
async def connect_social_account(
    connection: SocialConnectionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Conecta una cuenta de red social usando código OAuth

    Args:
        connection: Datos de conexión OAuth
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Cuenta social conectada

    Raises:
        HTTPException: Si falla la conexión
    """
    try:
        # Intercambiar código por token según la plataforma
        if connection.platform == SocialPlatform.FACEBOOK:
            service = FacebookService()
            token_data = service.exchange_code_for_token(connection.code)
            user_info = service.get_user_info(token_data["access_token"])

            platform_user_id = user_info["id"]
            platform_username = user_info.get("name")
            access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 5184000)  # 60 días por defecto

        elif connection.platform == SocialPlatform.INSTAGRAM:
            service = InstagramService()
            token_data = service.exchange_code_for_token(connection.code)

            # Obtener páginas de Facebook y luego cuenta de Instagram
            pages = service.get_user_pages(token_data["access_token"])

            if not pages.get("data"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se encontró cuenta de Instagram Business"
                )

            # Usar la primera página por simplicidad
            page = pages["data"][0]
            ig_account = service.get_instagram_business_account(
                page["id"],
                token_data["access_token"]
            )

            platform_user_id = ig_account.get("instagram_business_account", {}).get("id", page["id"])
            platform_username = page.get("name")
            access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 5184000)

        elif connection.platform == SocialPlatform.TWITTER:
            service = TwitterService()
            # Para Twitter, necesitas code_verifier (PKCE)
            token_data = service.exchange_code_for_token(connection.code, "verifier")
            user_info = service.get_user_info(token_data["access_token"])

            platform_user_id = user_info["data"]["id"]
            platform_username = user_info["data"]["username"]
            access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 7200)

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Plataforma no soportada"
            )

        # Verificar si ya existe una cuenta con este platform_user_id
        existing_account = db.query(SocialAccount).filter(
            SocialAccount.user_id == current_user.id,
            SocialAccount.platform == connection.platform,
            SocialAccount.platform_user_id == platform_user_id
        ).first()

        if existing_account:
            # Actualizar token de cuenta existente
            existing_account.access_token = access_token
            existing_account.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            existing_account.is_active = True
            db.commit()
            db.refresh(existing_account)
            return existing_account

        # Crear nueva cuenta social
        new_account = SocialAccount(
            user_id=current_user.id,
            platform=connection.platform,
            platform_user_id=platform_user_id,
            platform_username=platform_username,
            access_token=access_token,
            refresh_token=token_data.get("refresh_token"),
            token_expires_at=datetime.utcnow() + timedelta(seconds=expires_in)
        )

        db.add(new_account)
        db.commit()
        db.refresh(new_account)

        return new_account

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error al conectar cuenta: {str(e)}"
        )


@router.delete("/disconnect/{account_id}")
async def disconnect_social_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Desconecta una cuenta de red social

    Args:
        account_id: ID de la cuenta social
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Mensaje de éxito
    """
    account = db.query(SocialAccount).filter(
        SocialAccount.id == account_id,
        SocialAccount.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cuenta no encontrada"
        )

    # Marcar como inactiva en lugar de eliminar
    account.is_active = False
    db.commit()

    return {"message": "Cuenta desconectada exitosamente"}


@router.get("/platforms")
async def get_available_platforms():
    """
    Obtiene lista de plataformas soportadas

    Returns:
        Lista de plataformas disponibles
    """
    return {
        "platforms": [
            {
                "name": "Facebook",
                "value": SocialPlatform.FACEBOOK.value,
                "description": "Conecta tu cuenta de Facebook para publicar en tu perfil o páginas"
            },
            {
                "name": "Instagram",
                "value": SocialPlatform.INSTAGRAM.value,
                "description": "Conecta tu cuenta de Instagram Business para publicar fotos"
            },
            {
                "name": "Twitter/X",
                "value": SocialPlatform.TWITTER.value,
                "description": "Conecta tu cuenta de Twitter/X para publicar tweets"
            }
        ]
    }
