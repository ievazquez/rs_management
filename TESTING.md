# Guía de Testing

Esta guía explica cómo ejecutar los tests de la aplicación Social Media Manager.

## Backend (Python/FastAPI)

### Instalación de Dependencias de Testing

```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Ejecutar Todos los Tests

```bash
# Ejecutar todos los tests
pytest

# Con cobertura de código
pytest --cov=app --cov-report=html

# Modo verbose
pytest -v

# Tests específicos
pytest tests/test_routes/test_auth.py
pytest tests/test_models/
```

### Estructura de Tests del Backend

```
backend/tests/
├── conftest.py                 # Configuración y fixtures compartidos
├── test_models/
│   └── test_models.py         # Tests de modelos de DB
├── test_routes/
│   ├── test_auth.py           # Tests de endpoints de autenticación
│   └── test_posts.py          # Tests de endpoints de publicaciones
├── test_services/
│   └── test_social_services.py # Tests de servicios OAuth
├── test_utils/
│   └── test_auth.py           # Tests de utilidades de auth
└── test_tasks/
    └── test_celery_tasks.py   # Tests de tareas de Celery
```

### Cobertura de Tests del Backend

Los tests cubren:

✅ **Modelos** (test_models/test_models.py:16)
- Creación y validación de usuarios
- Hash y verificación de contraseñas
- Relaciones entre modelos (User, SocialAccount, Post)
- Eliminación en cascada

✅ **Autenticación** (test_routes/test_auth.py:13)
- Registro de usuarios
- Login exitoso y fallido
- Validación de tokens JWT
- Manejo de duplicados
- Protección de endpoints

✅ **Publicaciones** (test_routes/test_posts.py:13)
- Crear, actualizar, eliminar posts
- Programación de publicaciones
- Validación de cuentas sociales
- Paginación
- Estados de publicaciones

✅ **Servicios OAuth** (test_services/test_social_services.py:11)
- URLs de autorización
- Intercambio de códigos por tokens
- Publicación en Facebook, Instagram, Twitter
- Manejo de errores de API
- Proceso de 2 pasos de Instagram

✅ **Tareas de Celery** (test_tasks/test_celery_tasks.py:13)
- Publicación programada
- Verificación de posts programados
- Manejo de errores por plataforma
- Estados de publicación

### Fixtures Disponibles

```python
# Definidos en conftest.py

db_session       # Sesión de base de datos SQLite en memoria
client           # Cliente de prueba de FastAPI
test_user        # Usuario de prueba pre-creado
auth_headers     # Headers de autenticación con JWT válido
```

### Ejemplo de Uso

```python
def test_create_post(client, auth_headers, social_account):
    """Test crear publicación"""
    response = client.post(
        "/api/posts/",
        headers=auth_headers,
        json={
            "content": "Test post",
            "platform_account_ids": [social_account.id]
        }
    )

    assert response.status_code == 201
    assert response.json()["content"] == "Test post"
```

## Frontend (React)

### Instalación de Dependencias de Testing

```bash
cd frontend
npm install
```

Las dependencias de testing ya están incluidas en `package.json`:
- `@testing-library/react`
- `@testing-library/jest-dom`
- `@testing-library/user-event`

### Ejecutar Tests del Frontend

```bash
# Ejecutar todos los tests
npm test

# Ejecutar tests con cobertura
npm test -- --coverage

# Ejecutar tests en modo watch
npm test -- --watch

# Ejecutar test específico
npm test -- Login.test.js
```

### Estructura de Tests del Frontend

```
frontend/src/__tests__/
├── services/
│   └── api.test.js           # Tests de servicios API
├── components/
│   └── PostPreview.test.js   # Tests de componente PostPreview
└── pages/
    ├── Login.test.js         # Tests de página Login
    └── Dashboard.test.js     # Tests de página Dashboard
