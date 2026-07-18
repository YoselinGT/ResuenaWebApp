# Fase 06e — Revisión granular de canales: flujo de solicitud y panel admin

> **Estado:** `[ ]` pendiente · **Días estimados:** 3 · **Modelo:** `claude-opus-4-7`
> **Skills:** `developer-skill`, `dba-skill`, `frontend-skill`
> **Pre-requisitos:** Fase 05 `[x]`, Fase 06c `[x]`

---

## Contexto

### Estado real después de las fases ejecutadas

**Fase 03 implementó:**
- `POST /auth/aplicar` — recibe `{tipo_profesional, url_portfolio}` y crea `solicitudes_curador`
- `POST /onboarding/medios` — el curador agrega canales a `curador_medios` durante el onboarding
- Estos son **dos pasos separados e independientes**: primero `/aplicar` (con portfolio), luego onboarding de canales

**Fase 05 implementó:**
- `GET /admin/solicitudes` — lista de solicitudes
- `GET /admin/solicitudes/:id` — detalle (solo datos de `solicitudes_curador` + `usuarios`)
- `app/(dashboard)/admin/solicitudes/page.tsx` — lista con filtros ✓
- `app/(dashboard)/admin/solicitudes/[id]/page.tsx` — **pendiente** (T12 quedó sin implementar)
- Aprobar/rechazar **por solicitud completa** (una decisión aplica al curador entero)

**Lo que NO existe y necesitamos:**
1. La vista de detalle `admin/solicitudes/[id]/page.tsx` nunca se implementó
2. El endpoint `GET /admin/solicitudes/:id` no incluye los canales del curador
3. No hay aprobación/rechazo por canal individual
4. El flujo de `/aplicar` con `url_portfolio` es innecesario — el canal ya es la evidencia real

### Modelo de datos en BD real

`solicitudes_curador`:
```
id, usuario_id FK, estado ENUM(pendiente,aprobada,rechazada),
notas_revision, revisor_id FK nullable, created_at, updated_at
```
**No hay `url_portfolio` en `solicitudes_curador`** — ese dato se recibía en el body del
endpoint `/auth/aplicar` pero no hay columna para él en la BD actual.

`curador_medios` (después de fase-06c):
```
id, curador_id FK, nombre, tipo ENUM(...), url, descripcion,
audiencia_estimada, precio_creditos, descripcion_precio, activo, created_at, updated_at
```
Más `curador_medio_generos` para los géneros por canal.

### Lo que cambia esta fase

**Problema 1:** El admin ve la solicitud pero no puede ver los canales del curador para
evaluar la calidad. Sin esa información no puede tomar una decisión informada.

**Problema 2:** La aprobación es todo-o-nada. Un curador puede tener un TikTok activo
con 50k seguidores y un blog abandonado. El admin no puede aprobar uno y rechazar otro.

**Problema 3:** La vista de detalle de solicitud nunca se implementó (T12 de fase-05).

**Solución:**
1. Reemplazar el flujo `/aplicar` + `url_portfolio` por: al agregar el primer canal en
   el onboarding, se crea la solicitud automáticamente.
2. Agregar `estado_revision` por canal en `curador_medios`.
3. Implementar la vista de detalle con lista de canales y acciones por canal.
4. La solicitud global se aprueba cuando el admin aprueba el primer canal.

### Regla de negocio — ¿qué ve el admin?

El curador **no tiene redes sociales propias**. `usuario_redes` es exclusivo de artistas.
Cada canal en `curador_medios` es en sí mismo una red social o medio — la URL del canal
de TikTok es su presencia en TikTok, la URL del blog es su presencia editorial.

El admin revisa canal por canal y decide si ese canal tiene la calidad suficiente.

### Estado de revisión por canal

```
curador_medios.estado_revision:
  'pendiente'  → canal registrado, aún no revisado (default)
  'aprobado'   → admin aprobó este canal
  'rechazado'  → admin rechazó (con motivo requerido)
```

**Regla operativa:** el curador puede recibir campañas cuando:
- `solicitudes_curador.estado = 'aprobada'` **Y**
- Tiene ≥ 1 canal con `estado_revision = 'aprobado'` Y `activo = true`

Solo los canales `aprobados` aparecen en el catálogo del artista.
La solicitud pasa a `aprobada` automáticamente al aprobar el primer canal.

---

## Tareas

