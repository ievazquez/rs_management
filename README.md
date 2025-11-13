# Social Media Manager

Plataforma centralizada de gestión de redes sociales que permite publicar contenido simultáneamente en Facebook, Instagram y Twitter/X desde una única interfaz.

## Características

- **Autenticación de usuarios** con JWT
- **Conexión OAuth 2.0** con Facebook, Instagram y Twitter/X
- **Publicación multi-plataforma** simultánea o selectiva
- **Programación de publicaciones** con sistema de colas (Celery)
- **Vista previa** del contenido según cada plataforma
- **Gestión de tokens** con renovación automática
- **Dashboard** intuitivo para monitoreo
- **Manejo de errores** por plataforma (publicación parcial)

## Arquitectura

### Backend (Python + FastAPI)
- **FastAPI** - Framework web moderno y rápido
- **SQLAlchemy** - ORM para base de datos
- **PostgreSQL** - Base de datos relacional
- **Celery** - Sistema de tareas asíncronas y programadas
- **Redis** - Broker de mensajes para Celery
- **OAuth 2.0** - Autenticación con redes sociales

### Frontend (React)
- **React 18** - Framework de interfaz de usuario
- **React Router** - Navegación entre páginas
- **Context API** - Gestión de estado global
- **Axios** - Cliente HTTP para API
- **CSS Modules** - Estilos componetizados

## Estructura del Proyecto

```
rs_management/
├── backend/
│   ├── app/
│   │   ├── models/          # Modelos de base de datos
│   │   ├── routes/          # Endpoints de la API
│   │   ├── services/        # Servicios de redes sociales
│   │   ├── schemas/         # Schemas de validación (Pydantic)
│   │   ├── tasks/           # Tareas de Celery
│   │   ├── utils/           # Utilidades (auth, helpers)
│   │   ├── config.py        # Configuración
│   │   ├── database.py      # Conexión a base de datos
│   │   └── main.py          # Punto de entrada
│   ├── tests/               # Unit tests (pytest)
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/      # Componentes React
│   │   ├── pages/           # Páginas
│   │   ├── services/        # Servicios API
│   │   ├── context/         # Context providers
│   │   ├── styles/          # Estilos CSS
│   │   ├── __tests__/       # Unit tests (Jest)
│   │   ├── App.js
│   │   └── index.js
│   ├── public/
│   ├── package.json
│   └── Dockerfile
├── docs/                    # Documentación técnica
│   └── architecture-overview.md
├── docker-compose.yml
├── README.md
├── DIAGRAMS.md             # Diagramas técnicos (Mermaid)
├── API_SPECS.md            # Especificaciones de APIs
└── TESTING.md              # Guía de testing
```

## Documentación Técnica

- **[DIAGRAMS.md](DIAGRAMS.md)** - Diagramas de arquitectura, flujos y secuencias (Mermaid)
- **[API_SPECS.md](API_SPECS.md)** - Especificaciones detalladas de APIs de Facebook, Instagram y Twitter
- **[TESTING.md](TESTING.md)** - Guía completa de testing y cobertura
- **[docs/architecture-overview.md](docs/architecture-overview.md)** - Resumen ejecutivo de arquitectura

## Requisitos Previos

- Docker y Docker Compose (recomendado)
- O bien:
  - Python 3.11+
  - Node.js 18+
  - PostgreSQL 15+
  - Redis 7+

## Instalación

### Opción 1: Docker (Recomendado)

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd rs_management
```

2. **Configurar variables de entorno**
```bash
cp .env.example .env
```

Edita el archivo `.env` con tus credenciales de redes sociales:
```env
SECRET_KEY=tu-clave-secreta-super-segura

# Facebook
FACEBOOK_APP_ID=tu-facebook-app-id
FACEBOOK_APP_SECRET=tu-facebook-app-secret

# Instagram (usa credenciales de Facebook)
INSTAGRAM_APP_ID=tu-instagram-app-id
INSTAGRAM_APP_SECRET=tu-instagram-app-secret

