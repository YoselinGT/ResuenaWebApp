# Fase 06c — Migración retroactiva: precio_creditos en medios del curador

> **Estado:** `[ ]` pendiente · **Días estimados:** 1 · **Modelo:** `claude-opus-4-7`
> **Skill:** `dba-skill`, `developer-skill`
> **Pre-requisitos:** Fase 06b `[x]`

---

## Contexto

La fase 02 ya está ejecutada. La fase 04b implementó la gestión de medios del curador.
Esta fase agrega dos columnas a `curador_medios` que no existían en la BD original:
- `precio_creditos` — cuántos créditos cobra este medio por campaña (default 1)
- `descripcion_precio` — descripción de qué incluye (ej. "Reel de 15–60 segundos")

Estas columnas son necesarias antes de fase 08 (campañas), donde el artista ve el precio
de cada medio antes de seleccionarlo y el sistema calcula el total a retener.

También agrega `precio_snapshot` a `campana_medios` — la copia del precio al momento del
envío, para que cambios futuros del curador no afecten campañas ya enviadas.

Y agrega `monto_usd` a `creditos_transacciones` para trazabilidad del valor en USD de
cada transacción (el monto real según Stripe al momento de la compra).

---

## Tareas

- [ ] **T1.** Crear migración `0007_precio_medios.py`:
  ```python
  def upgrade() -> None:
      # curador_medios — precio por tipo de contenido
      op.add_column('curador_medios',
          sa.Column('precio_creditos', sa.Integer(), nullable=False, server_default='1'))
      op.create_check_constraint(
          'ck_curador_medios_precio', 'curador_medios', 'precio_creditos >= 1')
      op.add_column('curador_medios',
          sa.Column('descripcion_precio', sa.String(100), nullable=True))

      # campana_medios — snapshot de precio al enviar
      op.add_column('campana_medios',
          sa.Column('precio_snapshot', sa.Integer(), nullable=False, server_default='1'))

      # creditos_transacciones — trazabilidad USD
      op.add_column('creditos_transacciones',
          sa.Column('monto_usd', sa.Numeric(10, 2), nullable=True))

  def downgrade() -> None:
      op.drop_column('creditos_transacciones', 'monto_usd')
      op.drop_column('campana_medios', 'precio_snapshot')
      op.drop_constraint('ck_curador_medios_precio', 'curador_medios', type_='check')
      op.drop_column('curador_medios', 'descripcion_precio')
      op.drop_column('curador_medios', 'precio_creditos')
  ```

- [ ] **T2.** Aplicar y validar:
  ```bash
  docker compose exec api alembic upgrade head
  # Verificar:
  docker compose exec api python -c "
  from sqlalchemy import text
  from src.infra.db import sync_engine
  with sync_engine.connect() as c:
      r = c.execute(text('''
          SELECT column_name FROM information_schema.columns
          WHERE table_name IN ('curador_medios','campana_medios','creditos_transacciones')
          AND column_name IN ('precio_creditos','descripcion_precio','precio_snapshot','monto_usd')
          ORDER BY table_name, column_name
      '''))
      print([row[0] for row in r])
  "
  # Debe retornar: ['descripcion_precio', 'precio_creditos', 'monto_usd', 'precio_snapshot']
  ```

- [ ] **T3.** Probar rollback: `alembic downgrade -1` → exit 0 → `alembic upgrade head` → exit 0.

- [ ] **T4.** Actualizar endpoints de medios del curador en `src/api/curador_medios.py`
  (y su servicio) para aceptar y retornar `precio_creditos` y `descripcion_precio`:
    - `POST /curador/medios` — body acepta `precio_creditos` (int, min 1, default 1) y `descripcion_precio` (str nullable).
    - `PATCH /curador/medios/:id` — edita ambos campos.
    - `GET /curador/medios` — incluye ambos campos en el response.

- [ ] **T5.** Actualizar DTOs `src/models/dto/curador_medios.py`:
    - `CuradorMedioCreateDTO` — agregar `precio_creditos: int = 1` y `descripcion_precio: str | None = None`.
    - `CuradorMedioUpdateDTO` — agregar ambos campos como opcionales.
    - `CuradorMedioResponseDTO` — agregar ambos campos.

- [ ] **T6.** Tests:
    - `alembic upgrade head` → exit 0.
    - `alembic downgrade -1` → exit 0.
    - `POST /curador/medios` sin `precio_creditos` → usa default 1.
    - `POST /curador/medios` con `precio_creditos=0` → 422 (CHECK constraint vía validación Pydantic `ge=1`).
    - `PATCH /curador/medios/:id` con `precio_creditos=3` → actualizado, no afecta campañas existentes.

---

## Archivos a crear / modificar

| Ruta | Acción |
|------|--------|
| `alembic/versions/0007_precio_medios.py` | crear |
| `src/models/dto/curador_medios.py` | modificar — agregar precio_creditos |
| `src/services/curador_medios_service.py` | modificar — persistir precio_creditos |
| `src/api/curador_medios.py` | modificar — response incluye precio_creditos |
| `tests/integration/test_curador_medios.py` | modificar — agregar casos precio |

---

## Notas para el agente

- Esta fase **no toca campañas ni wallet** — solo agrega columnas a tablas de medios y transacciones.
- El campo `precio_snapshot` en `campana_medios` se llena en fase 08 al enviar la campaña.
- El campo `monto_usd` en `creditos_transacciones` se llena en fase 06b al procesar el webhook.
- Los medios existentes quedan con `precio_creditos=1` (el default) — retrocompatible.
- **No hay estados de campañas nuevos aquí** (propuesta/pendiente_envio van en fase 08).

---

## Skill recomendado

- **T1-T3:** `dba-skill`.
- **T4-T5:** `developer-skill`.
- **T6:** `testing-skill`.

---

## PROGRESO

- [x] T1 — Migración 0007 (precio_creditos, descripcion_precio, precio_snapshot, monto_usd)
- [x] T2 — Aplicar y verificar columnas
- [x] T3 — Probar rollback
- [x] T4 — Actualizar endpoints curador_medios
- [x] T5 — Actualizar DTOs
- [x] T6 — Tests

**Última sesión:** 2026-07-10
**Próximo paso al reanudar:** T6 — tests de migración + endpoints (POST sin precio → default 1, POST con precio=0 → 422, PATCH precio → actualizado).