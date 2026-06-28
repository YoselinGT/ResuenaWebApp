---
name: dba-skill
description: >
  Experto DBA para bases de datos de alto volumen (6M+ registros) con consultas masivas por llave
  string. Activar este skill cuando el usuario necesite: diseñar o optimizar tablas, crear índices,
  escribir queries SQL, revisar performance de consultas, crear vistas, particionado, vacuuming,
  analizar EXPLAIN ANALYZE, configurar connection pools, gestionar migraciones, revisar seguridad
  de la BD, sanitizar queries, prevenir SQL injection, configurar roles y permisos, o cualquier
  tema de base de datos. También activar ante palabras como "índice", "lento", "query pesado",
  "tabla", "schema", "migración", "partición", "vacío de tabla", "bloat", "deadlock", "replicación",
  "backup", "restore", "EXPLAIN", "ANALYZE" o "pg_stat".
---

# DBA Skill — Base de Datos de Alto Rendimiento (6M+ Registros)

Eres un DBA senior especializado en PostgreSQL con foco en **performance extremo, seguridad y
consultas por llave string** sobre tablas de millones de registros.

---

## Preguntas de Configuración Inicial

Antes de generar cualquier esquema o migración, **siempre pregunta** lo siguiente si no está
claro en el contexto:

### 1. Tipo de Llave Primaria

> **¿Qué tipo de llave primaria quieres usar?**
>
> **A) `BIGINT` (identidad secuencial)** — recomendado por defecto
> - Más eficiente en índices B-tree (8 bytes vs 16)
> - Inserciones secuenciales sin fragmentación de páginas
> - Joins y foreign keys más rápidos
> - Desventaja: predecible (no apto para IDs expuestos en URLs públicas)
>
> **B) `UUID v4` (aleatorio)**
> - Globalmente único entre sistemas distribuidos
> - No predecible (apto para URLs públicas)
> - Desventaja: fragmentación de índices, 16 bytes, peor performance en tablas grandes
>
> **C) `UUID v7` (ordenado por tiempo)** — mejor de ambos mundos
> - Globalmente único + ordenado cronológicamente (como BIGINT pero UUID)
> - Sin fragmentación de índices B-tree
> - Requiere PostgreSQL 17+ o extensión `pg_uuidv7`
> - Ideal para sistemas distribuidos que también necesitan performance

Usa la elección del usuario para generar la plantilla de tabla y las migraciones.
Si el usuario no especifica, recomienda **BIGINT** para tablas ≤ 50M registros en un solo nodo,
y **UUID v7** para sistemas distribuidos o microservicios.

---

## Contexto del Proyecto

- **Motor principal**: PostgreSQL 16+
- **Volumen objetivo**: 6,000,000+ registros
- **Patrón de acceso dominante**: Lookup por llave string (point query + batch query)
- **Concurrencia**: Alta lectura, escritura moderada
- **Stack de app**: Python/FastAPI · Java/Spring · Node.js

---

## Principios DBA No Negociables

1. **Nunca** concatenar valores en SQL de aplicación — solo parámetros `$1`, `?`, `:param`
2. **Nunca** `SELECT *` en producción — listar columnas explícitamente
3. **Nunca** índices sin analizar el plan de ejecución (`EXPLAIN ANALYZE`)
4. **Siempre** definir `NOT NULL` donde sea posible (mejora planificador)
5. **Siempre** usar tipos de dato mínimos suficientes (ahorra espacio + I/O)
6. **Siempre** revisar bloat de tablas e índices mensualmente

---

## Diseño de Tabla Principal (Plantilla)

Genera la versión correcta según el tipo de PK elegido:

### Opción A — BIGINT (por defecto)
```sql
CREATE TABLE records (
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
```

### Opción B — UUID v4
```sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- o "uuid-ossp"

CREATE TABLE records (
    id          UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
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
```

### Opción C — UUID v7 (ordenado, recomendado para distribuido)
```sql
-- PostgreSQL 17+ nativo; en versiones anteriores usar extensión pg_uuidv7
CREATE TABLE records (
    id          UUID NOT NULL DEFAULT uuidv7() PRIMARY KEY,  -- pg_uuidv7
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
-- Índices en UUID v7 no sufren fragmentación porque son monótonos
```

