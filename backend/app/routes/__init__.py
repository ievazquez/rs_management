"""
Rutas de la API
"""
from .auth import router as auth_router
from .social import router as social_router
from .posts import router as posts_router

__all__ = ["auth_router", "social_router", "posts_router"]
