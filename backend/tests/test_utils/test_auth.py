"""
Tests para utilidades de autenticación
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt
from app.utils.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user
)
from app.config import settings
from app.models.user import User


class TestPasswordHashing:
    """Tests para hashing de contraseñas"""

    def test_password_hash_different_from_plain(self):
        """Test hash es diferente del texto plano"""
        password = "mysecretpassword"
        hashed = get_password_hash(password)

        assert hashed != password
        assert len(hashed) > len(password)

    def test_same_password_different_hashes(self):
        """Test mismo password genera diferentes hashes (sal aleatoria)"""
        password = "samepassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2

    def test_verify_correct_password(self):
        """Test verificar contraseña correcta"""
        password = "correctpassword"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_incorrect_password(self):
        """Test verificar contraseña incorrecta"""
        password = "correctpassword"
        hashed = get_password_hash(password)

        assert verify_password("wrongpassword", hashed) is False


class TestJWTTokens:
    """Tests para tokens JWT"""

    def test_create_access_token(self):
        """Test crear token de acceso"""
        data = {"sub": "123"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_correct_data(self):
        """Test token contiene datos correctos"""
        user_id = "456"
        token = create_access_token({"sub": user_id})

        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        assert decoded["sub"] == user_id
        assert "exp" in decoded

    def test_token_expiration_default(self):
        """Test token tiene expiración por defecto"""
        token = create_access_token({"sub": "123"})

        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        exp = datetime.fromtimestamp(decoded["exp"])
        now = datetime.utcnow()

        # Debe expirar en aproximadamente 30 minutos
        time_diff = exp - now
        assert timedelta(minutes=25) < time_diff < timedelta(minutes=35)

    def test_token_custom_expiration(self):
        """Test token con expiración personalizada"""
        custom_delta = timedelta(hours=2)
        token = create_access_token({"sub": "123"}, expires_delta=custom_delta)

        decoded = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        exp = datetime.fromtimestamp(decoded["exp"])
        now = datetime.utcnow()

        time_diff = exp - now
        assert timedelta(hours=1, minutes=55) < time_diff < timedelta(hours=2, minutes=5)

    def test_invalid_token_raises_error(self):
        """Test token inválido genera error"""
        from jose import JWTError

        invalid_token = "invalid.token.here"

        with pytest.raises(JWTError):
            jwt.decode(
                invalid_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )

    def test_expired_token_raises_error(self):
        """Test token expirado genera error"""
        from jose import JWTError

        # Crear token que expira inmediatamente
        token = create_access_token(
            {"sub": "123"},
            expires_delta=timedelta(seconds=-1)
        )

        with pytest.raises(JWTError):
            jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )


class TestGetCurrentUser:
    """Tests para obtener usuario actual"""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self, db_session, test_user):
        """Test obtener usuario con token válido"""
        from fastapi import HTTPException

        token = create_access_token({"sub": str(test_user.id)})

        user = await get_current_user(token=token, db=db_session)

        assert user.id == test_user.id
        assert user.email == test_user.email

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, db_session):
        """Test con token inválido genera excepción"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="invalid_token", db=db_session)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_nonexistent_user(self, db_session):
        """Test con usuario que no existe"""
        from fastapi import HTTPException

        # Token válido pero usuario no existe
        token = create_access_token({"sub": "99999"})

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=db_session)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_no_sub_in_token(self, db_session):
        """Test token sin campo 'sub'"""
        from fastapi import HTTPException

        # Token sin el campo 'sub' requerido
        token_data = {"user": "123"}  # Debería ser 'sub', no 'user'
        token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token, db=db_session)

        assert exc_info.value.status_code == 401
