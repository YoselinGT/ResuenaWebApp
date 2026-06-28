# CLAUDE.md — Resuena

> Este archivo es leído automáticamente por Claude Code al iniciar en este repositorio.
> Contiene todo el contexto necesario para trabajar en el proyecto sin preguntar.

---

## Qué es este proyecto

**Resuena** es una plataforma web para gestión de campañas musicales. Conecta artistas con profesionales de la industria (bloggers, playlisters, influencers, creadores de reels). Los artistas compran créditos y los gastan enviando campañas; los profesionales las reciben, evalúan y entregan contenido editorial.

Funcionalidad diferenciadora: editor anti-IA para bloggers que captura metadatos de escritura y calcula una puntuación de autenticidad.

---

## Estado del proyecto

**Fase activa:** Fase 02 — Modelo de datos + migraciones PostgreSQL
(Fase 01 — Bootstrap + Infraestructura: completada ✅)

Para ver el estado detallado: `docs/PLAN.md`
Para ver la fase activa: `docs/fase-02.md`

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend API | Python 3.12 + FastAPI + Gunicorn/Uvicorn |
| Frontend | Next.js 14 App Router + TypeScript + Tailwind |
| Base de datos | PostgreSQL 16 + SQLAlchemy 2 async + Alembic |
| Cache / sesiones | Redis 7 |
| Mensajería | RabbitMQ 3.12 |
| Almacenamiento | AWS S3 (prod) / LocalStack (dev) vía abstracción `StorageProvider` |
| Pagos | Stripe (modo test en dev) |
| Email dev | MailHog |
| Observabilidad | structlog + Sentry |
| Testing | pytest + Playwright + Locust |
| CI/CD | Bitbucket Pipelines |

---

## Estructura del repositorio

```
resuena/
├── CLAUDE.md               ← este archivo
├── docker-compose.yml      ← arranca el stack completo
├── requirements.txt        ← dependencias Python
├── pyproject.toml          ← config ruff + pytest
├── alembic.ini             ← config migraciones
├── alembic/                ← migraciones SQL
├── src/                    ← backend FastAPI
│   ├── api/                ← routers y endpoints
│   ├── services/           ← lógica de negocio
│   ├── repositories/       ← queries SQL
│   ├── models/             ← modelos SQLAlchemy
│   │   └── dto/            ← modelos Pydantic
│   ├── middleware/          ← auth, roles, rate limiting
│   ├── infra/              ← S3, Stripe, RabbitMQ, email
│   ├── workers/            ← consumers RabbitMQ
│   ├── config/             ← settings pydantic-settings
│   └── utils/              ← helpers puros
├── app/                    ← frontend Next.js
│   ├── (auth)/             ← rutas sin sesión
│   └── (dashboard)/        ← rutas protegidas
├── components/             ← componentes React reutilizables
├── lib/                    ← helpers frontend (api, fetcher)
├── hooks/                  ← custom hooks React
├── infra/                  ← Dockerfiles + scripts de infraestructura
│   ├── Dockerfile.api
│   ├── Dockerfile.app
│   ├── postgres/
│   │   └── init.sql
│   └── localstack/
│       └── init-s3.sh      ← crea buckets S3 en LocalStack al arrancar
├── tests/                  ← tests pytest + Playwright + Locust
├── docs/                   ← plan de fases, manuales, diagramas
│   ├── PLAN.md
│   ├── AGENTES.md
│   ├── SESION-TEMPLATE.md
│   └── fase-01.md … fase-15.md
├── .claude/
│   └── skills/             ← skills para Claude Code
└── .opencode/
    └── skills/             ← skills para OpenCode (mismo contenido)
```

---

## Skills disponibles

Antes de ejecutar cualquier tarea, revisa si existe una skill relevante en `.claude/skills/`.
Lee el campo `description` del frontmatter de cada `SKILL.md` para decidir cuál aplica.
Si aplica, léela **completa** antes de escribir código.

| Skill | Cuándo usarla |
|-------|--------------|
| `developer-skill` | Endpoints FastAPI, servicios, workers, integraciones S3/Stripe/RabbitMQ |
| `dba-skill` | Modelos SQLAlchemy, migraciones Alembic, queries, índices |
| `security-skill` | Auth, JWT, BCrypt, OTP, guards de rol, webhooks Stripe |
| `frontend-skill` | Páginas Next.js, componentes React, formularios, dashboards |
| `testing-skill` | Tests pytest, Playwright e2e, Locust, fixtures, mocks |
| `deployment-skill` | Bitbucket Pipelines, scripts deploy, Docker Compose prod |
| `document-skill` | Swagger, Postman, manuales, diagramas Mermaid, CHANGELOG |

---

## Reglas no negociables

Estas reglas aplican en **cada cambio**, sin excepciones:

### Arquitectura
- La dependencia de capas es estricta: `api → services → repositories → models`. Nunca al revés.
- Un endpoint nunca contiene lógica de negocio — delega 100% al service.
- Un service nunca lanza `HTTPException` — lanza excepciones propias tipadas.
- El router traduce excepciones del service a códigos HTTP.

### Base de datos
- PKs siempre UUID (`gen_random_uuid()` de pgcrypto), nunca SERIAL.
- Toda operación que modifique créditos o saldo usa `SELECT FOR UPDATE`.
- Timestamps siempre con timezone (`DateTime(timezone=True)`).