### Base de datos

- [ ] **T1.** Migración `0008_canales_revision.py`:
  ```python
  def upgrade() -> None:
      # Estado de revisión por canal en curador_medios
      op.add_column('curador_medios',
          sa.Column('estado_revision', sa.String(20),
                    nullable=False, server_default='pendiente'))
      op.create_check_constraint(
          'ck_curador_medios_estado_revision', 'curador_medios',
          "estado_revision IN ('pendiente','aprobado','rechazado')")
      op.add_column('curador_medios',
          sa.Column('motivo_rechazo', sa.Text(), nullable=True))
      op.add_column('curador_medios',
          sa.Column('revisado_por', pg.UUID(as_uuid=True), nullable=True))
      op.create_foreign_key(
          'fk_curador_medios_revisado_por', 'curador_medios',
          'usuarios', ['revisado_por'], ['id'], ondelete='SET NULL')
      op.add_column('curador_medios',
          sa.Column('revisado_at', sa.DateTime(timezone=True), nullable=True))
      op.create_index('ix_curador_medios_estado_revision',
                      'curador_medios', ['estado_revision'])

  def downgrade() -> None:
      op.drop_index('ix_curador_medios_estado_revision')
      op.drop_constraint('fk_curador_medios_revisado_por',
                         'curador_medios', type_='foreignkey')
      op.drop_constraint('ck_curador_medios_estado_revision',
                         'curador_medios', type_='check')
      op.drop_column('curador_medios', 'revisado_at')
      op.drop_column('curador_medios', 'revisado_por')
      op.drop_column('curador_medios', 'motivo_rechazo')
      op.drop_column('curador_medios', 'estado_revision')
  ```
  **Nota:** no se elimina ninguna columna existente. `solicitudes_curador` no tenía
  `url_portfolio` en BD — ese campo solo existía en el DTO del endpoint, no en la tabla.

### Backend — flujo de solicitud

- [ ] **T2.** Eliminar o deprecar `POST /auth/aplicar` y reemplazarlo por creación
  automática de solicitud al agregar el primer canal. Buscar en todo el codebase
  referencias a `/auth/aplicar` y `url_portfolio` en DTOs/servicios.

- [ ] **T3.** Actualizar `src/auth/confirm/[token]` backend: para curadores, después de
  confirmar el email, redirigir a `/onboarding/medios` en lugar de `/aplicar`.

- [ ] **T4.** Actualizar `curador_medio_service.add_medio()` — al crear el primer canal
  activo del curador, disparar `on_primer_canal_creado(db, curador_id)`:
  ```python
  async def on_primer_canal_creado(db: AsyncSession, curador_id: UUID) -> None:
      """Crea solicitud si no existe. Idempotente."""
      existe = await db.scalar(
          select(SolicitudCurador)
          .where(SolicitudCurador.usuario_id == curador_id)
      )
      if existe:
          return
      solicitud = SolicitudCurador(usuario_id=curador_id, estado='pendiente')
      db.add(solicitud)
      await db.flush()
      await email_service.notificar_admin_nueva_solicitud(db, curador_id)
      await bitacora_service.log_event(
          db, autor_id=curador_id, accion='solicitud_curador_enviada',
          entidad='solicitudes_curador', entidad_id=str(solicitud.id))
  ```

- [ ] **T5.** Actualizar `GET /admin/solicitudes/:id` para incluir los canales del curador:
  ```json
  {
    "id": "uuid",
    "estado": "pendiente",
    "notas_revision": null,
    "created_at": "...",
    "usuario": {
      "nombre_completo": "Juan Pérez",
      "correo": "juan@email.com",
      "created_at": "..."
    },
    "canales": [
      {
        "id": "uuid",
        "nombre": "Urbano MX TikTok",
        "tipo": "tiktok",
        "url": "https://tiktok.com/@urbanomx",
        "descripcion": "Reels de música urbana",
        "audiencia_estimada": 48000,
        "precio_creditos": 2,
        "descripcion_precio": "Reel 15–60 seg",
        "generos": ["Reggaeton", "Trap"],
        "estado_revision": "pendiente",
        "motivo_rechazo": null,
        "revisado_at": null
      }
    ]
  }
  ```
  Implementar con `selectinload` sobre `curador_medios WHERE activo = true` +
  subquery de géneros via `curador_medio_generos`. Actualizar `SolicitudDetalleDTO`.