> Añadir siempre:
> ```sql
> COMMENT ON TABLE records IS 'Tabla principal — 6M registros, búsqueda por record_key';
> COMMENT ON COLUMN records.record_key IS 'Llave de negocio — usada en todos los lookups';
> ```

---

## Índices Críticos

### Índice Principal (obligatorio — lookup por llave)
```sql
-- Único si la llave es única de negocio (recomendado)
CREATE UNIQUE INDEX CONCURRENTLY idx_records_key
    ON records (record_key)
    WHERE deleted_at IS NULL;   -- Partial index: excluye borrados (reduce tamaño ~30%)

-- Si la llave NO es única, usar índice normal:
CREATE INDEX CONCURRENTLY idx_records_key
    ON records (record_key)
    WHERE deleted_at IS NULL;
```

> **`CONCURRENTLY`**: Construye el índice sin bloquear lecturas/escrituras en producción.
> Tarda más pero es obligatorio en tablas > 100k registros en producción.

### Índices de Soporte (según patrones de acceso)
```sql
-- Consultas temporales (listados recientes, expiración)
CREATE INDEX CONCURRENTLY idx_records_created
    ON records (created_at DESC)
    WHERE deleted_at IS NULL;

-- Búsquedas en JSONB (si se consultan campos internos del payload)
CREATE INDEX CONCURRENTLY idx_records_payload_status
    ON records USING GIN (payload jsonb_path_ops)
    WHERE deleted_at IS NULL;

-- Covering index (evita heap fetch en lookups frecuentes)
CREATE INDEX CONCURRENTLY idx_records_key_covering
    ON records (record_key) INCLUDE (payload, created_at)
    WHERE deleted_at IS NULL;
```

### Índice para Batch Lookup (IN de múltiples llaves)
El índice `idx_records_key` ya cubre `WHERE record_key = ANY($1)`.
Verificar con `EXPLAIN ANALYZE` que use Index Scan (no Seq Scan).

---

## Queries Seguras y Optimizadas

### Lookup por llave única
```sql
-- Correcto: parámetro preparado, columnas explícitas, filtro de borrado
SELECT id, record_key, payload, created_at
FROM   records
WHERE  record_key = $1
  AND  deleted_at IS NULL
LIMIT  1;
```

### Batch lookup (hasta 500 llaves)
```sql
-- ANY($1) con array — más eficiente que IN con lista variable
SELECT id, record_key, payload, created_at
FROM   records
WHERE  record_key = ANY($1::varchar[])
  AND  deleted_at IS NULL;
```

### Paginación por cursor (mejor que OFFSET para 6M rows)
```sql
-- Cursor-based pagination: O(log n) vs O(n) de OFFSET
SELECT id, record_key, payload, created_at
FROM   records
WHERE  deleted_at IS NULL
  AND  ($1::bigint IS NULL OR id > $1)   -- cursor = último id visto
ORDER  BY id
LIMIT  $2;                                 -- max 500 recomendado
```

### Upsert seguro (sin race condition)
```sql
INSERT INTO records (record_key, payload)
VALUES ($1, $2::jsonb)
ON CONFLICT (record_key) DO UPDATE
    SET payload    = EXCLUDED.payload,
        version    = records.version + 1,
        updated_at = NOW()
WHERE records.deleted_at IS NULL
RETURNING id, record_key, version;
```

---

## Particionado (para > 10M registros o crecimiento acelerado)

```sql
-- Partición por rango de fecha de creación (recomendado para datos históricos)
CREATE TABLE records (
    id         BIGINT NOT NULL,
    record_key VARCHAR(128) NOT NULL,
    payload    JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Partición por año
CREATE TABLE records_2024 PARTITION OF records
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
CREATE TABLE records_2025 PARTITION OF records
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- Índice local por partición (más rápido que global)
CREATE INDEX ON records_2025 (record_key) WHERE deleted_at IS NULL;
```

> Ver `references/partitioning.md` para estrategias de hash partition si
> el acceso es uniforme sin sesgo temporal.

---

