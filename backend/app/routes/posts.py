"""
Rutas para gestión de publicaciones
Endpoints para crear, editar, eliminar y publicar contenido
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ..database import get_db
from ..models.user import User
from ..models.post import Post, PostStatus, PostPlatform, PlatformPostStatus
from ..models.social_account import SocialAccount, SocialPlatform
from ..schemas.post import PostCreate, PostUpdate, PostResponse
from ..utils.auth import get_current_active_user

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.get("/", response_model=List[PostResponse])
async def get_user_posts(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene las publicaciones del usuario

    Args:
        skip: Número de registros a saltar
        limit: Número máximo de registros a retornar
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Lista de publicaciones
    """
    posts = db.query(Post).filter(
        Post.user_id == current_user.id
    ).order_by(Post.created_at.desc()).offset(skip).limit(limit).all()

    return posts


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene una publicación específica

    Args:
        post_id: ID de la publicación
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Publicación
    """
    post = db.query(Post).filter(
        Post.id == post_id,
        Post.user_id == current_user.id
    ).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada"
        )

    return post


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Crea una nueva publicación

    Args:
        post_data: Datos de la publicación
        background_tasks: Tareas en segundo plano
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Publicación creada
    """
    # Verificar que las cuentas sociales pertenezcan al usuario
    social_accounts = db.query(SocialAccount).filter(
        SocialAccount.id.in_(post_data.platform_account_ids),
        SocialAccount.user_id == current_user.id,
        SocialAccount.is_active == True
    ).all()

    if len(social_accounts) != len(post_data.platform_account_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Una o más cuentas sociales no son válidas"
        )

    # Determinar estado inicial
    if post_data.scheduled_at:
        if post_data.scheduled_at <= datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La fecha de programación debe ser futura"
            )
        post_status = PostStatus.SCHEDULED
    else:
        post_status = PostStatus.DRAFT

    # Crear publicación
    new_post = Post(
        user_id=current_user.id,
        content=post_data.content,
        image_url=post_data.image_url,
        status=post_status,
        scheduled_at=post_data.scheduled_at
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    # Crear relaciones con plataformas
    for account in social_accounts:
        post_platform = PostPlatform(
            post_id=new_post.id,
            social_account_id=account.id,
            status=PlatformPostStatus.PENDING
        )
        db.add(post_platform)

    db.commit()
    db.refresh(new_post)

    # Si no está programada, publicar inmediatamente
    if post_status == PostStatus.DRAFT and not post_data.scheduled_at:
        # Esto normalmente se haría con Celery, pero por ahora lo hacemos directamente
        background_tasks.add_task(publish_post_task, new_post.id, db)

    return new_post


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    post_data: PostUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza una publicación existente

    Args:
        post_id: ID de la publicación
        post_data: Datos actualizados
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Publicación actualizada
    """
    post = db.query(Post).filter(
        Post.id == post_id,
        Post.user_id == current_user.id
    ).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada"
        )

    if post.status == PostStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede editar una publicación ya publicada"
        )

    # Actualizar campos
    if post_data.content is not None:
        post.content = post_data.content
    if post_data.image_url is not None:
        post.image_url = post_data.image_url
    if post_data.scheduled_at is not None:
        post.scheduled_at = post_data.scheduled_at
        post.status = PostStatus.SCHEDULED

    # Actualizar plataformas si se proporcionaron
    if post_data.platform_account_ids is not None:
        # Verificar que las cuentas sociales pertenezcan al usuario
        social_accounts = db.query(SocialAccount).filter(
            SocialAccount.id.in_(post_data.platform_account_ids),
            SocialAccount.user_id == current_user.id,
            SocialAccount.is_active == True
        ).all()

        if len(social_accounts) != len(post_data.platform_account_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Una o más cuentas sociales no son válidas"
            )

        # Eliminar plataformas antiguas
        db.query(PostPlatform).filter(PostPlatform.post_id == post_id).delete()

        # Crear nuevas relaciones
        for account in social_accounts:
            post_platform = PostPlatform(
                post_id=post.id,
                social_account_id=account.id,
                status=PlatformPostStatus.PENDING
            )
            db.add(post_platform)

    db.commit()
    db.refresh(post)

    return post


@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Elimina una publicación

    Args:
        post_id: ID de la publicación
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Mensaje de éxito
    """
    post = db.query(Post).filter(
        Post.id == post_id,
        Post.user_id == current_user.id
    ).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada"
        )

    db.delete(post)
    db.commit()

    return {"message": "Publicación eliminada exitosamente"}