- [ ] **T6.** Endpoint `POST /admin/solicitudes/:sol_id/canales/:medio_id/aprobar`:
  - Valida que `medio_id.curador_id == solicitud.usuario_id`.
  - Marca `estado_revision='aprobado'`, `revisado_por=admin_id`, `revisado_at=now()`.
  - Si es el **primer canal aprobado** → `solicitudes_curador.estado='aprobada'`,
    email de bienvenida al curador (`aprobacion_curador.html` ya existe en fase-03).
  - Bitácora `canal_aprobado`. Solo Admin.

- [ ] **T7.** Endpoint `POST /admin/solicitudes/:sol_id/canales/:medio_id/rechazar`:
  - Body: `{motivo: string}` requerido (min 10 chars).
  - Marca `estado_revision='rechazado'`, guarda `motivo_rechazo`.
  - Si **todos** los canales activos quedan rechazados →
    `solicitudes_curador.estado='rechazada'`, email al curador.
  - Si quedan canales `pendiente` → solicitud sigue `pendiente`.
  - Bitácora `canal_rechazado`. Solo Admin.

- [ ] **T8.** Endpoint `POST /admin/solicitudes/:sol_id/canales/:medio_id/pendiente`:
  - Revierte a `pendiente`, limpia `motivo_rechazo`, `revisado_por`, `revisado_at`.
  - Si no queda ningún canal `aprobado` → solicitud vuelve a `pendiente`.
  - Solo Admin.

- [ ] **T9.** Actualizar `require_curador_aprobado` en `src/middleware/roles.py`:
  ```python
  async def require_curador_aprobado(current_user, db) -> Usuario:
      solicitud = await db.scalar(
          select(SolicitudCurador).where(
              SolicitudCurador.usuario_id == current_user.id,
              SolicitudCurador.estado == 'aprobada'))
      if not solicitud:
          raise HTTPException(403, "Tu solicitud aún no ha sido aprobada")
      canal_ok = await db.scalar(
          select(CuradorMedio).where(
              CuradorMedio.curador_id == current_user.id,
              CuradorMedio.estado_revision == 'aprobado',
              CuradorMedio.activo == True))
      if not canal_ok:
          raise HTTPException(403, "Ninguno de tus canales ha sido aprobado aún")
      return current_user
  ```

- [ ] **T10.** Actualizar `GET /medios/disponibles` (fase-08 lo implementa, esta fase
  agrega el filtro): `.where(CuradorMedio.estado_revision == 'aprobado')`.
  Si fase-08 aún no está ejecutada, documentar aquí que ese filtro debe incluirse.

### Frontend — onboarding curador

- [ ] **T11.** Actualizar `app/(auth)/confirm/[token]/page.tsx` — curadores redirigen
  a `/onboarding/medios` en lugar de `/aplicar`.

- [ ] **T12.** Eliminar `app/(auth)/aplicar/page.tsx`.

- [ ] **T13.** Actualizar `app/(onboarding)/medios/page.tsx`:
  - Aviso superior: "Agrega al menos un canal para enviar tu solicitud de aprobación."
  - Al guardar el primer canal → toast: "Canal agregado. Tu solicitud fue enviada al equipo."
  - Si ya tiene canales → lista + botón "Agregar otro canal".
  - Sin campo `url_portfolio` en ninguna parte.

- [ ] **T14.** Actualizar `app/(auth)/pendiente/page.tsx`:
  - Mostrar canales enviados a revisión con badge de `estado_revision`.
  - Chips por canal: ⏳ Pendiente / ✓ Aprobado / ✗ Rechazado + motivo si aplica.
  - Link "Agregar más canales" → dashboard de medios.

### Frontend — panel admin (implementa T12 pendiente de fase-05)