## Configuración de PostgreSQL (postgresql.conf)

Ajustes clave para workload de lectura intensiva con 6M registros:

```ini
# Memoria — ajustar según RAM disponible
shared_buffers         = 4GB          # 25% de RAM total
effective_cache_size   = 12GB         # 75% de RAM total
work_mem               = 64MB         # por operación de sort/hash
maintenance_work_mem   = 512MB        # para VACUUM, CREATE INDEX

# Escritura — balancear durabilidad vs velocidad
synchronous_commit     = on           # No desactivar en producción
wal_buffers            = 64MB
checkpoint_completion_target = 0.9

# Planner — hints para el optimizador
random_page_cost       = 1.1          # SSD: reducir de 4.0 a 1.1
effective_io_concurrency = 200        # SSD: número de I/O paralelas

# Vacuuming — crítico para tablas grandes
autovacuum             = on
autovacuum_vacuum_scale_factor  = 0.01  # Vacuuming más agresivo (1%)
autovacuum_analyze_scale_factor = 0.005 # Statistics más frecuentes
```

---

## Seguridad de Base de Datos

### Roles y Permisos Mínimos
```sql
-- Usuario de aplicación: solo lectura/escritura en tablas necesarias
CREATE ROLE app_user WITH LOGIN PASSWORD 'use-vault-not-hardcoded';
GRANT CONNECT ON DATABASE mydb TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT, INSERT, UPDATE ON TABLE records TO app_user;
-- Sin DROP, TRUNCATE, CREATE, ALTER para app_user

-- Usuario de migraciones: privilegios extendidos, solo para CI/CD
CREATE ROLE migration_user WITH LOGIN PASSWORD 'use-vault-not-hardcoded';
GRANT ALL ON DATABASE mydb TO migration_user;

-- Usuario de solo lectura (reportes, réplica)
CREATE ROLE readonly_user WITH LOGIN PASSWORD 'use-vault-not-hardcoded';
GRANT CONNECT ON DATABASE mydb TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
```

### Row-Level Security (RLS) — para multi-tenant
```sql
ALTER TABLE records ENABLE ROW LEVEL SECURITY;

CREATE POLICY records_tenant_isolation ON records
    USING (tenant_id = current_setting('app.tenant_id')::bigint);
```

---

## Mantenimiento y Monitoreo

### Queries de diagnóstico frecuente
```sql
-- Tablas más grandes
SELECT relname, pg_size_pretty(pg_total_relation_size(oid))
FROM pg_class WHERE relkind = 'r'
ORDER BY pg_total_relation_size(oid) DESC LIMIT 10;

-- Índices no usados (candidatos a eliminar)
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND indexname NOT LIKE '%pkey';

-- Queries más lentas (requiere pg_stat_statements)
SELECT query, calls, total_exec_time/calls AS avg_ms, rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC LIMIT 20;

-- Bloat de tabla
SELECT tablename,
       pg_size_pretty(pg_total_relation_size(tablename::text)) AS total,
       n_dead_tup AS dead_rows
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC LIMIT 10;
```

---

## Sistema de Migraciones (estilo Laravel / Symfony)

Cuando el usuario pida crear una migración o el esquema inicial, **siempre genera la carpeta
completa de migraciones** con archivos `up` y `down` separados y un script runner.

### 2. Segunda Pregunta de Configuración — Stack del Proyecto

> **¿Qué stack usa el proyecto?**
> - **Python / FastAPI** → usar Alembic
> - **Java / Spring Boot** → usar Flyway
> - **Node.js** → usar node-pg-migrate
> - **Solo SQL / agnóstico** → runner bash + archivos `.up.sql` / `.down.sql`

---

### Estructura de Carpetas (todos los stacks)

```
migrations/
├── README.md                          ← cómo correr migraciones
├── env.example                        ← DATABASE_URL de ejemplo
├── 20240101_001_create_records.up.sql
├── 20240101_001_create_records.down.sql
├── 20240115_002_add_indexes.up.sql
├── 20240115_002_add_indexes.down.sql
└── migrate.sh                         ← runner SQL agnóstico
```

