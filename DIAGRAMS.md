# Diagramas Técnicos - Social Media Manager

Esta documentación contiene los diagramas técnicos de la arquitectura y flujos del sistema.

## Tabla de Contenidos

1. [Arquitectura General del Sistema](#1-arquitectura-general-del-sistema)
2. [Diagrama de Base de Datos (ERD)](#2-diagrama-de-base-de-datos-erd)
3. [Flujo de Autenticación de Usuario](#3-flujo-de-autenticación-de-usuario)
4. [Flujo OAuth 2.0 para Redes Sociales](#4-flujo-oauth-20-para-redes-sociales)
5. [Flujo de Creación y Publicación](#5-flujo-de-creación-y-publicación)
6. [Arquitectura de Componentes Frontend](#6-arquitectura-de-componentes-frontend)
7. [Diagrama de Secuencia - Publicación Multi-Plataforma](#7-diagrama-de-secuencia---publicación-multi-plataforma)
8. [Diagrama de Estados de Publicación](#8-diagrama-de-estados-de-publicación)
9. [Infraestructura Docker](#9-infraestructura-docker)
10. [Flujo de Tareas de Celery](#10-flujo-de-tareas-de-celery)

---

## 1. Arquitectura General del Sistema

```mermaid
graph TB
    subgraph "Cliente"
        Browser[Navegador Web]
    end

    subgraph "Frontend - React"
        ReactApp[React App<br/>Port 3000]
        AuthContext[Auth Context]
        Components[Components]
        Services[API Services]
    end

    subgraph "Backend - FastAPI"
        API[FastAPI Server<br/>Port 8000]
        AuthRoutes[Auth Routes]
        SocialRoutes[Social Routes]
        PostRoutes[Post Routes]

        AuthUtils[Auth Utils<br/>JWT, Bcrypt]

        subgraph "Services"
            FBService[Facebook Service]
            IGService[Instagram Service]
            TWService[Twitter Service]
        end
    end

    subgraph "Async Tasks"
        CeleryWorker[Celery Worker]
        CeleryBeat[Celery Beat<br/>Scheduler]
        Flower[Flower Monitor<br/>Port 5555]
    end

    subgraph "Data Layer"
        PostgreSQL[(PostgreSQL<br/>Port 5432)]
        Redis[(Redis<br/>Port 6379)]
    end

    subgraph "External APIs"
        FacebookAPI[Facebook<br/>Graph API]
        InstagramAPI[Instagram<br/>Graph API]
        TwitterAPI[Twitter<br/>API v2]
    end

    Browser --> ReactApp
    ReactApp --> AuthContext
    ReactApp --> Components
    Components --> Services
    Services --> API

    API --> AuthRoutes
    API --> SocialRoutes
    API --> PostRoutes

    AuthRoutes --> AuthUtils
    AuthRoutes --> PostgreSQL

    SocialRoutes --> FBService
    SocialRoutes --> IGService
    SocialRoutes --> TWService
    SocialRoutes --> PostgreSQL

    PostRoutes --> PostgreSQL
    PostRoutes --> CeleryWorker

    FBService --> FacebookAPI
    IGService --> InstagramAPI
    TWService --> TwitterAPI

    CeleryWorker --> Redis
    CeleryBeat --> Redis
    CeleryWorker --> PostgreSQL
    CeleryBeat --> CeleryWorker

    Flower --> Redis

    style ReactApp fill:#61dafb
    style API fill:#009688
    style PostgreSQL fill:#336791
    style Redis fill:#dc382d
    style CeleryWorker fill:#37814a
    style FacebookAPI fill:#1877f2
    style InstagramAPI fill:#e4405f
    style TwitterAPI fill:#1da1f2
```

---

## 2. Diagrama de Base de Datos (ERD)

```mermaid
erDiagram
    USER ||--o{ SOCIAL_ACCOUNT : owns
    USER ||--o{ POST : creates
    SOCIAL_ACCOUNT ||--o{ POST_PLATFORM : uses
    POST ||--o{ POST_PLATFORM : targets

    USER {
        int id PK
        string email UK
        string username UK
        string hashed_password
        string full_name
        boolean is_active
        boolean is_verified
        datetime created_at
        datetime updated_at
    }

    SOCIAL_ACCOUNT {
        int id PK
        int user_id FK
        enum platform
        string platform_user_id
        string platform_username
        text access_token
        text refresh_token
        datetime token_expires_at
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    POST {
        int id PK
        int user_id FK
        text content
        string image_url
        enum status
        datetime scheduled_at
        datetime published_at
        datetime created_at
        datetime updated_at
    }

    POST_PLATFORM {
        int id PK
        int post_id FK
        int social_account_id FK
        enum status
        string platform_post_id
        text error_message
        datetime published_at
        datetime created_at
        datetime updated_at
    }
```

**Relaciones:**
- Un `USER` puede tener múltiples `SOCIAL_ACCOUNT`
- Un `USER` puede crear múltiples `POST`
- Un `POST` puede publicarse en múltiples `POST_PLATFORM`
- Un `SOCIAL_ACCOUNT` puede usarse en múltiples `POST_PLATFORM`

**Enums:**
- `platform`: facebook, instagram, twitter
- `post.status`: draft, scheduled, publishing, published, failed, partial
- `post_platform.status`: pending, publishing, published, failed

---

## 3. Flujo de Autenticación de Usuario

```mermaid
sequenceDiagram
    participant U as Usuario
    participant F as Frontend
    participant API as FastAPI
    participant DB as PostgreSQL
    participant Auth as Auth Utils

    Note over U,Auth: Registro de Usuario

    U->>F: Completa formulario de registro
    F->>API: POST /api/auth/register
    API->>DB: Verificar email único
    DB-->>API: Email disponible
    API->>Auth: Hash contraseña (bcrypt)
    Auth-->>API: Password hasheado
    API->>DB: Crear usuario
    DB-->>API: Usuario creado
    API->>Auth: Crear token JWT
    Auth-->>API: access_token
    API-->>F: {access_token, user}
    F->>F: Guardar token en localStorage
    F-->>U: Redirigir a Dashboard

    Note over U,Auth: Login de Usuario

    U->>F: Ingresa credenciales
    F->>API: POST /api/auth/login
    API->>DB: Buscar usuario por email
    DB-->>API: Usuario encontrado
    API->>Auth: Verificar password
    Auth-->>API: Password válido
    API->>Auth: Crear token JWT
    Auth-->>API: access_token
    API-->>F: {access_token, user}
    F->>F: Guardar token en localStorage
    F-->>U: Redirigir a Dashboard

    Note over U,Auth: Solicitud Autenticada

    U->>F: Acción protegida
    F->>API: Request + Authorization: Bearer token
    API->>Auth: Verificar JWT
    Auth-->>API: Token válido, user_id
    API->>DB: Obtener usuario
    DB-->>API: Datos del usuario
    API-->>F: Respuesta autorizada
    F-->>U: Mostrar datos
```

---

## 4. Flujo OAuth 2.0 para Redes Sociales

```mermaid
sequenceDiagram
    participant U as Usuario
    participant F as Frontend
    participant API as Backend
    participant OAuth as Plataforma Social
    participant DB as PostgreSQL

    U->>F: Clic en "Conectar Facebook"
    F->>API: GET /api/social/auth-url/facebook
    API-->>F: {authorization_url, state}
    F->>OAuth: Redirigir a authorization_url

    Note over U,OAuth: Usuario autoriza en Facebook

    OAuth->>U: Solicitar permisos
    U->>OAuth: Aprobar permisos
    OAuth->>F: Redirigir con ?code=xxx&state=yyy

    F->>API: POST /api/social/connect<br/>{platform, code, redirect_uri}
    API->>OAuth: POST /oauth/token<br/>Intercambiar código
    OAuth-->>API: {access_token, refresh_token, expires_in}

    API->>OAuth: GET /me<br/>Obtener info de usuario
    OAuth-->>API: {id, name, email}

    API->>DB: Guardar SocialAccount
    DB-->>API: Cuenta guardada

    API-->>F: {id, platform, username, is_active}
    F-->>U: "Facebook conectado exitosamente"

    Note over API,DB: Renovación Automática de Token

    API->>DB: Verificar token_expires_at
    DB-->>API: Token por expirar
    API->>OAuth: POST /oauth/token<br/>{grant_type: refresh_token}
    OAuth-->>API: Nuevo access_token
    API->>DB: Actualizar token
```

---

## 5. Flujo de Creación y Publicación

```mermaid
flowchart TD
    Start([Usuario inicia]) --> CreateForm[Completar formulario<br/>de publicación]

    CreateForm --> SelectPlatforms{Seleccionar<br/>plataformas}
    SelectPlatforms --> AddContent[Agregar contenido<br/>y imagen opcional]

    AddContent --> ScheduleCheck{¿Programar<br/>publicación?}

    ScheduleCheck -->|Sí| SetDateTime[Establecer<br/>fecha/hora]
    ScheduleCheck -->|No| PublishNow[Publicar ahora]

    SetDateTime --> CreateDraft[POST /api/posts/<br/>status: scheduled]
    PublishNow --> CreateDraft2[POST /api/posts/<br/>status: draft]

    CreateDraft --> SaveDB[(Guardar en DB)]
    CreateDraft2 --> SaveDB

    SaveDB --> CreatePlatforms[Crear registros<br/>PostPlatform]

    CreatePlatforms --> CheckSchedule{¿Es programada?}

    CheckSchedule -->|Sí| CeleryBeat[Celery Beat<br/>verifica cada minuto]
    CheckSchedule -->|No| PublishTask[Lanzar tarea<br/>de publicación]

    CeleryBeat --> TimeCheck{¿Hora de<br/>publicar?}
    TimeCheck -->|No| Wait[Esperar]
    Wait --> CeleryBeat
    TimeCheck -->|Sí| PublishTask

    PublishTask --> UpdateStatus1[Actualizar status:<br/>PUBLISHING]

    UpdateStatus1 --> ForEachPlatform[Por cada plataforma<br/>seleccionada]

    ForEachPlatform --> Platform{Tipo de<br/>plataforma}

    Platform -->|Facebook| FBPublish[Facebook Service<br/>publish_post]
    Platform -->|Instagram| IGPublish[Instagram Service<br/>2-step publish]
    Platform -->|Twitter| TWPublish[Twitter Service<br/>publish_tweet]

    FBPublish --> CheckFBResult{¿Exitoso?}
    IGPublish --> CheckIGResult{¿Exitoso?}
    TWPublish --> CheckTWResult{¿Exitoso?}

    CheckFBResult -->|Sí| MarkSuccess1[PostPlatform:<br/>PUBLISHED]
    CheckFBResult -->|No| MarkFail1[PostPlatform:<br/>FAILED + error]

    CheckIGResult -->|Sí| MarkSuccess2[PostPlatform:<br/>PUBLISHED]
    CheckIGResult -->|No| MarkFail2[PostPlatform:<br/>FAILED + error]

    CheckTWResult -->|Sí| MarkSuccess3[PostPlatform:<br/>PUBLISHED]
    CheckTWResult -->|No| MarkFail3[PostPlatform:<br/>FAILED + error]

    MarkSuccess1 --> CountResults[Contar resultados]
    MarkFail1 --> CountResults
    MarkSuccess2 --> CountResults
    MarkFail2 --> CountResults
    MarkSuccess3 --> CountResults
    MarkFail3 --> CountResults

    CountResults --> FinalStatus{Evaluar<br/>resultados}

    FinalStatus -->|Todas exitosas| StatusPublished[Post status:<br/>PUBLISHED]
    FinalStatus -->|Todas fallidas| StatusFailed[Post status:<br/>FAILED]
    FinalStatus -->|Mixto| StatusPartial[Post status:<br/>PARTIAL]

    StatusPublished --> NotifyUser[Notificar usuario]
    StatusFailed --> NotifyUser
    StatusPartial --> NotifyUser

    NotifyUser --> End([Fin])

    style CreateForm fill:#e1f5ff
    style PublishTask fill:#fff9c4
    style FBPublish fill:#e3f2fd
    style IGPublish fill:#fce4ec
    style TWPublish fill:#e1f5fe
    style StatusPublished fill:#c8e6c9
    style StatusFailed fill:#ffcdd2
    style StatusPartial fill:#ffe0b2
```

---

## 6. Arquitectura de Componentes Frontend

```mermaid
graph TD
    subgraph "App.js"
        Router[React Router]
        AuthProvider[Auth Provider<br/>Context]
    end

    subgraph "Rutas Públicas"
        Login[Login Page]
        Register[Register Page]
    end

    subgraph "Rutas Protegidas"
        Layout[Layout Component]
        Dashboard[Dashboard Page]
        SocialAccounts[Social Accounts Page]
        CreatePost[Create Post Page]
        Posts[Posts Page]
    end

    subgraph "Componentes Comunes"
        Navbar[Navbar]
        ProtectedRoute[Protected Route]
        PublicRoute[Public Route]
    end

    subgraph "Componentes Específicos"
        PostPreview[Post Preview]
        AccountCard[Account Card]
        PostCard[Post Card]
    end

    subgraph "Services"
        APIService[API Service]
        AuthService[Auth Service]
        SocialService[Social Service]
        PostService[Post Service]
    end

    subgraph "Context"
        AuthContext[Auth Context]
        UserState[User State]
        LoginFn[Login Function]
        LogoutFn[Logout Function]
    end

    Router --> AuthProvider
    AuthProvider --> ProtectedRoute
    AuthProvider --> PublicRoute

    PublicRoute --> Login
    PublicRoute --> Register

    ProtectedRoute --> Layout
    Layout --> Navbar
    Layout --> Dashboard
    Layout --> SocialAccounts
    Layout --> CreatePost
    Layout --> Posts

    Dashboard --> AccountCard
    Dashboard --> PostCard
    SocialAccounts --> AccountCard
    CreatePost --> PostPreview
    Posts --> PostCard

    Login --> AuthService
    Register --> AuthService
    Dashboard --> SocialService
    Dashboard --> PostService
    SocialAccounts --> SocialService
    CreatePost --> PostService
    Posts --> PostService

    AuthService --> APIService
    SocialService --> APIService
    PostService --> APIService

    AuthContext --> UserState
    AuthContext --> LoginFn
    AuthContext --> LogoutFn

    style AuthProvider fill:#61dafb
    style Layout fill:#4caf50
    style APIService fill:#ff9800
    style AuthContext fill:#9c27b0
```

---

## 7. Diagrama de Secuencia - Publicación Multi-Plataforma

```mermaid
sequenceDiagram
    participant U as Usuario
    participant F as Frontend
    participant API as FastAPI
    participant DB as PostgreSQL
    participant W as Celery Worker
    participant FB as Facebook API
    participant IG as Instagram API
    participant TW as Twitter API

    U->>F: Crear publicación
    F->>F: Validar formulario
    F->>API: POST /api/posts/<br/>{content, image, accounts}

    API->>DB: Verificar social_accounts
    DB-->>API: Cuentas válidas

    API->>DB: Crear Post (status: DRAFT)
    DB-->>API: Post creado (id: 1)

    API->>DB: Crear PostPlatform records
    DB-->>API: Records creados

    API->>W: Lanzar publish_task(post_id=1)
    API-->>F: {post_id: 1, status: "publishing"}
    F-->>U: "Publicando..."

    Note over W,TW: Worker procesa en background

    W->>DB: Actualizar Post.status = PUBLISHING
    W->>DB: Obtener Post + Platforms
    DB-->>W: Post data + 3 platforms

    par Publicación Paralela
        W->>FB: POST /page_id/feed<br/>{message, access_token}
        FB-->>W: {id: "fb_post_123"}
        W->>DB: PostPlatform[FB].status = PUBLISHED

    and
        W->>IG: 1. POST /media<br/>{image_url, caption}
        IG-->>W: {id: "container_456"}
        W->>IG: 2. POST /media_publish<br/>{creation_id}
        IG-->>W: {id: "ig_post_789"}
        W->>DB: PostPlatform[IG].status = PUBLISHED

    and
        W->>TW: POST /tweets<br/>{text: content[0:280]}
        TW-->>W: {data: {id: "tw_post_321"}}
        W->>DB: PostPlatform[TW].status = PUBLISHED
    end

    W->>W: Evaluar resultados<br/>(3 exitosas, 0 fallidas)

    W->>DB: Actualizar Post.status = PUBLISHED<br/>published_at = now()
    DB-->>W: Actualizado

    Note over F: Frontend hace polling o WebSocket

    F->>API: GET /api/posts/1
    API->>DB: Query Post
    DB-->>API: Post actualizado
    API-->>F: {status: "published", platforms: [...]}
    F-->>U: "¡Publicado exitosamente!"
```

---

## 8. Diagrama de Estados de Publicación

```mermaid
stateDiagram-v2
    [*] --> DRAFT: Usuario crea post

    DRAFT --> SCHEDULED: Usuario programa<br/>fecha futura
    DRAFT --> PUBLISHING: Usuario publica<br/>inmediatamente

    SCHEDULED --> PUBLISHING: Celery Beat detecta<br/>scheduled_at <= now()

    PUBLISHING --> PUBLISHED: Todas las plataformas<br/>exitosas
    PUBLISHING --> PARTIAL: Algunas plataformas<br/>exitosas
    PUBLISHING --> FAILED: Todas las plataformas<br/>fallaron

    DRAFT --> [*]: Usuario elimina
    SCHEDULED --> [*]: Usuario elimina

    note right of DRAFT
        Estado inicial
        Puede editarse
    end note

    note right of SCHEDULED
        En cola para publicar
        Puede editarse o cancelarse
    end note

    note right of PUBLISHING
        Publicación en proceso
        No se puede editar
    end note

    note right of PUBLISHED
        Publicación completada
        Inmutable
    end note

    note right of PARTIAL
        Exitoso en algunas
        plataformas, falló en otras
        Requiere revisión
    end note

    note right of FAILED
        Falló en todas
        las plataformas
        Revisar errores
    end note
```

**Estados de PostPlatform:**

```mermaid
stateDiagram-v2
    [*] --> PENDING: Post creado

    PENDING --> PUBLISHING: Worker inicia publicación

    PUBLISHING --> PUBLISHED: API responde exitosamente<br/>platform_post_id guardado

    PUBLISHING --> FAILED: API retorna error<br/>error_message guardado

    note right of PENDING
        Esperando publicación
    end note

    note right of PUBLISHING
        Request en progreso
    end note

    note right of PUBLISHED
        Publicado exitosamente
        platform_post_id almacenado
    end note

    note right of FAILED
        Error en publicación
        error_message para debug
    end note
```

---

## 9. Infraestructura Docker

```mermaid
graph TB
    subgraph "Docker Compose Network"
        subgraph "Frontend Container"
            ReactContainer[React Dev Server<br/>node:18-alpine<br/>Port 3000]
        end

        subgraph "Backend Container"
            FastAPIContainer[FastAPI + Uvicorn<br/>python:3.11-slim<br/>Port 8000]
        end

        subgraph "Worker Containers"
            CeleryWorkerContainer[Celery Worker<br/>python:3.11-slim]
            CeleryBeatContainer[Celery Beat<br/>python:3.11-slim]
            FlowerContainer[Flower Monitor<br/>python:3.11-slim<br/>Port 5555]
        end

        subgraph "Data Containers"
            PostgreSQLContainer[PostgreSQL 15<br/>postgres:15<br/>Port 5432]
            RedisContainer[Redis 7<br/>redis:7-alpine<br/>Port 6379]
        end

        subgraph "Volumes"
            PostgresData[(postgres_data)]
            BackendCode[./backend:/app]
            FrontendCode[./frontend:/app]
        end
    end

    ReactContainer -.->|Proxy| FastAPIContainer
    FastAPIContainer -->|SQLAlchemy| PostgreSQLContainer
    FastAPIContainer -->|Task Queue| RedisContainer

    CeleryWorkerContainer -->|Consume Tasks| RedisContainer
    CeleryBeatContainer -->|Schedule Tasks| RedisContainer
    FlowerContainer -->|Monitor| RedisContainer

    CeleryWorkerContainer -->|DB Access| PostgreSQLContainer
    CeleryBeatContainer -->|DB Access| PostgreSQLContainer

    PostgreSQLContainer -.->|Persist| PostgresData
    FastAPIContainer -.->|Mount| BackendCode
    ReactContainer -.->|Mount| FrontendCode

    style ReactContainer fill:#61dafb
    style FastAPIContainer fill:#009688
    style CeleryWorkerContainer fill:#37814a
    style CeleryBeatContainer fill:#37814a
    style FlowerContainer fill:#ff69b4
    style PostgreSQLContainer fill:#336791
    style RedisContainer fill:#dc382d
```

**Healthchecks:**
- PostgreSQL: `pg_isready -U social_user`
- Redis: `redis-cli ping`
- Servicios dependen de healthchecks para iniciar

---

## 10. Flujo de Tareas de Celery

```mermaid
flowchart TB
    Start([Inicio]) --> BeatSchedule[Celery Beat<br/>Ejecuta cada 60s]

    BeatSchedule --> CheckTask[check_scheduled_posts]

    CheckTask --> QueryDB[Query Posts WHERE<br/>status=SCHEDULED AND<br/>scheduled_at <= now]

    QueryDB --> HasPosts{¿Encontró<br/>posts?}

    HasPosts -->|No| Wait[Esperar 60s]
    Wait --> BeatSchedule

    HasPosts -->|Sí| ForEach[Por cada post<br/>encontrado]

    ForEach --> LaunchTask[Lanzar tarea:<br/>publish_scheduled_post.delay]

    LaunchTask --> RedisQueue[(Redis Queue)]

    RedisQueue --> WorkerPick[Celery Worker<br/>toma tarea]

    WorkerPick --> UpdateStatus[Actualizar Post<br/>status = PUBLISHING]

    UpdateStatus --> GetPlatforms[Obtener plataformas<br/>del post]

    GetPlatforms --> LoopPlatforms[Iterar plataformas]

    LoopPlatforms --> CheckPlatform{Tipo de<br/>plataforma?}

    CheckPlatform -->|Facebook| FacebookFlow[FacebookService<br/>1. get_user_pages<br/>2. publish_post]

    CheckPlatform -->|Instagram| InstagramFlow[InstagramService<br/>1. get_pages<br/>2. get_ig_account<br/>3. create_container<br/>4. publish_container]

    CheckPlatform -->|Twitter| TwitterFlow[TwitterService<br/>1. publish_tweet<br/>truncate a 280 chars]

    FacebookFlow --> TryCatch1{¿Exitoso?}
    InstagramFlow --> TryCatch2{¿Exitoso?}
    TwitterFlow --> TryCatch3{¿Exitoso?}

    TryCatch1 -->|Sí| SaveSuccess1[PostPlatform<br/>status=PUBLISHED<br/>platform_post_id]
    TryCatch1 -->|No| SaveError1[PostPlatform<br/>status=FAILED<br/>error_message]

    TryCatch2 -->|Sí| SaveSuccess2[PostPlatform<br/>status=PUBLISHED<br/>platform_post_id]
    TryCatch2 -->|No| SaveError2[PostPlatform<br/>status=FAILED<br/>error_message]

    TryCatch3 -->|Sí| SaveSuccess3[PostPlatform<br/>status=PUBLISHED<br/>platform_post_id]
    TryCatch3 -->|No| SaveError3[PostPlatform<br/>status=FAILED<br/>error_message]

    SaveSuccess1 --> CounterIncr[success_count++]
    SaveSuccess2 --> CounterIncr
    SaveSuccess3 --> CounterIncr

    SaveError1 --> CounterFail[failure_count++]
    SaveError2 --> CounterFail
    SaveError3 --> CounterFail

    CounterIncr --> AllDone{¿Todas<br/>procesadas?}
    CounterFail --> AllDone

    AllDone -->|No| LoopPlatforms

    AllDone -->|Sí| EvaluateResults{Evaluar<br/>resultados}

    EvaluateResults -->|success>0 AND failure=0| SetPublished[Post.status<br/>= PUBLISHED]
    EvaluateResults -->|success>0 AND failure>0| SetPartial[Post.status<br/>= PARTIAL]
    EvaluateResults -->|success=0 AND failure>0| SetFailed[Post.status<br/>= FAILED]

    SetPublished --> SetTimestamp[Post.published_at<br/>= now]
    SetPartial --> SetTimestamp
    SetFailed --> SetTimestamp

    SetTimestamp --> CommitDB[(Commit a DB)]

    CommitDB --> ReturnResult[Retornar resultado<br/>{post_id, status,<br/>success_count,<br/>failure_count}]

    ReturnResult --> End([Fin])

    style BeatSchedule fill:#fff9c4
    style WorkerPick fill:#c8e6c9
    style FacebookFlow fill:#e3f2fd
    style InstagramFlow fill:#fce4ec
    style TwitterFlow fill:#e1f5fe
    style SetPublished fill:#a5d6a7
    style SetPartial fill:#ffcc80
    style SetFailed fill:#ef9a9a
```

---

## Convenciones de Diagramas

### Colores

- **Azul claro** (#61dafb): Frontend/React
- **Verde** (#009688): Backend/FastAPI
- **Verde oscuro** (#37814a): Celery/Workers
- **Azul oscuro** (#336791): PostgreSQL
- **Rojo** (#dc382d): Redis
- **Azul Facebook** (#1877f2): Facebook API
- **Rosa Instagram** (#e4405f): Instagram API
- **Azul Twitter** (#1da1f2): Twitter API

### Símbolos

- `[]` Proceso/Componente
- `{}` Decisión
- `()` Inicio/Fin
- `[()]` Base de datos
- `-->` Flujo síncrono
- `-.->` Flujo asíncrono o dependencia

---

## Exportar Diagramas

### Como PNG (GitHub/GitLab)

Los diagramas Mermaid se renderizan automáticamente en:
- GitHub
- GitLab
- VS Code (con extensión)
- Confluence
- Notion

### Como SVG/PNG

Usar herramientas online:
- https://mermaid.live/
- https://mermaid.ink/

### En Documentación

Estos diagramas están en formato Mermaid y son compatibles con:
- MkDocs (plugin mermaid2)
- Docusaurus
- Sphinx (con extensión)
- Hugo

---

## Referencias

- [Mermaid Documentation](https://mermaid.js.org/)
- [Mermaid Live Editor](https://mermaid.live/)
- [GitHub Mermaid Support](https://github.blog/2022-02-14-include-diagrams-markdown-files-mermaid/)
