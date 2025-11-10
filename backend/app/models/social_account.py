"""
Modelo de Cuenta Social
Almacena tokens y configuración de cuentas de redes sociales conectadas
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import enum


class SocialPlatform(str, enum.Enum):
    """Plataformas de redes sociales soportadas"""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"


class SocialAccount(Base):
    """Modelo de cuenta de red social conectada"""

    __tablename__ = "social_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    platform = Column(Enum(SocialPlatform), nullable=False)
    platform_user_id = Column(String, nullable=False)  # ID del usuario en la plataforma
    platform_username = Column(String)  # Nombre de usuario en la plataforma
    access_token = Column(Text, nullable=False)  # Token de acceso OAuth
    refresh_token = Column(Text)  # Token de refresco (si aplica)
    token_expires_at = Column(DateTime(timezone=True))  # Expiración del token
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    user = relationship("User", back_populates="social_accounts")
    post_platforms = relationship("PostPlatform", back_populates="social_account")

    def __repr__(self):
        return f"<SocialAccount(id={self.id}, platform={self.platform}, username={self.platform_username})>"