# Twitter/X
TWITTER_CLIENT_ID=tu-twitter-client-id
TWITTER_CLIENT_SECRET=tu-twitter-client-secret
TWITTER_API_KEY=tu-twitter-api-key
TWITTER_API_SECRET=tu-twitter-api-secret
```

3. **Levantar servicios con Docker Compose**
```bash
docker-compose up -d
```

4. **Acceder a la aplicación**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Flower (Celery Monitor): http://localhost:5555

### Opción 2: Instalación Manual

#### Backend

1. **Crear entorno virtual**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar base de datos**
```bash
# Crear base de datos PostgreSQL
createdb social_media_manager
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. **Iniciar servidor**
```bash
uvicorn app.main:app --reload
```

6. **Iniciar Celery Worker (en otra terminal)**
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

7. **Iniciar Celery Beat (en otra terminal)**
```bash
celery -A app.tasks.celery_app beat --loglevel=info
```

#### Frontend

1. **Instalar dependencias**
```bash
cd frontend
npm install
```

2. **Configurar variables de entorno**
```bash
cp .env.example .env
```

3. **Iniciar servidor de desarrollo**
```bash
npm start
```

## Configuración de APIs de Redes Sociales

### Facebook

1. Ve a [Facebook Developers](https://developers.facebook.com/)
2. Crea una nueva aplicación
3. Configura productos: Facebook Login
4. Agrega dominios válidos de OAuth redirect URIs:
   - `http://localhost:3000/callback/facebook` (desarrollo)
   - Tu dominio de producción
5. Obtén App ID y App Secret
6. Agrega permisos: `pages_show_list`, `pages_manage_posts`, `pages_read_engagement`

### Instagram

Instagram usa la API de Facebook Graph. Necesitas:

1. Crear aplicación en Facebook Developers (mismo proceso)
2. Configurar Instagram Graph API
3. Tener una cuenta de Instagram Business vinculada a una página de Facebook
4. Permisos necesarios: `instagram_basic`, `instagram_content_publish`

### Twitter/X

1. Ve a [Twitter Developer Portal](https://developer.twitter.com/)
2. Crea un nuevo proyecto y aplicación
3. Habilita OAuth 2.0
4. Configura Callback URL: `http://localhost:3000/callback/twitter`
5. Obtén:
   - Client ID
   - Client Secret
   - API Key
   - API Secret
   - Bearer Token
6. Permisos: Read and Write

## Uso

### Registro e Inicio de Sesión

1. Accede a http://localhost:3000
2. Crea una cuenta nueva o inicia sesión
3. Serás redirigido al dashboard

### Conectar Cuentas Sociales

1. Ve a "Cuentas Sociales" en el menú
2. Haz clic en "Conectar" para la plataforma deseada
3. Autoriza la aplicación en la ventana emergente
4. La cuenta quedará conectada y lista para usar

### Crear Publicación

1. Ve a "Nueva Publicación"
2. Escribe tu contenido (máx. 280 caracteres para Twitter)
3. Agrega URL de imagen (requerida para Instagram)
4. Selecciona las plataformas donde publicar
5. Opcionalmente programa una fecha/hora futura
6. Haz clic en:
   - "Publicar Ahora" - Publica inmediatamente
   - "Programar Publicación" - Si seleccionaste fecha/hora
   - "Guardar Borrador" - Guarda sin publicar

### Ver Publicaciones

1. Ve a "Publicaciones"
2. Verás el estado de cada publicación:
   - **Borrador**: No publicada
   - **Programada**: Se publicará en fecha programada
   - **Publicando**: En proceso
   - **Publicada**: Exitosa en todas las plataformas
   - **Parcial**: Exitosa en algunas plataformas
   - **Fallida**: Error en todas las plataformas

## API Endpoints

### Autenticación
- `POST /api/auth/register` - Registrar usuario
- `POST /api/auth/login` - Iniciar sesión
- `GET /api/auth/me` - Obtener usuario actual

### Cuentas Sociales
- `GET /api/social/accounts` - Listar cuentas conectadas
- `GET /api/social/auth-url/{platform}` - Obtener URL OAuth
- `POST /api/social/connect` - Conectar cuenta
- `DELETE /api/social/disconnect/{account_id}` - Desconectar cuenta
- `GET /api/social/platforms` - Listar plataformas disponibles

### Publicaciones
- `GET /api/posts/` - Listar publicaciones
- `GET /api/posts/{post_id}` - Obtener publicación
- `POST /api/posts/` - Crear publicación
- `PUT /api/posts/{post_id}` - Actualizar publicación
- `DELETE /api/posts/{post_id}` - Eliminar publicación
- `POST /api/posts/{post_id}/publish` - Publicar inmediatamente

## Rate Limits

La aplicación respeta los límites de cada plataforma:

- **Facebook**: ~200 llamadas/hora/usuario
- **Instagram**: Límites variables por endpoint
- **Twitter**:
  - 300 tweets/3 horas
  - 50 requests/15 minutos (lectura)

## Seguridad

- Contraseñas hasheadas con bcrypt
- Autenticación JWT con expiración
- Tokens OAuth almacenados encriptados en base de datos
- CORS configurado correctamente
- Variables de entorno para datos sensibles
- Validación de datos con Pydantic

## Manejo de Errores

La aplicación maneja casos donde:
- Una publicación falla en una plataforma pero tiene éxito en otras (estado: PARTIAL)
- Los tokens expiran (renovación automática cuando es posible)
- Se exceden los rate limits (errores informativos)
- Faltan requisitos (ej. imagen para Instagram)

## Tecnologías Utilizadas

### Backend
- FastAPI 0.104+
- SQLAlchemy 2.0+
- PostgreSQL 15+
- Celery 5.3+
- Redis 5.0+
- Pydantic 2.5+
- Python-Jose (JWT)
- Requests (HTTP)

### Frontend
- React 18
- React Router 6
- Axios
- date-fns

### DevOps
- Docker
- Docker Compose

## Troubleshooting

### Error de conexión a la base de datos
```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps

# Ver logs
docker-compose logs db
```

### Celery no procesa tareas
```bash
# Verificar Redis
docker-compose logs redis

# Verificar worker
docker-compose logs celery_worker
```

### OAuth no funciona
1. Verifica que las URLs de callback coincidan
2. Confirma que los permisos estén correctos
3. Revisa que las credenciales en `.env` sean correctas

## Desarrollo

### Ejecutar Tests

#### Backend (Python + pytest)
```bash
cd backend

# Instalar dependencias de testing
pip install -r requirements-dev.txt

# Ejecutar todos los tests
pytest

# Con cobertura de código
pytest --cov=app --cov-report=html

# Tests específicos
pytest tests/test_routes/test_auth.py
pytest tests/test_models/
```

**Cobertura de Tests del Backend:**
- ✅ Modelos de base de datos (User, SocialAccount, Post)
- ✅ Endpoints de autenticación (registro, login, JWT)
- ✅ Endpoints de publicaciones (CRUD, programación)
- ✅ Servicios OAuth (Facebook, Instagram, Twitter)
- ✅ Tareas de Celery (publicación programada)
- ✅ Utilidades de autenticación (hashing, tokens)

#### Frontend (React + Jest)
```bash
cd frontend

# Ejecutar todos los tests
npm test

# Con cobertura
npm test -- --coverage

# Tests específicos
npm test -- Login.test.js
```

**Cobertura de Tests del Frontend:**
- ✅ Servicios API (auth, social, posts)
- ✅ Componentes (PostPreview, Layout)
- ✅ Páginas (Login, Dashboard)
- ✅ Context (AuthContext)

Ver [TESTING.md](TESTING.md) para guía completa de testing.

### Ver documentación API
Visita http://localhost:8000/docs para ver la documentación interactiva de Swagger

### Monitorear tareas Celery
Visita http://localhost:5555 para ver Flower (monitor de Celery)

## Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## Soporte

Para reportar bugs o solicitar features, abre un issue en GitHub.

## Roadmap

- [ ] Soporte para más redes sociales (LinkedIn, TikTok)
- [ ] Análisis de métricas y estadísticas
- [ ] Editor de imágenes integrado
- [ ] Plantillas de publicaciones
- [ ] Calendario visual de publicaciones
- [ ] Notificaciones en tiempo real
- [ ] API pública para integraciones

---

Desarrollado con ❤️ usando FastAPI y React
