"""
Schemas para operaciones de publicaciones
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from ..models.post import PostStatus, PlatformPostStatus


class PostCreate(BaseModel):
    """Schema para crear una publicación"""
    content: str = Field(..., min_length=1, max_length=5000)
    image_url: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    platform_account_ids: List[int] = Field(..., min_items=1)  # IDs de cuentas sociales


class PostUpdate(BaseModel):
    """Schema para actualizar una publicación"""
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    image_url: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    platform_account_ids: Optional[List[int]] = None


class PostPlatformResponse(BaseModel):
    """Schema para respuesta de plataforma de publicación"""
    id: int
    social_account_id: int
    status: PlatformPostStatus
    platform_post_id: Optional[str] = None
    error_message: Optional[str] = None
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PostResponse(BaseModel):
    """Schema para respuesta de publicación"""
    id: int
    user_id: int
    content: str
    image_url: Optional[str] = None
    status: PostStatus
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    platforms: List[PostPlatformResponse] = []

    class Config:
        from_attributes = True
