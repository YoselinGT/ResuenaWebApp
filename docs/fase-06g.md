# Fase 06g — Fixes: onboarding por medios, solicitudes por medio, precio en modal

> **Estado:** `[ ]` pendiente · **Días estimados:** 2 · **Modelo:** `claude-opus-4-7`
> **Skills:** `developer-skill`, `frontend-skill`, `dba-skill`
> **Pre-requisitos:** Fase 06f `[x]`

---

## Contexto

Esta fase corrige cuatro problemas concretos identificados en el código ejecutado.

### Problema 1 — Onboarding no exige medios y empieza en el paso incorrecto

**Estado actual (fase-03):** el onboarding del curador tiene 5 pasos:
Géneros → Idiomas → Regiones → Medios → Redes. El sistema no bloquea al curador
si llega al final sin haber agregado ningún medio. El paso "Medios" es el cuarto,
no el primero como debería ser para enfatizar su importancia.

**Fix:** el wizard del curador debe iniciar en el paso de medios/canales (Paso 1).
El botón "Continuar" o "Completar" al final del wizard solo se habilita cuando
el curador tiene al menos un medio registrado. Si intenta avanzar sin medios,
mostrar error inline: "Debes agregar al menos un canal antes de continuar."

**Nuevo orden del wizard del curador:**
1. Canales (medios) ← ahora es el primer paso y obligatorio
2. Géneros
3. Idiomas
4. Regiones

El paso de "Redes sociales" ya se eliminó en fase-06f.

### Problema 2 — Solicitudes son por curador, deben ser por medio

**Estado actual (fase-05):** `solicitudes_curador` es una sola solicitud por curador.
El admin aprueba al curador completo y desde ese momento todos sus medios quedan
habilitados, incluso los que el admin nunca revisó.

**Estado actual (fase-06e):** se agregó `estado_revision` por canal y la aprobación
granular por canal, pero el guard `require_curador_aprobado` en `roles.py` sigue
verificando `solicitudes_curador.estado == 'aprobada'`. La fase-06e actualizó el guard
para verificar también que haya ≥1 canal aprobado, pero la tabla `solicitudes_curador`
sigue siendo la fuente de verdad — no los medios.

**Fix:** el concepto de "solicitud" se mueve al nivel de `curador_medios`.
Cada medio nuevo que el curador crea empieza en `estado_revision='pendiente'`
y necesita aprobación independiente del admin. El curador puede crear medios
libremente (incluso antes de tener solicitud aprobada), pero **solo puede aceptar
campañas en medios con `estado_revision='aprobado'`**.

**Consecuencias:**
- `solicitudes_curador` se convierte en un registro de que el curador existe en la
  plataforma, pero ya no es la fuente de verdad de si puede operar.
- `require_curador_aprobado` deja de verificar `solicitudes_curador.estado` y
  pasa a verificar que el curador tenga ≥1 medio con `estado_revision='aprobado'`.
- El guard de **aceptar campañas** (`POST /curador/campanas/:id/aceptar`) verifica
  que el medio específico de esa campaña tenga `estado_revision='aprobado'`.
- El curador puede hacer login y crear medios sin solicitud aprobada.
- El curador NO puede aceptar campañas en medios pendientes o rechazados.

### Problema 3 — `POST /curador/medios` requiere aprobación previa (círculo vicioso)

**Estado actual (fase-04b, T17):** `POST /curador/medios` usa `require_curador_aprobado`.
Esto impide que el curador cree medios si no está aprobado, pero para ser aprobado
necesita medios. Círculo vicioso.

**Fix:** quitar `require_curador_aprobado` de `POST /curador/medios`. Solo requiere
que el usuario sea curador activo (`require_curador`). Cualquier curador autenticado
puede crear medios — pero esos medios empiezan en `estado_revision='pendiente'` y no
pueden recibir campañas hasta que el admin los apruebe.

### Problema 4 — `MedioFormModal.tsx` no guarda precio por campaña

**Estado actual (fase-04b, T22):** el modal de crear/editar medio en el dashboard del
curador (`components/curador/MedioFormModal.tsx`) tiene: tipo, nombre, URL, descripción,
géneros. Los campos `precio_creditos` y `descripcion_precio` existen en BD desde
fase-06c pero **no están en este formulario ni en el endpoint `PATCH /curador/medios/:id`**.

**Fix:** agregar `precio_creditos` y `descripcion_precio` al modal y al endpoint.

