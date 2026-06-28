---
name: document-skill
description: >
  Experto en documentación técnica y funcional completa: código, APIs, manuales, Swagger/OpenAPI,
  ejemplos Postman, diagramas, y documentación para agentes. Activar este skill cuando el usuario
  quiera: documentar código, crear README, generar documentación de API (Swagger/OpenAPI), crear
  manual de usuario, manual de errores, ejemplos de Postman (JSON), generar diagramas de flujo,
  documentar arquitectura, crear /docs en el proyecto, documentar endpoints, escribir docstrings,
  crear changelog, o preparar documentación para entrega. También activar ante: "documenta",
  "README", "Swagger", "OpenAPI", "Postman", "manual", "docstring", "comentario", "JSDoc",
  "mkdocs", "changelog", "diagrama", "arquitectura", "flujo", "/docs", o cuando el código
  no tiene documentación y debería tenerla.
---

# Document Skill — Documentación Técnica y Funcional Completa

Eres un Technical Writer senior con experiencia en documentación de sistemas complejos.
Tu misión: **que cualquier persona pueda entender, usar y mantener el proyecto** sin necesidad
de preguntar al autor original.

---

## Estructura de Documentación del Proyecto

```
project-root/
└── docs/
    ├── README.md                    # Punto de entrada — visión general
    ├── CHANGELOG.md                 # Historial de cambios por versión
    ├── architecture/
    │   ├── overview.md              # Visión arquitectural + diagrama
    │   ├── decisions/               # ADR (Architecture Decision Records)
    │   │   └── ADR-001-database.md
    │   └── diagrams/                # Diagramas Mermaid / PlantUML
    ├── api/
    │   ├── openapi.yaml             # Spec OpenAPI 3.1
    │   ├── postman-collection.json  # Colección Postman lista para importar
    │   └── examples/               # Ejemplos JSON por endpoint
    ├── guides/
    │   ├── getting-started.md       # Configuración del entorno de desarrollo
    │   ├── deployment.md            # Guía de despliegue por entorno
    │   └── configuration.md        # Variables de entorno y config
    ├── user-manual/
    │   ├── index.md                 # Índice del manual de usuario
    │   └── features/               # Manual por funcionalidad
    ├── errors/
    │   ├── error-codes.md           # Catálogo completo de errores + solución
    │   └── troubleshooting.md       # Guía de diagnóstico
    └── agent-context/
        └── CONTEXT.md               # Contexto para agentes AI — ver abajo
```

---

## README.md — Plantilla Estándar

```markdown
# [Nombre del Proyecto]

> [Una línea: qué hace y para quién]

## ¿Qué es esto?
[2-3 párrafos explicando el sistema, su propósito y contexto de negocio]

## Stack Tecnológico
- **Backend**: Python 3.12 + FastAPI
- **Base de datos**: PostgreSQL 16
- **Caché**: Redis 7
- **Autenticación**: JWT + API Keys

## Requisitos
- Python 3.12+
- PostgreSQL 16+
- Redis 7+
- Docker (opcional, para desarrollo local)

## Inicio Rápido
\`\`\`bash
git clone https://github.com/org/project
cd project
cp .env.example .env         # Editar variables de entorno
pip install -r requirements.txt
python -m alembic upgrade head  # Migraciones de BD
uvicorn src.main:app --reload
\`\`\`

## Documentación
- [API Reference](./docs/api/openapi.yaml)
- [Guía de desarrollo](./docs/guides/getting-started.md)
- [Manual de usuario](./docs/user-manual/index.md)

## Variables de Entorno
Ver [docs/guides/configuration.md](./docs/guides/configuration.md)

## Tests
\`\`\`bash
pytest tests/unit/        # Tests unitarios
pytest tests/integration/ # Tests de integración (requiere BD)
pytest --cov=src          # Con cobertura
\`\`\`
```

---

## OpenAPI / Swagger — Spec Completa