@router.post("/{post_id}/publish", response_model=PostResponse)
async def publish_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Publica inmediatamente una publicación

    Args:
        post_id: ID de la publicación
        background_tasks: Tareas en segundo plano
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Publicación actualizada
    """
    post = db.query(Post).filter(
        Post.id == post_id,
        Post.user_id == current_user.id
    ).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicación no encontrada"
        )

    if post.status == PostStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La publicación ya fue publicada"
        )

    # Cambiar estado a publicando
    post.status = PostStatus.PUBLISHING
    db.commit()

    # Publicar en segundo plano
    background_tasks.add_task(publish_post_task, post_id, db)

    return post


def publish_post_task(post_id: int, db: Session):
    """
    Tarea para publicar en las plataformas sociales
    Esta función normalmente se ejecutaría con Celery

    Args:
        post_id: ID de la publicación
        db: Sesión de base de datos
    """
    from ..services import FacebookService, InstagramService, TwitterService

    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        return

    success_count = 0
    failure_count = 0

    # Publicar en cada plataforma
    for post_platform in post.platforms:
        try:
            account = post_platform.social_account
            post_platform.status = PlatformPostStatus.PUBLISHING
            db.commit()

            # Publicar según la plataforma
            if account.platform == SocialPlatform.FACEBOOK:
                service = FacebookService()
                # Obtener páginas y publicar en la primera
                pages = service.get_user_pages(account.access_token)
                if pages.get("data"):
                    result = service.publish_post(
                        pages["data"][0]["access_token"],
                        pages["data"][0]["id"],
                        post.content,
                        post.image_url
                    )
                    post_platform.platform_post_id = result.get("id")

            elif account.platform == SocialPlatform.INSTAGRAM:
                service = InstagramService()
                # Obtener cuenta de Instagram Business
                pages = service.get_user_pages(account.access_token)
                if pages.get("data"):
                    ig_account = service.get_instagram_business_account(
                        pages["data"][0]["id"],
                        account.access_token
                    )
                    ig_user_id = ig_account.get("instagram_business_account", {}).get("id")
                    if ig_user_id and post.image_url:
                        result = service.publish_post(
                            account.access_token,
                            ig_user_id,
                            post.content,
                            post.image_url
                        )
                        post_platform.platform_post_id = result.get("id")

            elif account.platform == SocialPlatform.TWITTER:
                service = TwitterService()
                # Truncar contenido a 280 caracteres
                content = post.content[:280]
                result = service.publish_tweet(account.access_token, content)
                post_platform.platform_post_id = result.get("data", {}).get("id")

            post_platform.status = PlatformPostStatus.PUBLISHED
            post_platform.published_at = datetime.utcnow()
            success_count += 1

        except Exception as e:
            post_platform.status = PlatformPostStatus.FAILED
            post_platform.error_message = str(e)
            failure_count += 1

        db.commit()

    # Actualizar estado general del post
    if success_count > 0 and failure_count == 0:
        post.status = PostStatus.PUBLISHED
    elif success_count > 0 and failure_count > 0:
        post.status = PostStatus.PARTIAL
    else:
        post.status = PostStatus.FAILED

    post.published_at = datetime.utcnow()
    db.commit()