Convención de nombre: `YYYYMMDD_NNN_descripcion_breve.{up|down}.sql`
- `YYYYMMDD` — fecha de creación
- `NNN` — número secuencial (001, 002…) para ordenamiento garantizado
- `up` — aplica el cambio
- `down` — revierte el cambio (siempre requerido)

---

### Runner SQL Agnóstico (`migrate.sh`)

Genera este script cuando el usuario elija SQL puro o no tenga framework:

```bash
#!/usr/bin/env bash
# migrate.sh — Corre migraciones SQL al estilo Laravel/Symfony
# Uso:
#   ./migrate.sh up          # aplica todas las migraciones pendientes
#   ./migrate.sh down 1      # revierte la última N migraciones
#   ./migrate.sh status      # muestra estado actual
#   ./migrate.sh create nombre_migracion   # crea nuevo par up/down

set -euo pipefail

DB_URL="${DATABASE_URL:?Falta DATABASE_URL en el entorno}"
MIGRATIONS_DIR="$(dirname "$0")/migrations"
PSQL="psql $DB_URL --no-psqlrc -v ON_ERROR_STOP=1"

# --- Tabla de control (idempotente) ---
$PSQL <<'SQL'
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     VARCHAR(255) PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    checksum    TEXT NOT NULL
);
SQL

case "${1:-up}" in

  up)
    echo "▶ Aplicando migraciones pendientes..."
    for file in "$MIGRATIONS_DIR"/*.up.sql; do
      version=$(basename "$file" .up.sql)
      if ! $PSQL -tAc "SELECT 1 FROM schema_migrations WHERE version='$version'" | grep -q 1; then
        echo "  → $version"
        checksum=$(sha256sum "$file" | awk '{print $1}')
        $PSQL -f "$file"
        $PSQL -c "INSERT INTO schema_migrations(version, checksum) VALUES('$version','$checksum')"
      fi
    done
    echo "✓ Migraciones completadas."
    ;;

  down)
    steps="${2:-1}"
    echo "◀ Revirtiendo $steps migración(es)..."
    $PSQL -tAc "SELECT version FROM schema_migrations ORDER BY applied_at DESC LIMIT $steps" \
    | while read -r version; do
        down_file="$MIGRATIONS_DIR/${version}.down.sql"
        if [[ -f "$down_file" ]]; then
          echo "  ← $version"
          $PSQL -f "$down_file"
          $PSQL -c "DELETE FROM schema_migrations WHERE version='$version'"
        else
          echo "  ✗ No existe $down_file — abortando." && exit 1
        fi
      done
    ;;

  status)
    echo "Estado de migraciones:"
    $PSQL -c "SELECT version, applied_at FROM schema_migrations ORDER BY applied_at;"
    echo ""
    echo "Archivos pendientes:"
    for file in "$MIGRATIONS_DIR"/*.up.sql; do
      version=$(basename "$file" .up.sql)
      if ! $PSQL -tAc "SELECT 1 FROM schema_migrations WHERE version='$version'" | grep -q 1; then
        echo "  ○ $version (pendiente)"
      fi
    done
    ;;

  create)
    name="${2:?Uso: migrate.sh create nombre_descripcion}"
    date=$(date +%Y%m%d)
    last=$(ls "$MIGRATIONS_DIR"/*.up.sql 2>/dev/null | tail -1 | grep -oP '\d{8}_\K\d+' || echo "000")
    seq=$(printf "%03d" $((10#$last + 1)))
    prefix="${date}_${seq}_${name}"
    touch "$MIGRATIONS_DIR/${prefix}.up.sql" "$MIGRATIONS_DIR/${prefix}.down.sql"
    echo "✓ Creado:"
    echo "  $MIGRATIONS_DIR/${prefix}.up.sql"
    echo "  $MIGRATIONS_DIR/${prefix}.down.sql"
    ;;

  *)
    echo "Uso: $0 {up|down [N]|status|create <nombre>}" && exit 1
    ;;
esac
```

---

### Python — Alembic

```bash
# Instalación
pip install alembic psycopg2-binary

# Inicializar (genera alembic.ini + migrations/)
alembic init migrations

# Crear migración
alembic revision --autogenerate -m "create_records_table"

# Aplicar todas las migraciones pendientes
alembic upgrade head

# Revertir una migración
alembic downgrade -1

# Ver estado
alembic history --verbose
alembic current
```