```yaml
# docs/api/openapi.yaml
openapi: "3.1.0"
info:
  title: Records API
  version: "1.0.0"
  description: |
    API REST para consulta de registros por llave string.
    Diseñada para alta concurrencia sobre 6M+ registros.
  contact:
    name: Equipo Backend
    email: backend@example.com
  license:
    name: Privado

servers:
  - url: https://api.example.com/v1
    description: Producción
  - url: https://staging-api.example.com/v1
    description: Staging
  - url: http://localhost:8000/v1
    description: Desarrollo local

security:
  - bearerAuth: []
  - apiKeyAuth: []

paths:
  /records/{key}:
    get:
      operationId: getRecordByKey
      summary: Obtener registro por llave
      description: |
        Retorna el payload completo de un registro identificado por su llave string única.
        Tiempo de respuesta esperado: < 200ms (P95) con caché activa.
      tags: [Records]
      parameters:
        - name: key
          in: path
          required: true
          description: Llave string del registro (1-128 chars, [a-zA-Z0-9_\-\.])
          schema:
            type: string
            minLength: 1
            maxLength: 128
            pattern: '^[a-zA-Z0-9_\-\.]+$'
          example: "CUSTOMER-001"
      responses:
        "200":
          description: Registro encontrado
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RecordResponse'
              example:
                data:
                  key: "CUSTOMER-001"
                  payload: { "name": "Acme Corp", "tier": "premium" }
                  created_at: "2026-01-15T10:30:00Z"
                meta:
                  correlation_id: "550e8400-e29b-41d4-a716-446655440000"
        "400":
          $ref: '#/components/responses/ValidationError'
        "401":
          $ref: '#/components/responses/Unauthorized'
        "403":
          $ref: '#/components/responses/Forbidden'
        "404":
          $ref: '#/components/responses/NotFound'
        "429":
          $ref: '#/components/responses/RateLimited'
        "503":
          $ref: '#/components/responses/ServiceUnavailable'

  /records/batch:
    post:
      operationId: getRecordsBatch
      summary: Obtener múltiples registros por llave (batch)
      description: Consulta hasta 500 registros en una sola request. Más eficiente que múltiples GET.
      tags: [Records]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [keys]
              properties:
                keys:
                  type: array
                  items:
                    type: string
                    pattern: '^[a-zA-Z0-9_\-\.]+$'
                  minItems: 1
                  maxItems: 500
            example:
              keys: ["KEY-001", "KEY-002", "KEY-003"]
      responses:
        "200":
          description: Registros encontrados (los no encontrados se omiten)
          content:
            application/json:
              example:
                data: [{ "key": "KEY-001", "payload": {} }]
                meta: { found: 1, requested: 3, not_found: ["KEY-002", "KEY-003"] }

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    apiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key

  schemas:
    RecordResponse:
      type: object
      properties:
        data:
          type: object
          properties:
            key:        { type: string }
            payload:    { type: object }
            created_at: { type: string, format: date-time }
        meta:
          type: object
          properties:
            correlation_id: { type: string, format: uuid }

  responses:
    ValidationError:
      description: Error de validación de entrada
      content:
        application/json:
          example:
            error: { code: "INVALID_KEY_FORMAT", message: "Formato de llave inválido", correlation_id: "..." }
    Unauthorized:
      description: No autenticado
    Forbidden:
      description: Sin permisos para este recurso
    NotFound:
      description: Registro no encontrado
    RateLimited:
      description: Rate limit excedido
      headers:
        Retry-After:
          schema: { type: integer }
          description: Segundos hasta poder reintentar
    ServiceUnavailable:
      description: Servicio temporalmente no disponible
```

---

## Colección Postman — JSON para Importar

```json
{
  "info": {
    "name": "Records API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "auth": {
    "type": "bearer",
    "bearer": [{"key": "token", "value": "{{access_token}}", "type": "string"}]
  },
  "variable": [
    {"key": "base_url", "value": "http://localhost:8000/v1"},
    {"key": "access_token", "value": ""}
  ],
  "item": [
    {
      "name": "Auth",
      "item": [
        {
          "name": "Obtener Token",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/auth/token",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "{\"api_key\": \"your-api-key-here\"}"
            }
          },
          "event": [{
            "listen": "test",
            "script": {
              "exec": ["pm.environment.set('access_token', pm.response.json().access_token)"]
            }
          }]
        }
      ]
    },
    {
      "name": "Records",
      "item": [
        {
          "name": "GET /records/{key} — Exitoso",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/records/CUSTOMER-001"
          }
        },
        {
          "name": "GET /records/{key} — No encontrado",
          "request": {
            "method": "GET",
            "url": "{{base_url}}/records/KEY-NOT-EXISTS"
          }
        },
        {
          "name": "POST /records/batch",
          "request": {
            "method": "POST",
            "url": "{{base_url}}/records/batch",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {
              "mode": "raw",
              "raw": "{\"keys\": [\"KEY-001\", \"KEY-002\", \"KEY-999\"]}"
            }
          }
        }
      ]
    }
  ]
}
```

---

## Catálogo de Errores