- [ ] **T15.** Implementar `app/(dashboard)/admin/solicitudes/[id]/page.tsx`
  (este componente nunca fue creado en fase-05):

  ```
  ┌──────────────────────────────────────────────────────────┐
  │ ← Solicitudes     Juan Pérez García     [Pendiente]      │
  │                   juan@email.com · Solicitó hace 3d      │
  ├──────────────────────────────────────────────────────────┤
  │ CANALES PARA REVISAR                                     │
  │                                                          │
  │ ┌─ CanalRevisionCard ─────────────────────────────────┐ │
  │ │ 🎬 TikTok  ·  Urbano MX TikTok        [Pendiente]  │ │
  │ │ https://tiktok.com/@urbanomx   [Abrir ↗]           │ │
  │ │ 48,000 seg · Reggaeton, Trap · 2 créditos          │ │
  │ │ "Reels de música urbana, 15–60 seg"                │ │
  │ │                          [✗ Rechazar] [✓ Aprobar]  │ │
  │ └────────────────────────────────────────────────────┘ │
  │                                                          │
  │ ┌─ CanalRevisionCard (rechazado) ─────────────────────┐ │
  │ │ 📝 Blog  ·  Blog Música MX          ✗ Rechazado     │ │
  │ │ https://blogmusica.mx      [Abrir ↗]                │ │
  │ │ Motivo: "Sin publicaciones recientes"               │ │
  │ │                               [↩ Revertir]          │ │
  │ └────────────────────────────────────────────────────┘ │
  │                                                          │
  │ Si canales = [] →                                        │
  │ "El curador no ha registrado canales aún."              │
  └──────────────────────────────────────────────────────────┘
  ```

  - Server component que carga datos, pasa a Client components para las acciones.
  - **No hay botón "Aprobar todo"** — la aprobación es siempre canal por canal.
  - El estado global de la solicitud se actualiza en tiempo real al aprobar/rechazar.
  - Los botones Aprobar/Rechazar solo aparecen si `solicitud.estado === 'pendiente'`.

- [ ] **T16.** Componente `CanalRevisionCard.tsx`:
  - Header: ícono por tipo + nombre + badge estado (`pendiente`/`aprobado`/`rechazado`).
  - URL con botón "Abrir ↗" (`target="_blank" rel="noopener noreferrer"`).
  - Fila de chips: audiencia, géneros, precio en créditos.
  - Descripción del precio si existe.
  - Footer de acciones según `estado_revision`:
    - `pendiente` → `[✗ Rechazar]` `[✓ Aprobar]`
    - `aprobado` → badge verde + `[↩ Revertir]`
    - `rechazado` → badge rojo + motivo + `[↩ Revertir]`
  - Loading en botones mientras el request está en vuelo.
  - Transición suave al cambiar estado (Framer Motion `layout`).
  - Ícono por tipo:
    ```typescript
    const TIPO_ICONO: Record<string, string> = {
      tiktok: '🎬', instagram: '📸', youtube: '▶️', spotify: '🎵',
      blog: '📝', facebook: '📘', twitter: '🐦', soundcloud: '🎧',
      radio: '📻', website: '🌐', eventos: '🎪', playlist: '🎶', otro: '🔗'
    }
    ```

- [ ] **T17.** Componente `RechazarCanalModal.tsx` — modal inline con:
  - Textarea "Motivo del rechazo" (min 10 chars, requerido).
  - Chips de sugerencias (insertan texto): "Sin actividad reciente",
    "Audiencia muy pequeña", "Contenido no relacionado con música",
    "URL no funciona o está privado", "Canal eliminado o suspendido".
  - Botones: `[Cancelar]` `[Confirmar rechazo]`.

---

## Archivos a crear / modificar

| Ruta | Acción |
|------|--------|
| `alembic/versions/0008_canales_revision.py` | crear |
| `src/models/curador_medios.py` | modificar — 4 columnas nuevas |
| `src/models/dto/admin_solicitudes.py` | modificar — canales en response |
| `src/services/curador_medio_service.py` | modificar — on_primer_canal_creado |
| `src/services/admin_solicitudes_service.py` | modificar — aprobar/rechazar/revertir canal |
| `src/middleware/roles.py` | modificar — require_curador_aprobado |
| `src/api/admin_solicitudes.py` | modificar — T5 endpoint + 3 endpoints nuevos |
| `src/api/medios_busqueda.py` | modificar — filtro estado_revision='aprobado' |
| `app/(auth)/confirm/[token]/page.tsx` | modificar — redirigir curadores |
| `app/(auth)/aplicar/page.tsx` | **eliminar** |
| `app/(auth)/pendiente/page.tsx` | modificar — badges de estado por canal |
| `app/(onboarding)/medios/page.tsx` | modificar — primer canal dispara solicitud |
| `app/(dashboard)/admin/solicitudes/[id]/page.tsx` | **crear** (T12 pendiente fase-05) |
| `components/admin/CanalRevisionCard.tsx` | crear |
| `components/admin/RechazarCanalModal.tsx` | crear |
| `tests/integration/test_canal_revision.py` | crear |

