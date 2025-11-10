"""
Tareas de Celery para publicaciones programadas
"""
from celery import Task
from datetime import datetime
from sqlalchemy.orm import Session

from .celery_app import celery_app
from ..database import SessionLocal
from ..models.post import Post, PostStatus, PostPlatform, PlatformPostStatus
from ..models.social_account import SocialPlatform
from ..services import FacebookService, InstagramService, TwitterService


class DatabaseTask(Task):
    """Tarea base que proporciona sesión de base de datos"""

    _db: Session = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True)
def publish_scheduled_post(self, post_id: int):
    """
    Publica una publicación programada en todas las plataformas seleccionadas

    Args:
        post_id: ID de la publicación

    Returns:
        Diccionario con resultado de la publicación
    """
    db = self.db
    post = db.query(Post).filter(Post.id == post_id).first()

    if not post:
        return {"error": "Publicación no encontrada"}

    # Cambiar estado a publicando
    post.status = PostStatus.PUBLISHING
    db.commit()

    success_count = 0
    failure_count = 0
    results = []

    # Publicar en cada plataforma
    for post_platform in post.platforms:
        try:
            account = post_platform.social_account
            post_platform.status = PlatformPostStatus.PUBLISHING
            db.commit()

            platform_result = {
                "platform": account.platform.value,
                "account_id": account.id,
                "success": False
            }

            # Publicar según la plataforma
            if account.platform == SocialPlatform.FACEBOOK:
                service = FacebookService()
                pages = service.get_user_pages(account.access_token)

                if pages.get("data"):
                    result = service.publish_post(
                        pages["data"][0]["access_token"],
                        pages["data"][0]["id"],
                        post.content,
                        post.image_url
                    )
                    post_platform.platform_post_id = result.get("id")
                    platform_result["post_id"] = result.get("id")
                    platform_result["success"] = True

            elif account.platform == SocialPlatform.INSTAGRAM:
                if not post.image_url:
                    raise ValueError("Instagram requiere una imagen")

                service = InstagramService()
                pages = service.get_user_pages(account.access_token)

                if pages.get("data"):
                    ig_account = service.get_instagram_business_account(
                        pages["data"][0]["id"],
                        account.access_token
                    )
                    ig_user_id = ig_account.get("instagram_business_account", {}).get("id")

                    if ig_user_id:
                        result = service.publish_post(
                            account.access_token,
                            ig_user_id,
                            post.content,
                            post.image_url
                        )
                        post_platform.platform_post_id = result.get("id")
                        platform_result["post_id"] = result.get("id")
                        platform_result["success"] = True

            elif account.platform == SocialPlatform.TWITTER:
                service = TwitterService()
                content = post.content[:280]  # Truncar a 280 caracteres
                result = service.publish_tweet(account.access_token, content)
                post_platform.platform_post_id = result.get("data", {}).get("id")
                platform_result["post_id"] = result.get("data", {}).get("id")
                platform_result["success"] = True

            post_platform.status = PlatformPostStatus.PUBLISHED
            post_platform.published_at = datetime.utcnow()
            success_count += 1
            results.append(platform_result)

        except Exception as e:
            post_platform.status = PlatformPostStatus.FAILED
            post_platform.error_message = str(e)
            failure_count += 1
            platform_result["success"] = False
            platform_result["error"] = str(e)
            results.append(platform_result)

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

    return {
        "post_id": post_id,
        "status": post.status.value,
        "success_count": success_count,
        "failure_count": failure_count,
        "results": results
    }


@celery_app.task(base=DatabaseTask, bind=True)
def check_scheduled_posts(self):
    """
    Verifica y publica las publicaciones programadas que ya deben ser publicadas

    Esta tarea se ejecuta periódicamente (cada minuto) para verificar
    si hay publicaciones programadas listas para publicar
    """
    db = self.db

    # Buscar publicaciones programadas cuya fecha ya pasó
    now = datetime.utcnow()
    scheduled_posts = db.query(Post).filter(
        Post.status == PostStatus.SCHEDULED,
        Post.scheduled_at <= now
    ).all()

    results = []

    for post in scheduled_posts:
        # Lanzar tarea de publicación
        task = publish_scheduled_post.delay(post.id)
        results.append({
            "post_id": post.id,
            "task_id": task.id
        })

    return {
        "checked_at": now.isoformat(),
        "found": len(scheduled_posts),
        "tasks_launched": results
    }
