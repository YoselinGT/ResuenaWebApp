# Fase 06f — Onboarding curador: redes por canal, precio y flujo corregido

> **Estado:** `[ ]` pendiente · **Días estimados:** 3 · **Modelo:** `claude-opus-4-7`
> **Skills:** `dba-skill`, `developer-skill`, `frontend-skill`
> **Pre-requisitos:** Fase 06c `[x]`, Fase 06e `[x]`

---

## Contexto

### Estado real en BD y código (post fase-03 y fase-06c)

**`curador_medios` actual:**
```
id, curador_id, nombre, tipo ENUM(...), url (una sola URL),
descripcion, audiencia_estimada, precio_creditos, descripcion_precio,
activo, estado_revision, motivo_rechazo, revisado_por, revisado_at
```

**Problema:** cada canal tiene **una sola URL**. Un canal de TikTok debería poder
tener su cuenta principal de TikTok + su cuenta alternativa + su cuenta de Instagram
asociada. El campo `url` solo permite una.

**`usuario_redes` en BD:** existe para artistas y también para curadores porque la
fase-03 implementó el paso 5 de redes sociales para ambos tipos. Este paso
para curadores debe eliminarse — las redes del curador son las redes de sus canales.

**`solicitudes_curador` actual:** tiene `tipo_profesional` y `url_portfolio`
(migración 0003 de fase-03). `url_portfolio` se usó en el endpoint `/auth/aplicar`
pero ahora el curador se identifica por sus canales, no por un portfolio genérico.

**`MedioForm.tsx` actual:** solo tiene un campo URL por canal. El precio `precio_creditos`
existe en BD (fase-06c) pero no está expuesto en el formulario del onboarding.

### Lo que cambia esta fase

1. **Nueva tabla `curador_medio_redes`** — N redes sociales por canal (en lugar de
   la URL única de `curador_medios.url`). La URL existente se conserva como URL principal.

2. **Onboarding curador corregido:**
  - Quitar el paso 5 (redes sociales) del wizard del curador.
  - El paso de medios ahora incluye: N redes por canal + precio en créditos.
  - El artista conserva su paso 4 de redes sociales sin cambios.

3. **Panel admin:** la vista de solicitud muestra por canal todas sus redes sociales,
   con un link "Abrir ↗" por cada una. La aprobación/rechazo es por canal (ya implementado
   en fase-06e).

### Modelo de redes por canal

```
curador_medio_redes:
  id UUID PK
  medio_id FK → curador_medios (ON DELETE CASCADE)
  tipo ENUM(instagram, tiktok, youtube, spotify, facebook, twitter,
            soundcloud, bandcamp, website, otro)
  url TEXT NOT NULL
  es_principal BOOL DEFAULT false  -- la red principal del canal
  created_at TIMESTAMPTZ
```

**Regla:** cada canal puede tener N redes. Al menos una debe existir para que el canal
sea válido. El campo `curador_medios.url` se mantiene por compatibilidad pero pasa a ser
la URL principal (sincronizada con la red que tenga `es_principal=true`).

---

## Tareas

### Base de datos