---

## Tests / validaciones

- `alembic upgrade head` → exit 0; columnas nuevas presentes en `curador_medios`.
- `alembic downgrade -1` → exit 0.
- Curador agrega primer canal → `solicitudes_curador` creada automáticamente, email admin.
- Curador agrega segundo canal → NO se crea segunda solicitud (idempotente).
- `POST aprobar canal` → `estado_revision='aprobado'`, `solicitud.estado='aprobada'`,
  email bienvenida enviado (verificar en MailHog).
- `POST aprobar` segundo canal (ya hay uno aprobado) → solo actualiza ese canal,
  solicitud sigue `aprobada` (no cambia).
- `POST rechazar` sin motivo → 422.
- `POST rechazar` con motivo < 10 chars → 422.
- Rechazar único canal activo → `solicitud.estado='rechazada'`.
- Rechazar 1 de 2 canales activos → solicitud sigue `pendiente`.
- `require_curador_aprobado` con solicitud `aprobada` pero 0 canales aprobados → 403.
- Canal `pendiente` → no aparece en `GET /medios/disponibles`.
- Canal `rechazado` → no aparece en `GET /medios/disponibles`.
- Canal `aprobado` de curador aprobado → aparece en `GET /medios/disponibles`.
- Vista admin `/solicitudes/[id]` renderiza con 0 canales → mensaje informativo.
- Vista admin muestra botones Aprobar/Rechazar solo si `estado === 'pendiente'`.

---

## Notas para el agente

- **`solicitudes_curador` no tiene columna `url_portfolio` en BD** — solo existía en el
  DTO/body del endpoint `/auth/aplicar`. Al buscar referencias, limpiar solo los DTOs y
  el endpoint, no hacer DROP COLUMN (la columna no existe).
- **Los curadores no tienen redes sociales de perfil** (`usuario_redes` es solo de artistas).
  La vista de detalle solo muestra canales de `curador_medios`, no hay sección de redes.
- El email `aprobacion_curador.html` ya existe (fase-03). Reutilizarlo en T6.
- `GET /medios/disponibles` se implementa en fase-08. Esta fase documenta el filtro
  `estado_revision='aprobado'` que debe incluirse ahí. Si ya está ejecutada, parchearla.
- `app/(dashboard)/admin/solicitudes/[id]/page.tsx` **nunca existió** — no modificar,
  crear desde cero.
- No hay "Aprobar todo" — la aprobación global es implícita al aprobar el primer canal.

---

## Skill recomendado

- **T1:** `dba-skill`.
- **T2-T10:** `developer-skill`.
- **T11-T17:** `frontend-skill`.

---

## PROGRESO

- [x] T1 — Migración 0008 (estado_revision + 3 columnas en curador_medios)
- [x] T2 — Eliminar POST /auth/aplicar + limpiar referencias url_portfolio
- [x] T3 — confirm/[token] → redirigir curadores a /onboarding/medios
- [x] T4 — curador_medio_service → on_primer_canal_creado
- [x] T5 — GET /admin/solicitudes/:id → incluir canales con estado_revision
- [x] T6 — POST aprobar canal
- [x] T7 — POST rechazar canal (motivo requerido)
- [x] T8 — POST revertir canal a pendiente
- [x] T9 — require_curador_aprobado → verifica canal aprobado
- [x] T10 — GET /medios/disponibles → filtro estado_revision='aprobado' (pendiente fase-08, documentado)
- [x] T11 — confirm/[token] frontend → redirect (backend ya lo hace, frontend sigue redirect)
- [x] T12 — Eliminar app/(auth)/aplicar/page.tsx
- [x] T13 — /onboarding/medios → primer canal dispara solicitud (toast + aviso)
- [x] T14 — /auth/pendiente → copia actualizada + link agregar canales
- [x] T15 — admin/solicitudes/[id]/page.tsx (reescrito con CanalRevisionCard)
- [x] T16 — CanalRevisionCard (con inline rejection form)
- [x] T17 — RechazarCanalModal (inline en CanalRevisionCard)

**Última sesión:** 2026-07-10
**Próximo paso al reanudar:** Fase 07 — Géneros musicales + Configuración de categorías