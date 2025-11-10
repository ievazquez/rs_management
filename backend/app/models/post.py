"""
Modelos de Publicación
Almacena publicaciones y su estado en cada plataforma
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import enum


class PostStatus(str, enum.Enum):
    """Estados de una publicación"""
    DRAFT = "draft"  # Borrador
    SCHEDULED = "scheduled"  # Programada
    PUBLISHING = "publishing"  # En proceso de publicación
    PUBLISHED = "published"  # Publicada exitosamente
    FAILED = "failed"  # Falló la publicación
    PARTIAL = "partial"  # Publicada en algunas plataformas, falló en otras


class Post(Base):
    """Modelo de publicación"""

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)  # Texto de la publicación
    image_url = Column(String)  # URL de la imagen (si aplica)
    status = Column(Enum(PostStatus), default=PostStatus.DRAFT)
    scheduled_at = Column(DateTime(timezone=True))  # Fecha programada
    published_at = Column(DateTime(timezone=True))  # Fecha de publicación real
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    user = relationship("User", back_populates="posts")
    platforms = relationship("PostPlatform", back_populates="post", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Post(id={self.id}, status={self.status}, user_id={self.user_id})>"


class PlatformPostStatus(str, enum.Enum):
    """Estado de publicación en una plataforma específica"""
    PENDING = "pending"  # Pendiente
    PUBLISHING = "publishing"  # Publicando
    PUBLISHED = "published"  # Publicado
    FAILED = "failed"  # Falló


class PostPlatform(Base):
    """Modelo de relación entre publicación y plataforma"""

    __tablename__ = "post_platforms"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    social_account_id = Column(Integer, ForeignKey("social_accounts.id"), nullable=False)
    status = Column(Enum(PlatformPostStatus), default=PlatformPostStatus.PENDING)
    platform_post_id = Column(String)  # ID de la publicación en la plataforma
    error_message = Column(Text)  # Mensaje de error si falló
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    post = relationship("Post", back_populates="platforms")
    social_account = relationship("SocialAccount", back_populates="post_platforms")

    def __repr__(self):
        return f"<PostPlatform(id={self.id}, post_id={self.post_id}, status={self.status})>"