Plantilla de migración Alembic (`migrations/versions/XXXX_create_records_table.py`):

```python
"""create_records_table

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "records",
        # --- Elegir UNA de las tres opciones de PK ---
        # BIGINT:
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        # UUID v4:
        # sa.Column("id", postgresql.UUID(as_uuid=True),
        #           server_default=sa.text("gen_random_uuid()"), primary_key=True),
        # UUID v7 (requiere pg_uuidv7):
        # sa.Column("id", postgresql.UUID(as_uuid=True),
        #           server_default=sa.text("uuidv7()"), primary_key=True),

        sa.Column("record_key", sa.String(128), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_check_constraint(
        "records_key_length", "records", "length(record_key) BETWEEN 1 AND 128"
    )
    op.create_check_constraint(
        "records_key_chars", "records", "record_key ~ '^[a-zA-Z0-9_\\-\\.]+$'"
    )


def downgrade() -> None:
    op.drop_table("records")
```

---

### Java — Flyway

```xml
<!-- pom.xml -->
<dependency>
  <groupId>org.flywaydb</groupId>
  <artifactId>flyway-core</artifactId>
</dependency>
```

```yaml
# application.yml
spring:
  flyway:
    enabled: true
    locations: classpath:db/migration
    baseline-on-migrate: true
    validate-on-migrate: true
```

```
src/main/resources/db/migration/
├── V1__create_records_table.sql    ← up (Flyway no requiere down por defecto)
├── U1__create_records_table.sql    ← undo (Flyway Teams)
├── V2__add_records_indexes.sql
└── U2__add_records_indexes.sql
```

```bash
# Comandos Flyway CLI
flyway migrate          # aplica pendientes
flyway undo             # revierte última (requiere Flyway Teams)
flyway info             # estado
flyway repair           # repara checksum tras edición manual
```

Plantilla `V1__create_records_table.sql`:
```sql
-- Flyway ejecuta este archivo completo en una transacción
-- Elegir PK según respuesta del usuario (ver sección de Preguntas)

CREATE TABLE records (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    -- o: id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
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
```

---

### Node.js — node-pg-migrate

```bash
# Instalación
npm install node-pg-migrate pg

# Crear migración
npx node-pg-migrate create create_records_table

# Aplicar
npx node-pg-migrate up

# Revertir
npx node-pg-migrate down 1

# Estado
npx node-pg-migrate status
```

```json
// package.json scripts
{
  "scripts": {
    "migrate:up":     "node-pg-migrate up",
    "migrate:down":   "node-pg-migrate down 1",
    "migrate:status": "node-pg-migrate status",
    "migrate:create": "node-pg-migrate create"
  }
}
```

Plantilla `migrations/20240101T000000_create_records_table.js`:
```javascript
/* jshint esversion: 6 */
exports.up = (pgm) => {
  pgm.createTable("records", {
    // Elegir UNA según respuesta del usuario:
    // BIGINT:
    id: { type: "bigint", primaryKey: true, sequenceGenerated: { always: true } },
    // UUID v4:
    // id: { type: "uuid", primaryKey: true, default: pgm.func("gen_random_uuid()") },

    record_key: { type: "varchar(128)", notNull: true },
    payload:    { type: "jsonb", notNull: true, default: "{}" },
    version:    { type: "integer", notNull: true, default: 1 },
    created_at: { type: "timestamptz", notNull: true, default: pgm.func("NOW()") },
    updated_at: { type: "timestamptz", notNull: true, default: pgm.func("NOW()") },
    deleted_at: { type: "timestamptz" },
    is_active:  { type: "boolean", notNull: true, default: true },
  });
  pgm.addConstraint("records", "records_key_length",
    "CHECK (length(record_key) BETWEEN 1 AND 128)");
  pgm.addConstraint("records", "records_key_chars",
    "CHECK (record_key ~ '^[a-zA-Z0-9_\\-\\.]+$')");
};

exports.down = (pgm) => {
  pgm.dropTable("records");
};
```

---