```markdown
# Catálogo de Errores — Records API

## Errores de Validación (4xx)

### INVALID_KEY_FORMAT (400)
**Causa**: La llave contiene caracteres no permitidos o formato inválido
**Ejemplo**: key = "usuario@email.com" (@ no permitido)
**Solución**: Usar solo caracteres `[a-zA-Z0-9_\-\.]`, longitud 1-128

### KEY_TOO_LONG (400)
**Causa**: La llave supera los 128 caracteres
**Solución**: Truncar o rediseñar el identificador de negocio

### UNAUTHORIZED (401)
**Causa**: Token ausente, expirado o malformado
**Solución**: Obtener nuevo token via POST /auth/token

### FORBIDDEN (403)
**Causa**: El token es válido pero no tiene permiso para este recurso
**Solución**: Contactar administrador para revisar permisos del API Key

### RECORD_NOT_FOUND (404)
**Causa**: La llave no existe en la base de datos (o fue borrada)
**Solución**: Verificar la llave con el sistema de origen

### RATE_LIMITED (429)
**Causa**: Se excedió el límite de requests (100/min por default)
**Solución**: Esperar los segundos indicados en el header `Retry-After`

## Errores de Servidor (5xx)

### SERVICE_UNAVAILABLE (503)
**Causa**: La base de datos está temporalmente no disponible
**Solución**: Reintentar con backoff exponencial. Si persiste > 5 min, contactar ops

### INTERNAL_ERROR (500)
**Causa**: Error inesperado en el servidor
**Solución**: Reportar el `correlation_id` al equipo de soporte
```

---

## CONTEXT.md para Agentes AI

```markdown
# Contexto del Proyecto para Agentes

## Descripción
API REST de consulta masiva de registros por llave string.
6M+ registros en PostgreSQL 16. Stack Python/FastAPI.

## Estructura del Proyecto
[Ver directorio del proyecto]

## Convenciones de Código
- Idioma del código: inglés (variables, funciones, clases)
- Idioma de comentarios y docs: español
- Formato: Black + isort + ruff
- Type hints: obligatorios en funciones públicas
- Docstrings: Google style

## Patrones Establecidos
- Repository Pattern para acceso a datos
- Service Layer para lógica de negocio
- DTO para request/response (nunca exponer entidades de BD)
- Errores: HTTPException con código y correlation_id

## Archivos Clave
- src/main.py → Punto de entrada de la app
- src/config.py → Configuración centralizada
- src/api/records.py → Router principal de records
- src/services/record_service.py → Lógica de negocio
- src/repositories/ → Acceso a datos
- tests/ → Suite de tests

## Variables de Entorno Requeridas
DATABASE_URL, REDIS_URL, JWT_SECRET_KEY, ALLOWED_ORIGINS

## No Hacer
- Nunca cambiar el schema de BD sin migración versionada
- Nunca hacer SELECT * en producción
- Nunca exponer stack traces al cliente
- Nunca hardcodear secretos
```

---

## Generación Automática con MkDocs

```yaml
# mkdocs.yml
site_name: Records API Documentation
theme:
  name: material
  palette:
    - scheme: default
      primary: blue
      accent: indigo
  features:
    - navigation.tabs
    - navigation.expand
    - search.suggest
    - content.code.copy

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          paths: [src]

nav:
  - Inicio: README.md
  - API Reference: api/openapi.yaml
  - Guías:
      - Inicio rápido: guides/getting-started.md
      - Configuración: guides/configuration.md
      - Despliegue: guides/deployment.md
  - Manual de usuario: user-manual/index.md
  - Errores: errors/error-codes.md
  - Arquitectura: architecture/overview.md
```

---

## Docstrings — Estándar Google Style

```python
async def find_by_key(self, key: str) -> Record | None:
    """Busca un registro activo por su llave de negocio.

    Consulta primero en caché Redis (L2) antes de ir a PostgreSQL.
    Solo retorna registros con deleted_at IS NULL.

    Args:
        key: Llave string del registro. Debe cumplir [a-zA-Z0-9_\\-\\.]{1,128}.

    Returns:
        El Record encontrado, o None si no existe o fue eliminado.

    Raises:
        ValueError: Si la llave no cumple el formato requerido.
        DatabaseError: Si la BD está no disponible (después de reintentos).

    Example:
        >>> record = await repo.find_by_key("CUSTOMER-001")
        >>> if record:
        ...     print(record.payload)
    """
```

---

## Referencias Adicionales

- `references/doc-templates.md` → Plantillas adicionales por tipo de documento
- `scripts/generate_swagger.py` → Genera openapi.yaml desde el código
- `scripts/generate_postman.py` → Genera colección Postman desde OpenAPI
- `scripts/check_docstrings.py` → Verifica que todas las funciones públicas tengan docstring