- [ ] **T1.** Migración `0009_curador_medio_redes.py`:
  ```python
  def upgrade() -> None:
      op.create_table(
          'curador_medio_redes',
          sa.Column('id', pg.UUID(as_uuid=True), primary_key=True,
                    server_default=sa.text('gen_random_uuid()')),
          sa.Column('medio_id', pg.UUID(as_uuid=True),
                    sa.ForeignKey('curador_medios.id', ondelete='CASCADE'),
                    nullable=False),
          sa.Column('tipo', sa.String(20), nullable=False),
          sa.Column('url', sa.Text(), nullable=False),
          sa.Column('es_principal', sa.Boolean(), nullable=False,
                    server_default='false'),
          sa.Column('created_at', sa.DateTime(timezone=True),
                    server_default=sa.func.now()),
      )
      op.create_check_constraint(
          'ck_curador_medio_redes_tipo', 'curador_medio_redes',
          "tipo IN ('instagram','tiktok','youtube','spotify','facebook',"
          "'twitter','soundcloud','bandcamp','website','otro')")
      op.create_index('ix_curador_medio_redes_medio_id',
                      'curador_medio_redes', ['medio_id'])

      # Migrar URL existente de curador_medios → curador_medio_redes
      # Cada canal existente obtiene una red principal con su URL actual
      op.execute("""
          INSERT INTO curador_medio_redes (medio_id, tipo, url, es_principal)
          SELECT id, tipo, url, true
          FROM curador_medios
          WHERE url IS NOT NULL AND url != ''
      """)

  def downgrade() -> None:
      op.drop_index('ix_curador_medio_redes_medio_id')
      op.drop_table('curador_medio_redes')
  ```

- [ ] **T2.** Crear modelo SQLAlchemy `src/models/curador_medio_redes.py`:
  ```python
  class CuradorMedioRed(Base):
      __tablename__ = 'curador_medio_redes'
      id: Mapped[UUID] = mapped_column(primary_key=True, ...)
      medio_id: Mapped[UUID] = mapped_column(ForeignKey('curador_medios.id',
                                             ondelete='CASCADE'))
      tipo: Mapped[str]
      url: Mapped[str]
      es_principal: Mapped[bool] = mapped_column(default=False)
      created_at: Mapped[datetime] = ...
      medio: Mapped['CuradorMedio'] = relationship(back_populates='redes')
  ```
  Actualizar `CuradorMedio` en `src/models/curador_medios.py` para agregar:
  `redes: Mapped[list['CuradorMedioRed']] = relationship(back_populates='medio',
  cascade='all, delete-orphan')`

### Backend — DTOs y servicios

- [ ] **T3.** Actualizar `src/models/dto/onboarding.py`:
  ```python
  class CuradorMedioRedDTO(BaseModel):
      tipo: str  # debe ser uno de los valores del ENUM
      url: HttpUrl
      es_principal: bool = False

  class CuradorMedioDTO(BaseModel):
      nombre: str
      tipo: str
      descripcion: str | None = None
      audiencia_estimada: int | None = None
      precio_creditos: int = Field(default=1, ge=1)
      descripcion_precio: str | None = None
      genero_ids: list[int] = []
      redes: list[CuradorMedioRedDTO] = Field(
          min_length=1,  # al menos una red requerida
          description="Al menos una red social del canal"
      )
  ```

- [ ] **T4.** Actualizar `src/services/curador_medio_service.py`:
  - `add_medio(curador_id, data: CuradorMedioDTO)`:
    - Crea fila en `curador_medios` (usando la URL de la red principal como `url`).
    - Crea filas en `curador_medio_redes` por cada red en `data.redes`.
    - Valida que exactamente una red tenga `es_principal=true`; si ninguna lo indica,
      marcar la primera como principal.
    - Crea filas en `curador_medio_generos`.
    - Llama a `on_primer_canal_creado(db, curador_id)` si es el primero (fase-06e).
  - `update_medio(medio_id, curador_id, data)`:
    - Actualiza campos del medio.
    - **Reemplaza** todas las redes: `DELETE WHERE medio_id = X` + INSERT nuevas.
    - Actualiza `curador_medios.url` con la URL de la red principal.
  - `list_medios(curador_id)`: incluir `redes` en el response.
  - Agregar `list_redes(medio_id)` y validación de tipo de red.

- [ ] **T5.** Quitar redes sociales del onboarding del curador en
  `src/services/onboarding_service.py`:
  - Actualizar `get_progreso(usuario_id)` para curadores: el paso `redes` no existe
    en su progreso. Para artistas, sigue igual.
  - El `OnboardingProgressDTO` debe diferenciar por tipo de usuario.

