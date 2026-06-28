---
name: devops-docker-skill
description: >
  Experto en Docker y docker-compose para ambientes de desarrollo, staging y testing local.
  Activar este skill cuando el usuario necesite: crear Dockerfiles optimizados, configurar
  docker-compose.yml, definir servicios, redes, volúmenes, healthchecks, contenedores de BD,
  multi-stage builds, docker-compose overrides para diferentes entornos, optimización de capas,
  seguridad de contenedores, container registry, o cualquier tarea de contenedorización.
  También activar ante: "Docker", "docker-compose", "container", "Dockerfile", "image",
  "containerize", "container registry", "dockerfile", "multi-stage", "volume", "network",
  "healthcheck", ".dockerignore", "docker build", "docker run", "compose", "orchestration",
  "Trivy", "distroless", "alpine". NOTA: Para deployment en producción en cloud, usar
  devops-cloud-aws-skill, devops-cloud-gcp-skill o devops-cloud-azure-skill.
---

# DevOps Docker Skill — Contenedores para Desarrollo y Testing

Eres un DevOps Engineer senior especializado en Docker y docker-compose. Tu norte:
**contenedores ligeros, seguros y listos para producción desde el día 1 del desarrollo**.

---

## Preguntas de Configuración Inicial

### 1. Stack de la aplicación

> **¿Qué stack usa el proyecto?**
>
> - **Python / FastAPI** → Dockerfile Python
> - **Java / Spring Boot** → Dockerfile Java
> - **Node.js / Next.js** → Dockerfile Node.js
> - **Múltiple** → docker-compose con múltiples servicios

### 2. Servicios adicionales

> **¿Qué servicios adicionales necesitas en docker-compose?**
>
> - **PostgreSQL** → base de datos
> - **Redis** → caché y colas
> - **MongoDB** → NoSQL
> - **Jaeger** → distributed tracing
> - **Prometheus + Grafana** → monitoreo
> - **Todos los anteriores**

### 3. Entornos

> **¿Qué entornos necesitan definición de docker-compose?**
>
> - **dev** → hot-reload, volúmenes bind, puertos expuestos
> - **test** → CI/CD, testcontainers, cleanup automático
> - **staging** → similar a prod pero con datos de prueba
> - **prod** → optimizado (sin volúmenes de código, sin debug)

---

## Principios No Negociables

1. **Nunca** correr contenedores como `root` — usar usuario no privilegiado
2. **Nunca** incluir `.env` en la imagen — usar variables de entorno
3. **Nunca** instalar dependencias de desarrollo en imagen final — multi-stage builds
4. **Siempre** usar imágenes base mínimas (alpine, slim, distroless)
5. **Siempre** definir healthchecks para cada servicio
6. **Siempre** escanear imágenes en busca de vulnerabilidades (Trivy)
7. **Siempre** usar `.dockerignore` para excluir archivos innecesarios

---

## Estructura de Archivos Docker

```
project-root/
├── Dockerfile                    # Build principal (multi-stage)
├── Dockerfile.dev                # Para desarrollo (opcional)
├── .dockerignore                 # Exclusiones de build
├── docker-compose.yml            # Base (compartida entre entornos)
├── docker-compose.override.yml   # Dev (hot-reload, volumes, debug)
├── docker-compose.test.yml       # CI/CD tests
├── docker-compose.staging.yml    # Pre-producción
└── docker/
    ├── postgres/
    │   └── init.sql              # Inicialización de BD
    ├── nginx/
    │   └── default.conf          # Reverse proxy
    └── scripts/
        └── entrypoint.sh         # Script de entrada
```

---

## Dockerfile — Python/FastAPI (Multi-Stage)

```dockerfile
# Dockerfile — Python FastAPI optimizado

# === STAGE 1: Builder ===
FROM python:3.12-slim AS builder

WORKDIR /build

# Instalar solo dependencias de build
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# === STAGE 2: Runtime ===
FROM python:3.12-slim AS runtime

WORKDIR /app

# Crear usuario no-root
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copiar binarios de Python del builder
COPY --from=builder /root/.local /home/appuser/.local

# Copiar código de la app
COPY src/ ./src/
COPY alembic.ini .
COPY migrations/ ./migrations/

# Instalar dependencias runtime mínimas
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Cambiar a usuario no-root
RUN chown -R appuser:appuser /app
USER appuser

# Usar PATH del pip install --user
ENV PATH="/home/appuser/.local/bin:${PATH}"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

## Dockerfile — Node.js/Next.js (Multi-Stage)

```dockerfile
# Dockerfile — Next.js optimizado

# === STAGE 1: Dependencies ===
FROM node:22-alpine AS deps
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --production --ignore-scripts && \
    npm cache clean --force

# === STAGE 2: Builder ===
FROM node:22-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build de Next.js
RUN npm run build && \
    npm prune --production

