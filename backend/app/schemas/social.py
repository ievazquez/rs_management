"""
Schemas para operaciones de cuentas sociales
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..models.social_account import SocialPlatform


class SocialConnectionRequest(BaseModel):
    """Schema para solicitud de conexión OAuth"""
    platform: SocialPlatform
    code: str  # Código de autorización OAuth
    redirect_uri: str


class SocialAccountResponse(BaseModel):
    """Schema para respuesta de cuenta social"""
    id: int
    platform: SocialPlatform
    platform_user_id: str
    platform_username: Optional[str] = None
    is_active: bool
    created_at: datetime
    token_expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SocialDisconnectRequest(BaseModel):
    """Schema para desconectar cuenta social"""
    account_id: int
