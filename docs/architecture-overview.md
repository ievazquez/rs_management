# Resumen Ejecutivo - Arquitectura

## Vista de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USUARIO FINAL                              │
│                     (Navegador Web)                                 │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │  Login/  │  │Dashboard │  │  Social  │  │  Create  │           │
│  │ Register │  │          │  │ Accounts │  │   Post   │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
│       │              │              │              │                │
│       └──────────────┴──────────────┴──────────────┘                │
│                      │ Axios HTTP                                   │
└──────────────────────┼──────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BACKEND API (FastAPI)                            │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐       │
│  │  Auth Routes   │  │ Social Routes  │  │  Post Routes   │       │
│  │  - Register    │  │ - Connect      │  │ - Create       │       │
│  │  - Login       │  │ - Disconnect   │  │ - Update       │       │
│  │  - JWT Auth    │  │ - List         │  │ - Publish      │       │
│  └────────────────┘  └────────────────┘  └────────────────┘       │
│           │                   │                    │                │
│           └───────────────────┴────────────────────┘                │
│                               │                                     │
│  ┌────────────────────────────┼───────────────────────────┐        │
│  │         Services            │                           │        │
│  │  ┌──────────────┐  ┌───────┴──────┐  ┌─────────────┐  │        │
│  │  │   Facebook   │  │  Instagram   │  │   Twitter   │  │        │
│  │  │   Service    │  │   Service    │  │   Service   │  │        │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │        │
│  └─────────┬─────────────────┬─────────────────┬──────────┘        │
└────────────┼─────────────────┼─────────────────┼───────────────────┘
             │                 │                 │
             ▼                 ▼                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                    EXTERNAL APIs                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Facebook   │  │  Instagram   │  │   Twitter    │          │
│  │  Graph API   │  │  Graph API   │  │   API v2     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└──────────────────────────────────────────────────────────────────┘

             │
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ASYNC WORKERS (Celery)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │    Worker    │  │  Beat        │  │   Flower     │             │
│  │  (Publish)   │  │ (Scheduler)  │  │  (Monitor)   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                    │
│  ┌──────────────────────┐        ┌──────────────────────┐          │
│  │    PostgreSQL        │        │       Redis          │          │
│  │  - Users             │        │  - Task Queue        │          │
│  │  - Social Accounts   │        │  - Results           │          │
│  │  - Posts             │        │  - Cache             │          │
│  │  - Post Platforms    │        │                      │          │
│  └──────────────────────┘        └──────────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

## Flujo de Datos Principal

### 1. Autenticación
```
Usuario → Frontend → Backend API → Hash Password → PostgreSQL → JWT Token → Usuario
```

### 2. Conexión OAuth
```
Usuario → Frontend → Backend → OAuth URL → Plataforma Social
                                                ↓
Usuario ← Frontend ← Backend ← Token ← Código ← Plataforma Social
                      ↓
                  PostgreSQL (guardar token)
```

### 3. Publicación Inmediata
```
Usuario → Frontend → Backend API → PostgreSQL (crear post)
                                         ↓
                                   Celery Worker → Facebook API
                                         ↓         Instagram API
                                         ↓         Twitter API
                                         ↓
                                   PostgreSQL (actualizar estado)
                                         ↓
                                   Usuario (notificar)
```

### 4. Publicación Programada
```
Usuario → Frontend → Backend API → PostgreSQL (scheduled post)
                                         ↓
                              Celery Beat (verificar cada minuto)
                                         ↓
                              ¿Es hora de publicar? → Sí → Celery Worker
                                         ↓                       ↓
                                      Esperar              Publicar en APIs
```

## Componentes Principales

### Frontend (React)
- **Tecnología**: React 18, React Router, Axios
- **Responsabilidad**: UI/UX, validación de formularios, gestión de estado local
- **Puerto**: 3000

### Backend (FastAPI)
- **Tecnología**: Python 3.11, FastAPI, SQLAlchemy
- **Responsabilidad**: API REST, autenticación, lógica de negocio
- **Puerto**: 8000

### Workers (Celery)
- **Tecnología**: Celery, Redis
- **Responsabilidad**: Tareas asíncronas, publicaciones programadas
- **Componentes**:
  - Worker: Ejecuta tareas
  - Beat: Programa tareas periódicas
  - Flower: Monitor web (puerto 5555)

### Base de Datos (PostgreSQL)
- **Tecnología**: PostgreSQL 15
- **Responsabilidad**: Persistencia de datos
- **Puerto**: 5432

### Cola de Mensajes (Redis)
- **Tecnología**: Redis 7
- **Responsabilidad**: Broker de mensajes para Celery
- **Puerto**: 6379

## Patrones de Diseño Utilizados

