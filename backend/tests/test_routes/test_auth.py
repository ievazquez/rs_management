"""
Tests para endpoints de autenticación
"""
import pytest
from app.models.user import User


class TestAuthEndpoints:
    """Tests para endpoints de autenticación"""

    def test_register_user(self, client):
        """Test registro de nuevo usuario"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "securepass123",
                "full_name": "New User"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["username"] == "newuser"

    def test_register_duplicate_email(self, client, test_user):
        """Test registro con email duplicado"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": test_user.email,
                "username": "different",
                "password": "password123"
            }
        )

        assert response.status_code == 400
        assert "email ya está registrado" in response.json()["detail"].lower()

    def test_register_duplicate_username(self, client, test_user):
        """Test registro con username duplicado"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "different@example.com",
                "username": test_user.username,
                "password": "password123"
            }
        )

        assert response.status_code == 400
        assert "usuario" in response.json()["detail"].lower()

    def test_login_success(self, client, test_user):
        """Test login exitoso"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == test_user.email

    def test_login_wrong_password(self, client, test_user):
        """Test login con contraseña incorrecta"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "incorrectos" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login con usuario inexistente"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 401

    def test_get_current_user(self, client, auth_headers):
        """Test obtener usuario actual"""
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "username" in data
        assert "id" in data

    def test_get_current_user_unauthorized(self, client):
        """Test obtener usuario sin autenticación"""
        response = client.get("/api/auth/me")

        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """Test con token inválido"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    def test_register_short_password(self, client):
        """Test registro con contraseña corta"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "short"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_register_invalid_email(self, client):
        """Test registro con email inválido"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "username": "testuser",
                "password": "password123"
            }
        )

        assert response.status_code == 422