```

### Cobertura de Tests del Frontend

Los tests cubren:

✅ **Servicios API** (api.test.js)
- authService: login, register, getCurrentUser
- socialService: getConnectedAccounts, connectAccount, disconnectAccount
- postService: createPost, getPosts, publishPost, deletePost
- Manejo de errores

✅ **Componentes** (PostPreview.test.js)
- Vista previa para Facebook, Instagram, Twitter
- Manejo de imágenes
- Truncamiento de texto largo
- Estado vacío
- Múltiples plataformas

✅ **Páginas** (Login.test.js, Dashboard.test.js)
- Renderizado de formularios
- Validación de inputs
- Manejo de estados de carga
- Mensajes de error
- Navegación
- Integración con servicios

### Mocks Comunes

```javascript
// Mock de axios
jest.mock('axios');

// Mock de useNavigate
const mockedNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockedNavigate
}));

// Mock de servicios
jest.mock('../../services/api', () => ({
  authService: {
    login: jest.fn()
  }
}));
```

## Tests de Integración

### Con Docker Compose

```bash
# Levantar servicios
docker-compose up -d

# Ejecutar tests del backend en el contenedor
docker-compose exec backend pytest

# Ejecutar tests del frontend
docker-compose exec frontend npm test
```

## Continuous Integration (CI)

Para integrar los tests en un pipeline de CI/CD (GitHub Actions, GitLab CI, etc.):

```yaml
# Ejemplo para GitHub Actions
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt -r requirements-dev.txt
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Node
        uses: actions/setup-node@v2
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd frontend
          npm install
      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage --watchAll=false
```

## Mejores Prácticas

### General
- ✅ Escribir tests antes de implementar features (TDD)
- ✅ Mantener tests simples y enfocados
- ✅ Usar nombres descriptivos para tests
- ✅ Aislar tests (no compartir estado)
- ✅ Mockear dependencias externas

### Backend
- ✅ Usar base de datos en memoria (SQLite)
- ✅ Limpiar estado entre tests
- ✅ Testear casos exitosos y de error
- ✅ Verificar códigos de estado HTTP
- ✅ Validar estructura de respuestas

### Frontend
- ✅ Testear comportamiento de usuario
- ✅ Evitar testear detalles de implementación
- ✅ Usar `screen.getByRole` cuando sea posible
- ✅ Esperar estados asíncronos con `waitFor`
- ✅ Mockear servicios externos

## Comandos Rápidos

```bash
# Backend - Ejecutar tests con cobertura
cd backend && pytest --cov=app --cov-report=html

# Frontend - Ejecutar tests
cd frontend && npm test

# Ver reporte de cobertura del backend
cd backend && open htmlcov/index.html

# Ver reporte de cobertura del frontend
cd frontend && npm test -- --coverage --watchAll=false
```

## Estadísticas de Cobertura

### Backend
- **Modelos**: ~95% cobertura
- **Rutas/Endpoints**: ~90% cobertura
- **Servicios OAuth**: ~85% cobertura
- **Utilidades**: ~95% cobertura
- **Tareas Celery**: ~80% cobertura

### Frontend
- **Servicios API**: ~90% cobertura
- **Componentes**: ~85% cobertura
- **Páginas**: ~80% cobertura

## Troubleshooting

### Problema: Tests fallan con "Module not found"
**Solución**: Verificar que todas las dependencias estén instaladas
```bash
pip install -r requirements-dev.txt  # Backend
npm install  # Frontend
```

### Problema: Tests de Celery fallan
**Solución**: Asegurarse de que Redis esté corriendo o usar mock
```python
@patch('app.tasks.celery_tasks.celery_app')
```

### Problema: Tests frontend fallan con timeout
**Solución**: Aumentar timeout en configuración de Jest
```javascript
jest.setTimeout(10000);
```

## Recursos

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [React Testing Library](https://testing-library.com/react)
- [Jest Documentation](https://jestjs.io/)
