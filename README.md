# Resuena

> Plataforma web para la gestión de campañas musicales: conecta artistas con profesionales de la industria (bloggers, playlisters, influencers, creadores de reels).

Los artistas compran créditos y los gastan enviando campañas; los profesionales las reciben, evalúan y entregan contenido editorial. Funcionalidad diferenciadora: un editor anti-IA para bloggers que captura metadatos de escritura y calcula una puntuación de autenticidad.

---

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend API | Python 3.12 + FastAPI + Gunicorn/Uvicorn |
| Frontend | Next.js 14 (App Router) + TypeScript + Tailwind |
| Base de datos | PostgreSQL 16 + SQLAlchemy 2 async + Alembic |
| Cache / sesiones | Redis 7 |
| Mensajería | RabbitMQ 3.12 |
| Almacenamiento | AWS S3 (prod) / LocalStack (dev) vía `StorageProvider` |
| Pagos | Stripe (modo test en dev) |
| Email (dev) | MailHog |

---

## Requisitos

- Docker + Docker Compose (única dependencia para el stack local)
- Git

No necesitas Python ni Node instalados en el host: todo corre en contenedores.

---

## Inicio rápido (Quickstart — Fase 01)

```bash
# 1. Clonar y entrar al repo
git clone <repo-url> resuena
cd resuena

# 2. Crear el .env a partir de la plantilla
cp .env.example .env
#    (los valores de dev ya funcionan; completar Stripe si se va a probar pagos)

# 3. Arrancar el stack completo
docker compose up -d

# 4. Ver el estado de los servicios
docker compose ps
```

La primera vez tarda unos minutos (build de imágenes + descarga). Cuando todos los
servicios estén `healthy`, la plataforma está lista.

---

## Servicios y puertos

| Servicio | URL / Puerto | Notas |
|----------|--------------|-------|
| Frontend (Next.js) | http://localhost:3000 | landing "Hola Resuena" |
| API (FastAPI) | http://localhost:8000 | docs en `/docs` |
| API health | http://localhost:8000/health | `{"status":"ok","service":"api"}` |
| PostgreSQL | `localhost:5432` | usuario/clave: `portal` / `portal`, BD `resuena` |
| Redis | `localhost:6379` | — |
| RabbitMQ | http://localhost:15672 | management UI — `guest` / `guest` |
| MailHog | http://localhost:8025 | bandeja de correo de pruebas |
| LocalStack (S3) | http://localhost:4566 | emulador AWS S3 |

---

## Verificación (criterios de done Fase 01)

```bash
# API responde
curl http://localhost:8000/health
# → {"status":"ok","service":"api"}

# Frontend responde con HTML "Resuena"
curl -s http://localhost:3000/ | grep -i resuena

# PostgreSQL accesible
docker compose exec postgres psql -U portal -d resuena -c "SELECT 1"

# Redis responde PONG
docker compose exec redis redis-cli PING

# RabbitMQ vivo
docker compose exec rabbitmq rabbitmq-diagnostics -q ping

# Buckets S3 creados por el script de init de LocalStack
docker compose exec localstack awslocal s3 ls

# MailHog UI accesible
open http://localhost:8025
```

---

## Comandos frecuentes

```bash
docker compose up -d                 # arrancar
docker compose logs -f api           # logs del backend
docker compose logs -f app           # logs del frontend
docker compose down                  # detener (conserva datos)
docker compose down -v               # detener y BORRAR volúmenes

# Backend
docker compose exec api ruff check src/        # lint
docker compose exec api pytest -q              # tests
docker compose exec api alembic upgrade head   # migraciones (Fase 02+)

# Frontend
docker compose exec app npx tsc --noEmit       # chequeo de tipos
```

---

## Estructura del repositorio

```
resuena/
├── docker-compose.yml      # orquesta los 7 servicios
├── requirements.txt        # dependencias Python
├── package.json            # dependencias Node
├── pyproject.toml          # ruff + pytest
├── alembic/                # migraciones (scaffold; modelos en Fase 02)
├── src/                    # backend FastAPI (api/services/repositories/models/...)
├── app/                    # frontend Next.js (App Router)
├── components/ lib/ hooks/ # frontend reutilizable
├── infra/                  # Dockerfiles + init de Postgres/LocalStack
└── docs/                   # plan de fases y manuales
```

---

## Trabajar con Claude Code / OpenCode

Este repo está preparado para desarrollo asistido por agentes:

- **`CLAUDE.md`** (raíz) — contexto completo y reglas no negociables. Se lee automáticamente.
- **`docs/PLAN.md`** — tabla de fases y checkpoint global.
- **`docs/fase-XX.md`** — detalle y progreso de cada fase.
- **`.claude/skills/`** — skills especializadas (devops, developer, dba, security, frontend, testing, deployment, document).

**Al iniciar una sesión**, pega el prompt de inicio que está en `docs/SESION-TEMPLATE.md`.
El agente identifica la fase activa, lee su progreso y espera confirmación antes de codificar.

---

## Variables de entorno

Todas están documentadas en [`.env.example`](./.env.example). **Nunca** commitees un `.env`
con valores reales — solo `.env.example` va al repositorio.
