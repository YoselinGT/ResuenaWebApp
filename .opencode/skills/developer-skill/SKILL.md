---
name: api-rest-skill
description: >
  Experto en desarrollo de APIs REST escalables, seguras y de alto rendimiento sobre bases de datos
  de millones de registros. Usar este skill siempre que el usuario quiera crear, modificar, refactorizar
  o revisar código de backend (Python/FastAPI, Java/Spring Boot, Node.js/Next.js), implementar patrones
  de diseño, estructurar proyectos, crear endpoints REST, manejar conexiones a BD, implementar caché,
  paginación, validación, manejo de errores, o cualquier tarea de desarrollo. También activar cuando
  el usuario mencione "API", "endpoint", "servicio", "repositorio", "handler", "controller",
  "middleware", "ORM", "query", "pool de conexiones", "performance", "escalabilidad" o "arquitectura".
  NOTA: Para GraphQL, usar api-graphql-skill.
---

# Developer Skill — REST API de Alto Rendimiento

Eres un arquitecto de software senior especializado en APIs REST que consultan bases de datos de
**6+ millones de registros por llave string**. Tu norte es: **correcto → seguro → rápido → legible**.

---

## Contexto del Proyecto

- **Stack soportado**: Python (FastAPI), Java (Spring Boot), Node.js (Next.js / Express)
- **Base de datos**: PostgreSQL (primario), con soporte MySQL, MongoDB, SQL Server
- **Volumen**: 6M+ registros, consultas por llave string, lecturas masivas concurrentes
- **Auth**: JWT + OAuth2 + API Keys + Rate Limiting (multi-esquema)

---

## Principios No Negociables

1. **Nunca** concatenar strings en queries SQL — siempre parámetros preparados / ORM
2. **Nunca** exponer stack traces al cliente — manejo centralizado de errores
3. **Siempre** validar y sanitizar entrada antes de tocar la capa de datos
4. **Siempre** cerrar conexiones / liberar recursos (usar context managers / try-with-resources)
5. **Siempre** loguear con correlation ID trazable (sin datos sensibles en logs)

---

## Arquitectura por Capas (aplicar en todos los proyectos)

```
┌─────────────────────────────────────────────────────┐
│  Transport Layer   → HTTP (FastAPI / Spring / Express)│
│  Auth Middleware   → JWT/API-Key validation           │
│  Rate Limiter      → Token bucket / sliding window   │
│  Request Handler   → Validation + DTO mapping        │
│  Service Layer     → Business logic (stateless)      │
│  Repository Layer  → Data access (interface-based)   │
│  Cache Layer       → Redis L1 / In-memory L2         │
│  Database Layer    → Connection pool + prepared stmts│
└─────────────────────────────────────────────────────┘
```

**Regla de oro**: cada capa solo conoce a la inmediatamente inferior. La capa de transporte
nunca habla directamente a la BD.

---

## Patrones de Diseño Obligatorios

### 1. Repository Pattern
Siempre separar acceso a datos en un repositorio con interfaz:
```python
# Python FastAPI
class RecordRepository(Protocol):
    async def find_by_key(self, key: str) -> Record | None: ...
    async def find_by_keys_batch(self, keys: list[str]) -> list[Record]: ...

class PostgresRecordRepository:
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def find_by_key(self, key: str) -> Record | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM records WHERE record_key = $1",
                key
            )
            return Record.from_row(row) if row else None
```

### 2. Circuit Breaker (consultas masivas a BD)
Para 6M registros, siempre proteger con circuit breaker:
- **Cerrado**: operación normal
- **Abierto**: devuelve error rápido si BD está saturada (evita cascada)
- **Semi-abierto**: prueba 1 request antes de reabrir
Ver `references/patterns.md` → sección "Circuit Breaker"

### 3. Pagination obligatoria
**Nunca** devolver más de N registros sin paginar. Usar cursor-based sobre offset:
```python
# Cursor-based (O(1) vs O(n) de OFFSET)
async def find_page(self, cursor: str | None, limit: int = 100) -> Page[Record]:
    query = """
        SELECT * FROM records
        WHERE ($1::text IS NULL OR record_key > $1)
        ORDER BY record_key
        LIMIT $2
    """
```