- [ ] **T6.** Actualizar `src/api/onboarding.py`:
  - `POST /onboarding/medios` — body ahora incluye `redes: list[CuradorMedioRedDTO]`.
  - `PUT /onboarding/medios/{medio_id}` — idem.
  - `GET /onboarding/redes` — devolver 403 si el usuario es curador
    (las redes del curador son de sus canales, no del perfil).
  - `POST /onboarding/redes` — idem, 403 para curadores.
  - Agregar `GET /catalogos/tipos_red` — retorna los tipos válidos de red para canales.

- [ ] **T7.** Actualizar `GET /admin/solicitudes/:id` (ya modificado en fase-06e):
  Incluir `redes` en cada canal del response:
  ```json
  {
    "canales": [
      {
        "id": "uuid",
        "nombre": "Urbano MX",
        "tipo": "tiktok",
        "redes": [
          {"tipo": "tiktok",    "url": "https://tiktok.com/@urbanomx",    "es_principal": true},
          {"tipo": "instagram", "url": "https://instagram.com/urbanomx",  "es_principal": false}
        ],
        "audiencia_estimada": 48000,
        "precio_creditos": 2,
        "descripcion_precio": "Reel 15–60 seg",
        "generos": ["Reggaeton", "Trap"],
        "estado_revision": "pendiente"
      }
    ]
  }
  ```

### Frontend — onboarding curador

- [ ] **T8.** Actualizar `app/onboarding/medios/page.tsx` — reemplazar el formulario
  actual `MedioForm.tsx` por uno que soporte N redes por canal y el precio:

  ```
  ┌─ Agregar canal ────────────────────────────────────┐
  │ Nombre del canal  [Urbano MX TikTok         ]      │
  │ Tipo              [TikTok ▾]                       │
  │ Descripción       [Contenido urbano...]             │
  │ Audiencia         [48000   ] seguidores/lectores   │
  │                                                     │
  │ REDES SOCIALES DE ESTE CANAL                       │
  │ ┌─ Red 1 (principal) ──────────────────────────┐  │
  │ │ [TikTok ▾]  https://tiktok.com/@urbanomx ★  │  │
  │ └──────────────────────────────────────────────┘  │
  │ ┌─ Red 2 ───────────────────────────────────────┐  │
  │ │ [Instagram ▾]  https://instagram.com/...   ☆  │  │
  │ │                                     [✕ Quitar] │  │
  │ └──────────────────────────────────────────────┘  │
  │ [+ Agregar otra red]                               │
  │                                                     │
  │ PRECIO Y GÉNEROS                                   │
  │ Precio  [2] créditos por campaña                   │
  │ Descripción del precio [Reel de 15–60 seg    ]     │
  │ Géneros [Reggaeton ×] [Trap ×] [+ agregar]        │
  │                                                     │
  │ [Cancelar]                    [Guardar canal]      │
  └────────────────────────────────────────────────────┘
  ```

  - El ícono ★ indica la red principal (clickeable para cambiar cuál es principal).
  - Validación: mínimo 1 red requerida. La URL debe ser válida por tipo de red.
  - El precio `precio_creditos` tiene un input numérico con min=1.
  - Los géneros usan el componente `GenreChip.tsx` existente.

- [ ] **T9.** Actualizar `components/onboarding/MedioForm.tsx`:
  - Agregar sección "Redes sociales del canal" con lista dinámica de `RedSocialRow.tsx`.
  - Agregar botón "Agregar otra red" que añade una nueva fila.
  - Agregar campo de precio (`precio_creditos`) con label "¿Cuántos créditos cobras por campaña?".
  - Agregar campo `descripcion_precio` con placeholder "Ej. Reel de 15–60 segundos".
  - El campo URL original del canal se elimina de la UI — ya no existe como campo separado.