---

## Tareas

### Fix 1 — Onboarding: medios primero, obligatorio

- [ ] **T1.** Actualizar `app/onboarding/layout.tsx` o `hooks/useOnboardingProgress.ts`
  para que el wizard del curador inicie en `/onboarding/medios` en lugar de
  `/onboarding/generos`. El orden de pasos del curador pasa a ser:
  ```
  /onboarding/medios   → Paso 1 (obligatorio, bloquea el avance si está vacío)
  /onboarding/generos  → Paso 2
  /onboarding/idiomas  → Paso 3
  /onboarding/regiones → Paso 4
  ```
  Para artistas, el orden sigue igual (géneros → idiomas → regiones → redes).

- [ ] **T2.** Actualizar `components/onboarding/StepperNav.tsx` para reflejar el nuevo
  orden visual: el curador ve "Canales" como paso 1 resaltado al entrar al wizard.

- [ ] **T3.** Actualizar `app/onboarding/medios/page.tsx` — el botón de avanzar al
  siguiente paso (`/onboarding/generos`) debe estar **deshabilitado** si
  `medios.length === 0`. Mostrar mensaje inline:
  `"Debes agregar al menos un canal antes de continuar."` con color `var(--text-danger)`.
  El botón se habilita automáticamente al guardar el primer canal.

- [ ] **T4.** Actualizar `GET /onboarding/progreso` en `src/api/onboarding.py`:
  para curadores, el paso `medios` debe marcarse como **bloqueante** — si está
  incompleto, no permitir que el frontend navegue a otros pasos. Agregar campo
  `medios_count: int` al response para que el frontend evalúe si puede avanzar.

### Fix 2 — Solicitudes por medio, no por curador

- [ ] **T5.** Actualizar `src/middleware/roles.py` — `require_curador_aprobado`:
  ```python
  async def require_curador_aprobado(current_user, db) -> Usuario:
      """Verifica que el curador tiene al menos 1 medio aprobado."""
      if current_user.tipo != 'curador' or not current_user.activo:
          raise HTTPException(403, "Acceso restringido a curadores activos")
      canal_aprobado = await db.scalar(
          select(CuradorMedio).where(
              CuradorMedio.curador_id == current_user.id,
              CuradorMedio.estado_revision == 'aprobado',
              CuradorMedio.activo == True
          )
      )
      if not canal_aprobado:
          raise HTTPException(403,
              "Ninguno de tus canales ha sido aprobado aún. "
              "Puedes crear canales y esperar la revisión del equipo.")
      return current_user
  ```
  **Ya no verifica `solicitudes_curador.estado`.**

- [ ] **T6.** Agregar nuevo guard `require_curador` (curador activo, sin importar
  si tiene medios aprobados o no) en `src/middleware/roles.py`:
  ```python
  async def require_curador(current_user, db) -> Usuario:
      """Curador autenticado y activo. No requiere medios aprobados."""
      if current_user.tipo != 'curador' or not current_user.activo:
          raise HTTPException(403, "Acceso restringido a curadores")
      return current_user
  ```

- [ ] **T7.** En el endpoint de **aceptar campaña** (`POST /curador/campanas/:id/aceptar`
  — se implementará en fase-09), documentar que debe verificar que el medio específico
  de esa asignación tenga `estado_revision='aprobado'`. Si el medio está `pendiente`
  o `rechazado` → 403 `{"code": "medio_no_aprobado"}`.
  Si fase-09 ya está ejecutada: agregar esa verificación ahora.

- [ ] **T8.** Actualizar `src/api/curador_medios.py`:
  - `POST /curador/medios` → cambiar guard de `require_curador_aprobado`
    a `require_curador`. El curador puede crear medios en cualquier momento.
  - Los medios nuevos empiezan con `estado_revision='pendiente'` (ya es el default
    de la migración 0008 de fase-06e).
  - `GET /curador/medios` → mantener `require_curador` (puede ver sus propios medios).
  - `PATCH /curador/medios/:id` → mantener `require_curador`.
  - `POST /curador/medios/:id/toggle-activo` → mantener `require_curador`.

