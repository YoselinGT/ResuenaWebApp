# Fase 01 — Bootstrap + Infraestructura

> **Estado:** `[x]` completada · **Días estimados:** 3 · **Modelo:** `claude-opus-4-7`
> **Skills:** `devops-docker-skill`, `developer-skill`
> **Pre-requisitos:** ninguno (fase de arranque)

---

## Contexto

El repo está vacío de código. El objetivo de esta fase es dejar la **infraestructura local ejecutándose con un solo comando** (`docker compose up -d`). Sin esto, ninguna otra fase puede empezar.

Servicios necesarios:
- **app** — Next.js 14 (App Router + TypeScript)
- **api** — FastAPI con Gunicorn + Uvicorn workers
- **postgres** — BD local (PostgreSQL 16)
- **rabbitmq** — colas + management UI
- **redis** — cache + rate limit + tokens efímeros
- **mailhog** — SMTP de pruebas con UI
- **localstack** — emulador local de AWS S3 (misma API que S3; en producción se apunta a S3 real sin cambiar código)

El esqueleto de código backend sigue el patrón por capas (`src/api/`, `src/services/`, `src/repositories/`, `src/models/`, `src/middleware/`, `src/config/`, `src/infra/`, `src/utils/`).

El frontend usa App Router con grupos `(auth)` y `(dashboard)`.

---

## Tareas

- [x] **T1.** Crear `docker-compose.yml` con los 7 servicios + redes + volúmenes nombrados.
- [x] **T2.** Crear `infra/Dockerfile.api` (multi-stage: builder + runtime con `python:3.12-slim`).
- [x] **T3.** Crear `infra/Dockerfile.app` (multi-stage: builder + runtime con `node:20-alpine`).
- [x] **T4.** Esqueleto backend: `src/main.py` (FastAPI con `/health`), estructura de carpetas vacías con `__init__.py`.
- [x] **T5.** Esqueleto frontend: `package.json`, `tsconfig.json`, `next.config.mjs`, `app/layout.tsx`, `app/page.tsx` (página "Hola Resuena").
- [x] **T6.** `.env.example` con todas las variables documentadas (sin valores reales). Variables de almacenamiento: `STORAGE_PROVIDER` (valores: `s3` | `gcs` | `azure`), `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_S3_BUCKET`, `AWS_ENDPOINT_URL` (vacío en prod, apunta a LocalStack en dev). Incluir también vars de Stripe y PostgreSQL.
- [x] **T7.** Healthchecks para api, postgres, rabbitmq, redis, localstack en `docker-compose.yml`.
- [x] **T8.** Volúmenes persistentes para `postgres_data`, `rabbitmq_data`, `redis_data`, `localstack_data`.
- [x] **T9.** Configurar `requirements.txt` (FastAPI, SQLAlchemy 2, alembic, pydantic-settings, asyncpg, structlog, bcrypt, python-jose, slowapi, redis, aio-pika, Pillow, stripe, pytest, ruff, `boto3`, `aioboto3` para S3 async).
- [x] **T10.** Configurar `package.json` del frontend (next 14, react 18, typescript, tailwindcss, recharts, @tremor/react, framer-motion, lucide-react, zustand, stripe-js).
- [x] **T11.** `README.md` raíz con instrucciones de arranque (Quickstart Fase 01) + guía Claude Code/OpenCode.
- [x] **T12.** Probar `docker compose up -d` end-to-end y validar criterios de done. **7/7 criterios deben pasar.**

---

## Archivos a crear

| Ruta | Propósito |
|------|-----------|
| `docker-compose.yml` | orquestación de servicios |
| `infra/Dockerfile.api` | imagen del backend FastAPI |
| `infra/Dockerfile.app` | imagen del frontend Next.js |
| `infra/postgres/init.sql` | crear BD `resuena` + extensiones (uuid-ossp, pgcrypto) |
| `infra/localstack/init-s3.sh` | script que crea los buckets S3 en LocalStack al iniciar |
| `src/main.py` | entry point FastAPI |
| `src/config/settings.py` | pydantic-settings con vars de entorno |
| `src/api/__init__.py` | router raíz |
| `src/services/__init__.py` | placeholder |
| `src/repositories/__init__.py` | placeholder |
| `src/models/__init__.py` | placeholder |
| `src/middleware/__init__.py` | placeholder |
| `src/infra/__init__.py` | placeholder |
| `src/utils/__init__.py` | placeholder |
| `requirements.txt` | dependencias Python |
| `pyproject.toml` | ruff + pytest config |
| `app/layout.tsx` | layout raíz Next.js |
| `app/page.tsx` | landing inicial |
| `app/globals.css` | reset + design tokens |
| `tailwind.config.ts` | configuración Tailwind |
| `tsconfig.json` | TypeScript config |
| `next.config.mjs` | Next.js config |
| `package.json` | dependencias Node |
| `.env.example` | plantilla de variables de entorno |
| `.dockerignore`, `.gitignore` | exclusiones |
| `README.md` | guía de arranque |

---

## Tests / validaciones

- `curl http://localhost:8000/health` devuelve `{"status":"ok","service":"api"}`.
- `curl http://localhost:3000/` devuelve HTML con "Resuena".
- MailHog UI accesible en `http://localhost:8025`.
- RabbitMQ management UI accesible en `http://localhost:15672` (guest/guest).
- `aws s3 ls --endpoint-url=http://localhost:4566` lista los buckets creados por el script de init.
- `docker compose exec api psql $DATABASE_URL -c "SELECT 1"` retorna OK.
- `docker compose exec api redis-cli -h redis PING` responde `PONG`.

---

## Skill recomendado por tarea

- **T1, T2, T3, T7, T8, T12:** `devops-docker-skill`.
- **T4, T6, T9:** `developer-skill` (estructura FastAPI por capas).
- **T5, T10:** `frontend-skill` (estructura Next.js App Router).
- **T11:** `document-skill`.

---

## PROGRESO

- [x] T1 — docker-compose.yml
- [x] T2 — Dockerfile.api
- [x] T3 — Dockerfile.app
- [x] T4 — Esqueleto backend
- [x] T5 — Esqueleto frontend
- [x] T6 — .env.example
- [x] T7 — Healthchecks
- [x] T8 — Volúmenes
- [x] T9 — requirements.txt
- [x] T10 — package.json
- [x] T11 — README.md
- [x] T12 — Validación end-to-end

**Última sesión:** 2026-06-27 — Fase 01 completada. Stack levantado con `docker compose up -d`;
7/7 criterios de done validados (API /health, frontend, PostgreSQL+pgcrypto, Redis, RabbitMQ,
LocalStack S3 con buckets/prefijos, MailHog). Se ajustó `boto3==1.35.74` por conflicto de
dependencias con `aioboto3`. Se añadió scaffold mínimo de Alembic (env.py + script.py.mako)
para que el build del contenedor y los mounts funcionen; los modelos se conectan en Fase 02.

**Próximo paso al reanudar:** Iniciar Fase 02 — Modelo de datos + migraciones. Definir `Base`
declarativa de SQLAlchemy, conectar `target_metadata` en `alembic/env.py` y crear la primera
migración (`alembic revision --autogenerate`).