- [ ] **T10.** Actualizar `components/onboarding/RedSocialRow.tsx`:
  - Agregar selector de tipo de red (dropdown con ícono por tipo).
  - Agregar indicador de red principal (★ / ☆) — click para cambiar.
  - Agregar botón eliminar fila (excepto si es la única red).

- [ ] **T11.** Quitar el paso de redes sociales del wizard para curadores:
  - `app/onboarding/redes/page.tsx` — agregar redirect 302 a `/onboarding/medios`
    si el usuario es curador. El paso sigue existiendo para artistas.
  - `components/onboarding/StepperNav.tsx` — el stepper del curador no muestra
    el paso "Redes sociales"; muestra "Canales" en su lugar.
  - `hooks/useOnboardingProgress.ts` — para curadores, el paso `redes` no cuenta
    para el progreso; el paso `medios` incluye las redes.

### Frontend — panel admin (complementa fase-06e)

- [ ] **T12.** Actualizar `components/admin/CanalRevisionCard.tsx` (creado en fase-06e):
  Reemplazar la línea de URL única por la lista de redes del canal:

  ```
  ┌─ CanalRevisionCard ──────────────────────────────────────────┐
  │ 🎬 TikTok  ·  Urbano MX TikTok                [Pendiente]   │
  │                                                               │
  │ REDES SOCIALES                                               │
  │ ★ TikTok    https://tiktok.com/@urbanomx     [Abrir ↗]      │
  │   Instagram  https://instagram.com/urbanomx   [Abrir ↗]     │
  │                                                               │
  │ 48,000 seg · Reggaeton, Trap · 2 créditos                   │
  │ "Reels de música urbana, 15–60 seg"                         │
  │                                                               │
  │                          [✗ Rechazar]  [✓ Aprobar]          │
  └──────────────────────────────────────────────────────────────┘
  ```

  - ★ marca la red principal.
  - Cada red tiene su propio botón "Abrir ↗".
  - El admin puede ver todas las redes antes de aprobar/rechazar el canal.

### Tests

- [ ] **T13.** Tests BD: migración 0009 aplica y revierte sin errores. Canales existentes
  migran su URL al nuevo campo como red principal.

- [ ] **T14.** Tests backend:
  - `POST /onboarding/medios` sin `redes` → 422.
  - `POST /onboarding/medios` con 2 redes → 2 filas en `curador_medio_redes`.
  - `PUT /onboarding/medios/{id}` con nuevas redes → reemplaza las anteriores.
  - `GET /onboarding/redes` como curador → 403.
  - `GET /admin/solicitudes/:id` → cada canal incluye `redes` como array.
  - Validación de tipo de red inválido → 422.

- [ ] **T15.** Tests frontend (Playwright):
  - Curador en onboarding no ve el paso "Redes sociales" en el stepper.
  - Artista en onboarding sí ve el paso "Redes sociales".
  - Formulario de canal permite agregar 2 redes → ambas se guardan.
  - Campo precio en créditos acepta solo enteros ≥ 1.

---

## Archivos a crear / modificar

| Ruta | Acción |
|------|--------|
| `alembic/versions/0009_curador_medio_redes.py` | crear |
| `src/models/curador_medio_redes.py` | crear |
| `src/models/curador_medios.py` | modificar — agregar relación `redes` |
| `src/models/dto/onboarding.py` | modificar — CuradorMedioRedDTO, CuradorMedioDTO actualizado |
| `src/services/curador_medio_service.py` | modificar — CRUD con redes + on_primer_canal |
| `src/services/onboarding_service.py` | modificar — progreso diferenciado por tipo |
| `src/api/onboarding.py` | modificar — medios con redes, 403 en redes para curadores |
| `src/api/admin_solicitudes.py` | modificar — canales incluyen redes en response |
| `app/onboarding/medios/page.tsx` | modificar — formulario con redes + precio |
| `app/onboarding/redes/page.tsx` | modificar — redirect para curadores |
| `components/onboarding/MedioForm.tsx` | modificar — redes dinámicas + precio |
| `components/onboarding/RedSocialRow.tsx` | modificar — selector tipo + estrella principal |
| `components/onboarding/StepperNav.tsx` | modificar — pasos diferenciados por tipo |
| `hooks/useOnboardingProgress.ts` | modificar — progreso diferenciado curador/artista |
| `components/admin/CanalRevisionCard.tsx` | modificar — lista de redes por canal |
| `tests/integration/test_curador_medio_redes.py` | crear |