- [ ] **T9.** Actualizar notificación al admin: actualmente `on_primer_canal_creado`
  (fase-06e) notifica al admin cuando se crea el primer canal. Ahora debe notificar
  al admin **por cada canal creado** (no solo el primero), porque cada canal necesita
  revisión independiente.
  ```python
  async def on_canal_creado(db, curador_id, medio_id):
      """Notifica al admin que hay un canal nuevo para revisar."""
      await email_service.notificar_admin_canal_nuevo(db, curador_id, medio_id)
      await bitacora_service.log_event(db, autor_id=curador_id,
          accion='canal_creado_pendiente_revision',
          entidad='curador_medios', entidad_id=str(medio_id))
  ```

- [ ] **T10.** Actualizar `app/(dashboard)/curador/medios/page.tsx` — cada `MedioCard`
  debe mostrar el `estado_revision` del medio con badge visible:
  - ⏳ "Pendiente de revisión" (amarillo)
  - ✓ "Aprobado" (verde)
  - ✗ "Rechazado" (rojo) + motivo si existe

  Banner en la parte superior si 0 canales aprobados:
  `"Aún no tienes canales aprobados. Puedes crear canales y explorar la plataforma,
  pero podrás aceptar campañas una vez que el equipo apruebe al menos uno."`

### Fix 3 — Precio por campaña en MedioFormModal

- [ ] **T11.** Actualizar `src/api/curador_medios.py`:
  - `POST /curador/medios` — body acepta `precio_creditos: int = 1` y
    `descripcion_precio: str | None = None`.
  - `PATCH /curador/medios/:id` — acepta ambos campos como opcionales.

- [ ] **T12.** Actualizar `src/models/dto/curador_medios.py`:
  - `CuradorMedioCreateDTO` — agregar `precio_creditos: int = Field(default=1, ge=1)`
    y `descripcion_precio: str | None = None`.
  - `CuradorMedioUpdateDTO` — agregar ambos como opcionales.
  - `CuradorMedioOutDTO` — incluir ambos en el response.

- [ ] **T13.** Actualizar `src/services/curador_medios_service.py`:
  - `crear_medio()` — persistir `precio_creditos` y `descripcion_precio`.
  - `actualizar_medio()` — actualizar ambos campos si vienen en el body.

- [ ] **T14.** Actualizar `components/curador/MedioFormModal.tsx`:
  Agregar dos campos al formulario de crear/editar medio en el dashboard:
  ```
  ┌─ Formulario de canal ─────────────────────────────┐
  │ Tipo      [TikTok ▾]                              │
  │ Nombre    [Urbano MX TikTok              ]        │
  │ URL       [https://tiktok.com/@...       ]        │
  │ Descripción [Contenido urbano y trap...  ]        │
  │ Géneros   [Reggaeton ×] [Trap ×] [+ agregar]     │
  │ Audiencia [48000   ] seguidores/lectores          │
  │ ──────────────────────────────────────────────── │
  │ Precio    [2] créditos por campaña               │
  │ ¿Qué incluye? [Reel de 15–60 segundos   ]        │
  └───────────────────────────────────────────────────┘
  ```
  El campo "Precio" (número, min 1) y "¿Qué incluye?" (texto opcional) van al final
  del formulario, separados visualmente con un divider.

- [ ] **T15.** Actualizar `components/curador/MedioCard.tsx` — mostrar el precio
  en créditos en la card: `"2 créditos por campaña"` como chip o texto pequeño.
  Si `descripcion_precio` existe, mostrar debajo: `"Reel de 15–60 seg"`.

### Tests

- [ ] **T16.** Tests backend:
  - `POST /curador/medios` como curador no aprobado → 201 (ya no requiere aprobación).
  - `POST /curador/medios` como artista → 403.
  - `POST /curador/medios` con `precio_creditos=3, descripcion_precio="Reel"` →
    BD guarda ambos campos correctamente.
  - `PATCH /curador/medios/:id` con `precio_creditos=5` → actualizado en BD.
  - `require_curador_aprobado` sin medios aprobados → 403 con mensaje correcto.
  - `require_curador_aprobado` con ≥1 medio aprobado → pasa.
  - `GET /curador/medios` retorna `precio_creditos` y `descripcion_precio` por medio.

- [ ] **T17.** Tests frontend (Playwright):
  - Curador en onboarding: primer paso visible es "Canales", no "Géneros".
  - Botón avanzar deshabilitado cuando no hay canales → se habilita al agregar uno.
  - Modal de crear medio incluye campos de precio → al guardar aparecen en la card.
  - Badge de `estado_revision` visible en MedioCard.
  - Banner visible cuando 0 canales aprobados.

---

