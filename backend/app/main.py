"""
Aplicación principal FastAPI
Punto de entrada del backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .database import init_db
from .routes import auth_router, social_router, posts_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación
    Inicializa la base de datos al inicio
    """
    # Inicializar base de datos
    init_db()
    yield
    # Cleanup (si es necesario)


# Crear aplicación FastAPI
app = FastAPI(
    title="Social Media Manager API",
    description="API REST para gestión centralizada de redes sociales",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(auth_router)
app.include_router(social_router)
app.include_router(posts_router)


@app.get("/")
async def root():
    """Endpoint raíz de la API"""
    return {
        "message": "Social Media Manager API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Endpoint de health check"""
    return {
        "status": "healthy",
        "database": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