### 1. Repository Pattern
```
Controller → Service → Repository → Database
```

### 2. Factory Pattern
```python
def get_social_service(platform):
    services = {
        'facebook': FacebookService,
        'instagram': InstagramService,
        'twitter': TwitterService
    }
    return services[platform]()
```

### 3. Strategy Pattern
```python
class PublishStrategy:
    def publish(self, content, account):
        raise NotImplementedError

class FacebookStrategy(PublishStrategy):
    def publish(self, content, account):
        # Lógica específica de Facebook
        pass
```

### 4. Observer Pattern
```
Post Status Change → Notify User → Update UI
```

## Seguridad

### Capas de Seguridad

1. **Frontend**
   - HTTPS only
   - XSS prevention (React escape)
   - CSRF tokens
   - Input validation

2. **Backend**
   - JWT authentication
   - Password hashing (bcrypt)
   - SQL injection prevention (SQLAlchemy ORM)
   - Rate limiting
   - CORS configuration

3. **Database**
   - Encrypted tokens
   - User data encryption
   - Connection pooling
   - Prepared statements

4. **Infrastructure**
   - Docker isolation
   - Network segmentation
   - Environment variables
   - Secret management

## Escalabilidad

### Horizontal Scaling
```
┌─────────────┐
│ Load        │
│ Balancer    │
└──────┬──────┘
       │
   ┌───┴───┬───────┬───────┐
   ▼       ▼       ▼       ▼
┌────┐  ┌────┐  ┌────┐  ┌────┐
│API │  │API │  │API │  │API │
│ 1  │  │ 2  │  │ 3  │  │ 4  │
└────┘  └────┘  └────┘  └────┘
   │       │       │       │
   └───────┴───┬───┴───────┘
               ▼
         ┌──────────┐
         │PostgreSQL│
         │(Primary) │
         └────┬─────┘
              │
         ┌────┴─────┐
         ▼          ▼
    ┌────────┐ ┌────────┐
    │Replica │ │Replica │
    │   1    │ │   2    │
    └────────┘ └────────┘
```

### Caching Strategy
```
Request → Cache (Redis) → Hit? → Return
                  │
                  └─→ Miss → Database → Cache → Return
```

## Métricas y Monitoreo

### Métricas Clave
- Request rate (req/s)
- Response time (p50, p95, p99)
- Error rate (%)
- Task queue length
- Database connections
- Memory usage
- CPU usage

### Herramientas
- **Flower**: Monitor de Celery
- **PostgreSQL Logs**: Query performance
- **Application Logs**: Error tracking
- **Docker Stats**: Resource usage

## Deployment

### Development
```bash
docker-compose up -d
```

### Production (Ejemplo)
```
┌─────────────┐
│   Nginx     │ (Reverse Proxy)
└──────┬──────┘
       │
   ┌───┴───────────┐
   │               │
   ▼               ▼
┌────────┐    ┌─────────┐
│Frontend│    │ Backend │
│(Static)│    │  API    │
└────────┘    └─────────┘
```

## Consideraciones de Producción

### 1. Variables de Entorno
- Usar secretos reales (no .env.example)
- Rotar tokens regularmente
- SECRET_KEY fuerte y único

### 2. Base de Datos
- Backups automáticos diarios
- Replicación master-slave
- Connection pooling optimizado

### 3. Celery
- Múltiples workers
- Autoscaling basado en carga
- Dead letter queue para tareas fallidas

### 4. Monitoreo
- Health checks
- Alertas automáticas
- Log aggregation

### 5. Rate Limiting
- Por usuario
- Por IP
- Por endpoint

## Costos Estimados (Producción)

### Infraestructura
- **VPS/EC2**: $20-50/mes
- **PostgreSQL**: $15-30/mes (managed)
- **Redis**: $10-20/mes (managed)
- **Total**: ~$45-100/mes

### APIs (Free Tier)
- Facebook: Gratis
- Instagram: Gratis
- Twitter: $100/mes (Basic tier)

## Roadmap Técnico

### Fase 1 (Actual) ✅
- CRUD de publicaciones
- OAuth multi-plataforma
- Publicaciones programadas

### Fase 2 (Próximo)
- Analytics y métricas
- Calendario visual
- Notificaciones en tiempo real

### Fase 3 (Futuro)
- AI para sugerencias de contenido
- Editor de imágenes
- Plantillas reutilizables
- API pública

## Referencias

Ver documentación detallada en:
- [DIAGRAMS.md](../DIAGRAMS.md) - Diagramas técnicos completos
- [API_SPECS.md](../API_SPECS.md) - Especificaciones de APIs
- [TESTING.md](../TESTING.md) - Guía de testing
- [README.md](../README.md) - Documentación principal