### Almacenamiento S3
- Los endpoints y services nunca usan `boto3`/`aioboto3` directamente.
- Toda operación de archivos pasa por `StorageService` (`src/infra/storage.py`).
- La BD guarda **claves S3** (ej. `campanas-audio/uuid/audio.mp3`), nunca URLs.
- Las URLs se generan como presigned con TTL al momento de servir al cliente.

### Seguridad
- Passwords: BCrypt cost ≥ 12.
- JWT: cookie HttpOnly + Secure + SameSite=Lax.
- Tokens de un solo uso: verificar con `SELECT FOR UPDATE` antes de consumir.
- MIME de uploads: validar con `libmagic`, no por extensión del nombre.
- Webhooks Stripe: verificar firma antes de procesar cualquier dato.
- **Nunca** loguear passwords, tokens, claves API ni datos bancarios.

### Bitácora
- Toda acción crítica se registra en `bitacora_eventos`:
  login, registro, aprobación profesional, compra créditos, envío campaña, entrega, retiro, cambios admin.

### Código
- `ruff check src/` debe pasar sin errores antes de entregar.
- `tsc --noEmit` debe pasar sin errores en el frontend.
- No hay `any` en TypeScript sin comentario explicando por qué.

---

## Cómo trabajar en una sesión

### Al INICIAR — pegar este prompt en Claude Code:

```
=== INICIO DE SESIÓN — Resuena ===

1. Lee este CLAUDE.md.
2. Lee docs/PLAN.md y revisa la tabla de fases.
3. Identifica la FASE ACTIVA: primera marcada [~], o si no hay ninguna,
   la primera [ ] posterior a la última [x].
4. Lee docs/fase-XX.md (sección Contexto + sección PROGRESO).
5. Lee el CHECKPOINT al final de docs/PLAN.md.
6. Responde con: "Fase XX — <título> | Progreso: N/M tareas | Próximo paso: <descripción>"
7. NO empieces a codificar. Espera confirmación.

=== FIN ===
```

### Al CERRAR — pegar este prompt en Claude Code:

```
=== CIERRE DE SESIÓN — Resuena ===

1. Actualiza checkboxes en docs/fase-XX.md ([x] completadas, [~] en progreso).
2. Actualiza "Última sesión" y "Próximo paso al reanudar" en docs/fase-XX.md.
3. Si la fase completó todas sus tareas: marca [x] en docs/PLAN.md y pon [~] a la siguiente.
4. Actualiza el CHECKPOINT en docs/PLAN.md.
5. Actualiza "Fase activa" en este CLAUDE.md (sección "Estado del proyecto").
6. git status para ver qué cambió.
7. Haz commit: chore(fase-XX): <resumen breve> — checkpoint <YYYY-MM-DD>
8. Pregunta si hacer push.
9. Imprime: qué se completó hoy | próximo paso | modelo recomendado para la próxima sesión.

=== FIN ===
```

Los prompts completos están en `docs/SESION-TEMPLATE.md`.

---

## Variables de entorno

Copiar `.env.example` a `.env` y completar antes de `docker compose up -d`.
Las variables críticas para el stack local son:

```bash
# Base de datos
DATABASE_URL=postgresql+asyncpg://portal:portal@postgres:5432/resuena

# Redis
REDIS_URL=redis://redis:6379/0

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/

# S3 / LocalStack (dev — no cambiar estos valores en dev)
STORAGE_PROVIDER=s3
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_REGION=us-east-1
AWS_S3_BUCKET=resuena-dev
AWS_ENDPOINT_URL=http://localstack:4566

# Email (dev — MailHog)
SMTP_HOST=mailhog
SMTP_PORT=1025

# App
APP_SECRET_KEY=dev-secret-key-cambiar-en-produccion-minimo-32-chars
ENVIRONMENT=development

# Stripe (modo test — obtener en dashboard.stripe.com)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

**Nunca commitear `.env` con valores reales.** Solo `.env.example` va al repositorio.

---

## Comandos frecuentes

```bash
# Arrancar el stack completo
docker compose up -d

# Ver logs de la API
docker compose logs -f api

# Aplicar migraciones
docker compose exec api alembic upgrade head

# Crear nueva migración
docker compose exec api alembic revision --autogenerate -m "descripcion"

# Correr tests
docker compose exec api pytest -q

# Lint
docker compose exec api ruff check src/

# Verificar tipos frontend
docker compose exec app npx tsc --noEmit

# Consola PostgreSQL
docker compose exec postgres psql -U portal resuena

# MailHog — ver emails enviados
open http://localhost:8025

# RabbitMQ management
open http://localhost:15672  # guest / guest

# LocalStack — verificar buckets S3
docker compose exec api aws --endpoint-url=http://localstack:4566 s3 ls
```

---

## Modelo recomendado por tipo de tarea

Ver `docs/AGENTES.md` para la guía completa. Resumen:

- **Arquitectura, seguridad, BD, pagos, RabbitMQ** → `claude-opus-4-7`
- **Endpoints CRUD, vistas, tests, documentación** → `claude-sonnet-4-6`
- **Renombres, formateo, fixtures triviales** → `claude-haiku-4-5-20251001`

La fase activa indica el modelo recomendado en su encabezado.