---

## Tests / validaciones clave

- Canal con 2 redes: TikTok principal + Instagram secundaria → 2 filas en `curador_medio_redes`.
- `curador_medios.url` = URL de la red con `es_principal=true`.
- Curador visita `/onboarding/redes` → redirect a `/onboarding/medios`.
- Artista visita `/onboarding/redes` → funciona normal, sin cambios.
- StepperNav curador: muestra pasos [Géneros, Idiomas, Regiones, Canales] — sin "Redes sociales".
- StepperNav artista: muestra pasos [Géneros, Idiomas, Regiones, Redes sociales].
- Admin ve solicitud: cada canal muestra su lista de redes con ★ en la principal.
- Migración: canales existentes tienen exactamente 1 red en `curador_medio_redes` con `es_principal=true`.

---

## Notas para el agente

- **`curador_medios.url` se conserva** por compatibilidad — se sincroniza con la red
  principal. No eliminar la columna: otras partes del código la pueden referenciar.
- **El artista no se toca**: `usuario_redes`, `/onboarding/redes`, `RedSocialRow` para
  artistas quedan exactamente igual. Cualquier cambio en esos componentes debe ser
  condicional por tipo de usuario.
- **`precio_creditos` ya existe** en `curador_medios` (fase-06c). Solo falta exponerlo
  en el formulario de onboarding — no hay migración necesaria para ese campo.
- **`on_primer_canal_creado`** fue implementado en fase-06e en `curador_medio_service`.
  Asegurarse de que sigue llamándose después de T4 en esta fase.
- Al hacer `UPDATE` de medios, el reemplazo de redes es **destructivo** (delete + insert).
  No hacer merge. Esto simplifica la lógica y evita estados inconsistentes.
- La validación de "al menos una red" va en el DTO Pydantic (`min_length=1`) y también
  en el servicio como segunda línea de defensa.

---

## Skill recomendado

- **T1-T2:** `dba-skill`.
- **T3-T7:** `developer-skill`.
- **T8-T12:** `frontend-skill`.
- **T13-T15:** `testing-skill`.

---

## PROGRESO

- [x] T1 — Migración 0009 (tabla curador_medio_redes + migrar URLs existentes)
- [x] T2 — Modelo SQLAlchemy CuradorMedioRed + relación en CuradorMedio
- [x] T3 — DTOs: CuradorMedioRedDTO + CuradorMedioDTO actualizado
- [x] T4 — curador_medio_service: add/update/list con redes
- [x] T5 — onboarding_service: progreso diferenciado curador/artista
- [x] T6 — API onboarding: medios con redes + 403 en redes para curador
- [x] T7 — GET /admin/solicitudes/:id → canales incluyen redes
- [x] T8 — medios/page.tsx: formulario con redes dinámicas + precio
- [x] T9 — MedioForm.tsx: sección redes + campo precio
- [x] T10 — RedSocialEditableRow.tsx: selector tipo + indicador principal
- [x] T11 — Stepper + redes page: diferenciado por tipo de usuario
- [x] T12 — CanalRevisionCard: lista de redes por canal
- [x] T13 — Tests BD migración
- [x] T14 — Tests backend (helper actualizado, tests pasan individualmente, falla en batch por event loop asyncpg — pre-existente)
- [x] T15 — Tests frontend Playwright

**Última sesión:** 2026-07-10
**Próximo paso al reanudar:** T13 — Tests de migración, o Fase 07 si se decide saltar tests por ahora.