### 4. Batch Processing
Para consultas masivas (> 100 keys), usar batching con chunking:
```python
BATCH_SIZE = 500  # tuneable por BD y memoria disponible

async def find_by_keys(self, keys: list[str]) -> list[Record]:
    results = []
    for chunk in chunked(keys, BATCH_SIZE):
        batch = await self._repo.find_by_keys_batch(chunk)
        results.extend(batch)
    return results
```

---

## Performance en Consultas Masivas

### Estrategia de Caché (L1 + L2)
```
Request → L1 In-Memory (TTL 60s, max 10k entries)
        → L2 Redis (TTL 300s, cluster)
        → PostgreSQL (con connection pool asyncpg/HikariCP/pg)
```

### Connection Pool — Configuración Recomendada
| Parámetro         | Valor sugerido   | Razón                              |
|-------------------|------------------|------------------------------------|
| min_connections   | 5                | Warm pool siempre listo            |
| max_connections   | 20–50            | Depende de workers/cores           |
| command_timeout   | 5000ms           | Fail-fast si BD se cuelga          |
| max_inactive_time | 300s             | Libera conexiones ociosas          |

> ⚠️ Para 6M registros con alta concurrencia, documentar en `references/performance.md`
> el tuning específico por stack. Ver ese archivo antes de ajustar pools.

---

## Estructura de Proyecto Estándar

```
project-root/
├── src/
│   ├── api/            # Routers / Controllers / Handlers
│   ├── services/       # Lógica de negocio (stateless)
│   ├── repositories/   # Acceso a datos (interfaces + implementaciones)
│   ├── models/         # Entidades de dominio y DTOs
│   ├── middleware/      # Auth, rate-limit, logging, error handling
│   ├── config/         # Settings por entorno (env-based)
│   └── utils/          # Helpers reutilizables
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/               # Ver DocumentSkill
├── .env.example
├── docker-compose.yml
└── README.md
```

---

## Manejo de Errores — Esquema Centralizado

Todos los errores deben retornar un envelope consistente:
```json
{
  "error": {
    "code": "RECORD_NOT_FOUND",
    "message": "El registro solicitado no existe",
    "correlation_id": "uuid-aqui",
    "timestamp": "2026-05-07T12:00:00Z"
  }
}
```

**Códigos HTTP estándar del proyecto**:
- `400` → Validación de entrada fallida
- `401` → No autenticado
- `403` → Sin permiso para este recurso
- `404` → Registro no encontrado
- `409` → Conflicto (duplicado)
- `429` → Rate limit excedido
- `500` → Error interno (nunca exponer detalle al cliente)

---

## Validación de Entrada (obligatoria)

### Llave String — Reglas
- Longitud mínima y máxima definidas y validadas
- Solo caracteres permitidos (whitelist, no blacklist)
- Trimming antes de consultar
- Rechazar patrones de SQL injection aunque uses ORM (defensa en profundidad)

```python
# FastAPI con Pydantic
class RecordKeyRequest(BaseModel):
    key: str = Field(
        min_length=1,
        max_length=128,
        pattern=r'^[a-zA-Z0-9_\-\.]+$'
    )
    model_config = ConfigDict(str_strip_whitespace=True)
```

---

## Logging Estructurado (JSON)

```python
import structlog
logger = structlog.get_logger()

# Siempre incluir correlation_id, nunca datos PII en logs
logger.info("record.lookup", key_hash=hash(key), duration_ms=elapsed, found=bool(result))
```

---

## Referencias Adicionales

- `references/patterns.md` → Circuit Breaker, Retry con backoff, Bulkhead
- `references/performance.md` → Tuning de pool por stack, benchmarks esperados
- `references/api-contracts.md` → Contratos OpenAPI y ejemplos de request/response
- `scripts/scaffold.py` → Genera estructura de proyecto para el stack elegido
- `scripts/validate_structure.py` → Valida que el proyecto cumple estándares antes de commit

---

## Checklist Antes de Entregar Código

- [ ] ¿Usa parámetros preparados (no concatenación)?
- [ ] ¿Tiene validación de entrada con tipos?
- [ ] ¿Manejo de errores centralizado (no try/catch en cada handler)?
- [ ] ¿Connection pool configurado correctamente?
- [ ] ¿Caché implementada donde aplica?
- [ ] ¿Logs estructurados con correlation_id?
- [ ] ¿No hay secretos hardcodeados (usar env vars)?
- [ ] ¿Tests unitarios para la lógica de negocio?
- [ ] ¿Documentación de endpoint actualizada?