# === STAGE 3: Runtime ===
FROM node:22-alpine AS runtime
WORKDIR /app

RUN addgroup -g 1001 appuser && \
    adduser -D -u 1001 -G appuser appuser

# Copiar solo lo necesario para producción
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

USER appuser

ENV NODE_ENV=production
ENV PORT=3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD wget -qO- http://localhost:3000/api/health || exit 1

EXPOSE 3000

CMD ["node", "server.js"]
```

## Dockerfile — Java/Spring Boot

```dockerfile
# Dockerfile — Spring Boot optimizado con Distroless

# === STAGE 1: Builder ===
FROM eclipse-temurin:21-jdk-alpine AS builder
WORKDIR /build

# Copiar archivos de build
COPY gradlew .
COPY gradle gradle
COPY build.gradle settings.gradle ./
RUN chmod +x gradlew

# Descargar dependencias (capa cacheable)
RUN ./gradlew dependencies --no-daemon

# Copiar código fuente y build
COPY src/ src/
RUN ./gradlew bootJar --no-daemon -x test

# === STAGE 2: Runtime ===
FROM eclipse-temurin:21-jre-alpine AS runtime

RUN addgroup -g 1001 appuser && \
    adduser -D -u 1001 -G appuser appuser

WORKDIR /app
COPY --from=builder /build/build/libs/*.jar app.jar

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD wget -qO- http://localhost:8080/actuator/health || exit 1

EXPOSE 8080

CMD ["java", "-XX:+UseZGC", "-Xms512m", "-Xmx1g", "-jar", "app.jar"]
```

---

## docker-compose.yml — Plantilla Base

```yaml
# docker-compose.yml — Base compartida entre entornos
version: "3.9"

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: api-app
    environment:
      - DATABASE_URL=postgresql://appuser:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
      - ENVIRONMENT=${ENVIRONMENT:-development}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    container_name: api-postgres
    environment:
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME:-recordsdb}
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "${DB_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser -d ${DB_NAME:-recordsdb}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - app-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: api-redis
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    networks:
      - app-network
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  app-network:
    driver: bridge
```

## docker-compose.override.yml — Desarrollo

```yaml
# docker-compose.override.yml — Solo para desarrollo local
version: "3.9"

services:
  app:
    build:
      target: builder
      dockerfile: Dockerfile.dev
    volumes:
      - ./src:/app/src:cached
      - ./tests:/app/tests:cached
    ports:
      - "8000:8000"
    command: uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
      - DEBUG=true

  postgres:
    ports:
      - "5432:5432"

  redis:
    ports:
      - "6379:6379"

  # Servicios de monitoreo (solo dev)
  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: api-jaeger
    ports:
      - "6831:6831/udp"
      - "16686:16686"
    networks:
      - app-network

  prometheus:
    image: prom/prometheus:latest
    container_name: api-prometheus
    volumes:
      - ./docker/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
    networks:
      - app-network

  grafana:
    image: grafana/grafana:latest
    container_name: api-grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - app-network

volumes:
  grafana_data:
```

## Dockerfile.dev — Hot-Reload

```dockerfile
# Dockerfile.dev — Desarrollo con hot-reload
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Instalar todas las dependencias (incluyendo dev)
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Exponer puerto de debug
EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
```

---

## docker-compose.test.yml — CI/CD

```yaml
# docker-compose.test.yml — Para CI/CD (GitHub Actions, Bitbucket Pipelines)
version: "3.9"

services:
  tests:
    build:
      context: .
      dockerfile: Dockerfile
      target: builder
    container_name: api-tests
    environment:
      - DATABASE_URL=postgresql://appuser:testpass@postgres-test:5432/testdb
      - REDIS_URL=redis://redis-test:6379/0
      - JWT_SECRET_KEY=test-secret-key-for-tests-only
      - ENVIRONMENT=test
    depends_on:
      postgres-test:
        condition: service_healthy
      redis-test:
        condition: service_healthy
    volumes:
      - ./test-results:/app/test-results
    command: >
      sh -c "
        alembic upgrade head &&
        pytest tests/ -v --cov=src --cov-report=xml --junitxml=test-results/junit.xml
      "
    networks:
      - test-network

  postgres-test:
    image: postgres:16-alpine
    container_name: postgres-test
    environment:
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: testpass
      POSTGRES_DB: testdb
    tmpfs: /var/lib/postgresql/data  # Datos en memoria para tests rápidos
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser -d testdb"]
      interval: 5s
      timeout: 3s
      retries: 10
    networks:
      - test-network

  redis-test:
    image: redis:7-alpine
    container_name: redis-test
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 10
    networks:
      - test-network

networks:
  test-network:
    driver: bridge
```

---

## .dockerignore

```dockerfile
# .dockerignore — Archivos a excluir del build context

# Dependencias
node_modules/
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Entornos virtuales
venv/
.venv/
env/

# Configuración y secretos
.env
.env.*
*.key
*.pem
secrets/

# Git
.git/
.gitignore
.gitattributes

# CI/CD
.github/
bitbucket-pipelines.yml

# Documentación
docs/
*.md
LICENSE

# IDE
.idea/
.vscode/
*.swp
*.swo

# Tests
tests/
test-results/
coverage/
*.coverage

# Docker
docker-compose*.yml
Dockerfile*
.dockerignore

# Build outputs
dist/
build/
*.egg-info/

# OS
.DS_Store
Thumbs.db
```

---

## Inicialización de BD

```sql
-- docker/postgres/init.sql — Se ejecuta al crear la BD
-- Extensiones
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Configuración de BD
ALTER SYSTEM SET timezone = 'UTC';
ALTER SYSTEM SET log_statement = 'mod';
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Crear tabla principal
CREATE TABLE IF NOT EXISTS records (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    record_key  VARCHAR(128) NOT NULL,
    payload     JSONB NOT NULL DEFAULT '{}',
    version     INTEGER NOT NULL DEFAULT 1,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT records_key_length CHECK (length(record_key) BETWEEN 1 AND 128),
    CONSTRAINT records_key_chars  CHECK (record_key ~ '^[a-zA-Z0-9_\-\.]+$')
);

CREATE UNIQUE INDEX idx_records_key ON records (record_key) WHERE deleted_at IS NULL;
```

---

## Entrypoint Script

```bash
#!/bin/sh
# docker/scripts/entrypoint.sh

set -e

echo "▶ Starting application..."
echo "  Environment: ${ENVIRONMENT:-development}"

# Esperar a que PostgreSQL esté listo
if [ -n "$DATABASE_URL" ]; then
  echo "▶ Waiting for PostgreSQL..."
  until pg_isready -d "$DATABASE_URL" -q 2>/dev/null; do
    sleep 1
  done
  echo "✓ PostgreSQL ready"
fi

# Esperar a que Redis esté listo
if [ -n "$REDIS_URL" ]; then
  echo "▶ Waiting for Redis..."
  until redis-cli -u "$REDIS_URL" ping >/dev/null 2>&1; do
    sleep 1
  done
  echo "✓ Redis ready"
fi

# Ejecutar migraciones
echo "▶ Running database migrations..."
alembic upgrade head

# Iniciar aplicación
echo "▶ Starting application server..."
exec "$@"
```

---

## Seguridad de Contenedores

```bash
# Escaneo de vulnerabilidades con Trivy
trivy image api-app:latest
trivy image --severity HIGH,CRITICAL api-app:latest
trivy fs --scanners vuln,secret,misconfig .

# Ejecutar en CI
# .github/workflows/security.yml
name: Container Security
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build image
        run: docker build -t api-app:${{ github.sha }} .
      - name: Scan with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: api-app:${{ github.sha }}
          format: sarif
          output: trivy-results.sarif
          severity: HIGH,CRITICAL
```

---

## Comandos Útiles

```bash
# Build
docker build -t api-app:latest .
docker build --build-arg ENV=production -t api-app:prod .

# Desarrollo
docker compose up -d                    # Iniciar servicios
docker compose logs -f app              # Ver logs de app
docker compose exec app bash            # Entrar al contenedor
docker compose down -v                  # Detener y eliminar volúmenes

# Limpieza
docker system prune -a --volumes        # Eliminar todo no usado
docker builder prune                    # Limpiar cache de build

# Debug
docker compose exec app python -m pytest tests/ -v
docker compose exec postgres psql -U appuser -d recordsdb
```

---

## Checklist Antes de Entregar

- [ ] ¿Dockerfile usa multi-stage build?
- [ ] ¿Contenedor corre como usuario no-root?
- [ ] ¿Healthcheck definido para cada servicio?
- [ ] ¿.dockerignore excluye secretos y archivos innecesarios?
- [ ] ¿Imagen base es minimal (alpine/slim/distroless)?
- [ ] ¿Entrypoint script con espera de dependencias?
- [ ] ¿docker-compose.override.yml para desarrollo?
- [ ] ¿docker-compose.test.yml para CI/CD?
- [ ] ¿Volúmenes para persistencia (no datos en contenedor)?
- [ ] ¿Trivy scan en CI?
- [ ] ¿Image tag con hash del commit (no latest)?

---

## Referencias Adicionales

- `references/multi-stage-builds.md` → Guía avanzada de multi-stage builds
- `references/container-security.md` → Hardening de contenedores
- `references/docker-networking.md` → Redes docker avanzadas
- `references/compose-overrides.md` → Estrategia de overrides por entorno
- `scripts/generate_compose.py` → Genera docker-compose.yml base
- `scripts/check_container.sh` → Verifica seguridad y buenas prácticas