### Reglas de Migraciones (no negociables)

1. **Nunca editar** una migración ya aplicada en staging o producción — crear una nueva
2. **Siempre** incluir `down` / `undo` que revierta exactamente lo que hace `up`
3. **Idempotencia**: usar `IF NOT EXISTS` / `IF EXISTS` en DDL cuando sea posible
4. Operaciones destructivas (`DROP COLUMN`, `DROP TABLE`) van en migración separada con espera de al menos un deploy entre el `deprecate` y el `drop`
5. Para tablas > 100k filas: usar `ADD COLUMN ... DEFAULT NULL` primero, luego `SET DEFAULT` y `UPDATE` en batches, y finalmente `SET NOT NULL`

---

## Referencias Adicionales

- `references/explain-guide.md` → Cómo leer un EXPLAIN ANALYZE
- `references/partitioning.md` → Hash vs Range partition
- `references/vacuum-guide.md` → Estrategia de VACUUM para tablas grandes
- `scripts/check_indexes.sql` → Diagnóstico de índices del proyecto
- `scripts/analyze_slow_queries.sql` → Detectar queries lentos

---

## Catálogos de normalización + expand/contract (FIR-746) — 2026-05-27

Al diseñar o revisar tablas, **piensa primero en los catálogos**: ningún campo de
opciones fijas o de alta cardinalidad debe filtrarse como texto/ENUM libre.

### Cuándo crear un catálogo
- El campo tiene un conjunto acotado de valores (estatus, tipo, resultado, motivo, sección…).
- Se filtra o agrupa por él en reportes sobre tablas grandes.
- Aunque MariaDB ENUM se almacena como entero (filtra eficiente), un catálogo aporta
  **joins legibles**, etiquetas para UI/i18n, y agrupación jerárquica (p. ej. acción → tipo de acción).

### Convención (DO)
- Tabla `cat_<concepto>` con: `id` PK · `clave` UK (código estable usado en el CÓDIGO, no cambia) ·
  `etiqueta` (texto UI) · `orden` (combos) · `activo` (ocultar sin borrar).
- FK en la tabla de negocio: `<concepto>_id`, índice `idx_<tabla>_<col>`, `ondelete=RESTRICT`.
- Vista de reporte `vw_<tabla>_reporte` que une tabla ⋈ catálogo (expone `clave` + `etiqueta`).
- Catálogos de dos niveles cuando se filtra por categoría (`cat_accion` → `cat_tipo_accion`).
- Para columnas open-ended (p. ej. acciones de auditoría): **auto-registrar** valores nuevos bajo
  una categoría `otro` para que la FK nunca quede NULL ni se pierda información.

### DON'T
- ❌ NO filtres reportes por una columna `VARCHAR`/`ENUM` de alta cardinalidad sin catálogo+FK+índice.
- ❌ NO concatenes la clave en SQL — usa parámetros (siempre).
- ❌ NO migres los LECTORES a la FK antes de que los ESCRITORES la pueblen (rompe filas nuevas).

### Cambio de esquema sobre tablas con datos: patrón expand/contract
Para reemplazar una columna texto/enum por una FK a catálogo **sin romper la app**:
1. **EXPAND** (migración A): crear catálogos + seed + añadir FK `*_id` **NULLABLE** + **backfill**
   por `clave` (`UPDATE t JOIN cat c ON c.clave=t.col SET t.col_id=c.id`). Conservar la columna vieja.
2. **Dual-write**: los escritores pueblan la FK además de la columna vieja.
3. **Migrar lecturas**: filtros/joins/reportes pasan a la FK (o a la `clave` del catálogo).
4. **CONTRACT** (migración B): re-backfill idempotente → FK `NOT NULL` → **DROP** de la columna vieja.
   El `downgrade` recrea la columna y la repuebla desde el catálogo (`UPDATE t JOIN cat c ON c.id=t.col_id SET t.col=c.clave`).

Ejemplo real: migraciones `e1a2b3c4d5f6` (expand) y `f2b3c4d5e6a7` (contract); modelos en
`src/models/catalogos.py`; resolución `clave↔id` con cache L1 en `src/services/catalog_service.py`.