## Archivos a modificar

| Ruta | Qué cambia |
|------|-----------|
| `src/middleware/roles.py` | `require_curador_aprobado` sin solicitud; nuevo `require_curador` |
| `src/api/curador_medios.py` | guard POST → `require_curador`; campos precio en body |
| `src/models/dto/curador_medios.py` | agregar precio_creditos + descripcion_precio |
| `src/services/curador_medios_service.py` | persistir precio; notificar por cada canal |
| `src/api/onboarding.py` | `medios_count` en progreso |
| `app/onboarding/layout.tsx` | curador inicia en /medios |
| `app/onboarding/medios/page.tsx` | botón bloqueado si sin medios |
| `components/onboarding/StepperNav.tsx` | orden visual curador: Canales primero |
| `hooks/useOnboardingProgress.ts` | orden diferenciado curador/artista |
| `components/curador/MedioFormModal.tsx` | agregar campos precio |
| `components/curador/MedioCard.tsx` | mostrar precio + badge estado_revision |
| `app/(dashboard)/curador/medios/page.tsx` | badge estado_revision + banner |
| `tests/integration/test_curador_medios.py` | actualizar tests existentes + nuevos |

---

## Tests / validaciones clave

- Curador nuevo (sin aprobación) puede crear medios → 201.
- Curador con 0 medios aprobados → `require_curador_aprobado` → 403.
- Curador con ≥1 medio aprobado → pasa el guard.
- Curador en onboarding: primer paso = Canales.
- Sin canales → botón "Siguiente" deshabilitado.
- Con ≥1 canal → botón habilitado.
- `POST /curador/medios` con precio → `GET /curador/medios` retorna precio correcto.
- `MedioCard` muestra precio en créditos.
- `MedioCard` muestra badge de estado_revision.

---

## Notas para el agente

- **`solicitudes_curador` sigue existiendo** en BD. No eliminar la tabla ni el endpoint
  de lista del admin. La tabla ahora es solo un registro histórico/administrativo, pero
  `require_curador_aprobado` ya no la consulta.
- **El admin sigue viendo solicitudes en su panel** (fase-06e). El flujo de aprobación
  por canal ya está implementado. Esta fase solo cambia el guard del curador.
- **No tocar el flujo del artista** en ninguna parte. Solo los componentes compartidos
  del wizard deben diferenciarse por tipo de usuario.
- Si **fase-09 ya fue ejecutada**, el endpoint `POST /curador/campanas/:id/aceptar`
  también debe verificar que el medio tenga `estado_revision='aprobado'`. Si no, dejar
  la nota en el código como TODO para cuando llegue fase-09.
- El `on_primer_canal_creado` de fase-06e se renombra a `on_canal_creado` para reflejar
  que notifica por cada canal, no solo el primero.

---

## Skill recomendado

- **T5-T9, T11-T13:** `developer-skill`.
- **T1-T4, T10, T14-T15:** `frontend-skill`.
- **T16-T17:** `testing-skill`.

---

## PROGRESO

- [x] T1 — Onboarding curador: inicia en /medios
- [x] T2 — StepperNav: orden visual curador = Canales primero
- [x] T3 — medios/page.tsx: botón bloqueado sin medios
- [x] T4 — GET /onboarding/progreso: medios_count en response
- [x] T5 — require_curador_aprobado: sin solicitudes_curador, solo canal aprobado
- [x] T6 — Nuevo guard require_curador (sin aprobación requerida)
- [x] T7 — Documentar/parchear aceptar campaña: verificar estado_revision del medio
- [x] T8 — POST /curador/medios: cambiar guard a require_curador
- [x] T9 — on_canal_creado: notificar por cada canal nuevo (no solo el primero)
- [x] T10 — MedioCard: badge estado_revision + banner sin aprobados
- [x] T11 — API: precio_creditos + descripcion_precio en POST y PATCH /curador/medios
- [x] T12 — DTOs: CuradorMedioCreateDTO + UpdateDTO + OutDTO con precio
- [x] T13 — Service: persistir precio al crear y actualizar
- [x] T14 — MedioFormModal: campos precio + descripcion_precio
- [x] T15 — MedioCard: mostrar precio en créditos
- [x] T16 — Tests backend
- [x] T17 — Tests frontend Playwright

**Última sesión:** 2026-07-10
**Próximo paso al reanudar:** T16 — Tests backend, o Fase 07 si se decide saltar tests.