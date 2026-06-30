# Fase 05 — Admin — Aprobación de curadores + RBAC

> **Estado:** `[x]` completada · **Días estimados:** 4 · **Modelo:** `claude-opus-4-7`
> **Skills:** `security-skill`, `developer-skill`, `frontend-skill`
> **Pre-requisitos:** Fase 04 `[x]`

---

## Contexto

Esta fase implementa el panel de administración y el flujo de aprobación de curadores, que es el corazón del control de calidad de Resuena.

Flujo de aprobación:
1. Curador se registra y envía solicitud con portfolio y redes sociales.
2. Admin recibe notificación por email (Fase 03 ya lo envía).
3. Admin revisa la solicitud en el panel.
4. Admin aprueba (→ email de bienvenida al curador, puede recibir campañas) o rechaza (→ email con motivo, puede re-aplicar).

RBAC simplificado (Resuena no requiere el RBAC granular del Portal Vendedores):
- **Admin (perfil_id=1):** acceso total al panel admin.
- **Artista (perfil_id=2):** accede solo a su dashboard de artista.
- **Curador (perfil_id=3):** accede solo a su dashboard de curador, y solo si está aprobado.

Middleware `require_admin`, `require_artista`, `require_curador_aprobado` como guards.

---

## Tareas

- [x] **T1.** Middleware `require_admin` en `src/middleware/roles.py`: verifica `user.perfil_id == 1`.
- [x] **T2.** Middleware `require_artista`: verifica `perfil_id == 2` y `activo`.
- [x] **T3.** Middleware `require_curador_aprobado`: verifica `perfil_id == 3`, `activo`, y que `solicitudes_curador.estado == 'aprobada'`.
- [x] **T4.** Endpoint `GET /admin/solicitudes` (paginado): lista solicitudes de curadores filtrable por estado (pendiente/aprobada/rechazada), tipo_curador, fecha. Solo Admin.
- [x] **T5.** Endpoint `GET /admin/solicitudes/:id`: detalle completo de la solicitud.
- [x] **T6.** Endpoint `POST /admin/solicitudes/:id/aprobar`: cambia estado a `aprobada`, registra `revisor_id`, envía email de bienvenida al curador. Bitácora.
- [x] **T7.** Endpoint `POST /admin/solicitudes/:id/rechazar`: body `{motivo}`, cambia estado a `rechazada`, envía email con motivo. Bitácora.
- [x] **T8.** Endpoint `GET /admin/usuarios`: listado paginado de todos los usuarios con filtros (tipo, activo, fecha).
- [x] **T9.** Endpoint `PATCH /admin/usuarios/:id`: editar nombre, estado activo. No edita correo ni contraseña. Bloquea admin ID 1.
- [x] **T10.** Endpoint `POST /admin/usuarios/:id/toggle-status`: activa/desactiva usuario.
- [x] **T11.** Vista `(dashboard)/admin/solicitudes/page.tsx`: tabla con filtros, badge de estado, botones Aprobar/Rechazar con modal de confirmación (rechazo pide motivo).
- [x] **T12.** Vista `(dashboard)/admin/solicitudes/[id]/page.tsx`: detalle con portfolio, redes sociales, tipo. Botones de acción.
- [x] **T13.** Vista `(dashboard)/admin/usuarios/page.tsx`: tabla con acciones inline.
- [x] **T14.** Redireccionamiento guard en frontend: artistas que intentan acceder a `/admin/*` → 403; curadores no aprobados que intentan acceder a funcionalidades → pantalla de "en revisión".
- [x] **T15.** Tests: aprobar curador → puede recibir campañas; rechazar → no puede hacer login hasta re-aplicar; admin no puede editarse a sí mismo campos críticos.

---



## Archivos a crear

| Ruta | |
|------|-|
| `src/middleware/roles.py` | guards require_admin, require_artista, require_curador_aprobado |
| `src/api/admin_solicitudes.py` | |
| `src/api/admin_usuarios.py` | |
| `src/services/admin_service.py` | |
| `app/(dashboard)/admin/solicitudes/page.tsx` | |
| `app/(dashboard)/admin/solicitudes/[id]/page.tsx` | |
| `app/(dashboard)/admin/usuarios/page.tsx` | |
| `components/admin/SolicitudCard.tsx` | |
| `components/admin/RechazarModal.tsx` | |
| `tests/integration/test_admin_solicitudes.py` | |
| `tests/integration/test_roles.py` | |

---

## Tests / validaciones

- `POST /admin/solicitudes/:id/aprobar` sin cookie admin → 403.
- Curador recién aprobado → puede llamar a `GET /campanas/disponibles` sin error 403.
- Curador rechazado intenta login → sesión creada pero al acceder al dashboard ve pantalla "pendiente".
- `PATCH /admin/usuarios/1` (admin) → 403 protegido.
- Bitácora contiene `aprobacion_curador` y `rechazo_curador` con detalle.

---

## Skill recomendado por tarea

- **T1-T3:** `security-skill`.
- **T4-T10:** `developer-skill`.
- **T11-T14:** `frontend-skill`.
- **T15:** `testing-skill`.

---

## PROGRESO

- [x] T1 — require_admin middleware
- [x] T2 — require_artista middleware (+ activo)
- [x] T3 — require_curador_aprobado middleware (centralizado; curador_medios.py refactor)
- [x] T4 — GET /admin/solicitudes (paginado + filtros estado/tipo/fecha; require_admin)
- [x] T5 — GET /admin/solicitudes/:id (detalle + redes; 404/403)
- [x] T6 — POST aprobar (estado→aprobada, revisor_id, email, bitácora aprobacion_curador; 409 si ya aprobada)
- [x] T7 — POST rechazar (motivo→notas_revision, email, bitácora rechazo_curador; login rechazado→403; 409 ya rechazada)
- [x] T8 — GET /admin/usuarios (paginado + filtros tipo/activo/fecha)
- [x] T9 — PATCH /admin/usuarios/:id (nombre/activo; ignora correo/pass; admin→403; bitácora diff)
- [x] T10 — POST toggle-status (invierte activo; protege admin; bitácora)
- [x] T11 — Vista solicitudes (lista, filtros, aprobar/rechazar)
- [x] T12 — Vista solicitudes (detalle: SolicitudCard + acciones)
- [x] T13 — Vista usuarios admin (filtros tipo/activo + toggle inline)
- [x] T14 — Guards frontend (es_admin en /auth/me+contexto+sidebar; admin pages→/home; curador no aprobado→en revisión)
- [x] T15 — Tests (test_roles.py 4 + test_admin_solicitudes.py 6)

**Última sesión:** 2026-06-29 — Rama `fase-05` (desde main). T1-T3: `src/middleware/roles.py` con
`require_admin` (perfil 1), `require_artista` (perfil 2 + activo en BD), `require_curador_aprobado`
(perfil 3 + activo + solicitud aprobada). Se centralizó el guard que estaba duplicado en
`src/api/curador_medios.py` (ahora importa de roles). Validado: ruff limpio; suite 56 passed
(tests de medios cubren 403 no-aprobado/artista + 201 aprobado vía el guard movido). require_admin/
require_artista aún no cableados a endpoints (llegan en T4+/sellos).
**Próximo paso al reanudar:** **T11-T14** (frontend admin). Endpoints listos: GET /admin/solicitudes
(filtros estado/tipo/desde/hasta + page/page_size), GET /admin/solicitudes/{id}, POST .../aprobar,
POST .../rechazar (body {motivo}), GET /admin/usuarios (tipo/activo/desde/hasta), PATCH
/admin/usuarios/{id} ({nombre_completo?,activo?}), POST /admin/usuarios/{id}/toggle-status.
- T11 `app/(dashboard)/admin/solicitudes/page.tsx` (tabla + filtros + badges + aprobar/rechazar con
  RechazarModal) usando SolicitudCard/RechazarModal.
- T12 `app/(dashboard)/admin/solicitudes/[id]/page.tsx` (detalle: portfolio, redes, tipo + acciones).
- T13 `app/(dashboard)/admin/usuarios/page.tsx` (tabla + acciones inline toggle/editar).
- T14 guards frontend: items de sidebar admin (perfil 1) + páginas admin que redirigen no-admin a
  /home; curador no aprobado → pantalla "en revisión". DashboardUser hoy NO trae perfil_id —
  agregarlo al JWT/me o derivar admin de tipo: OJO el contexto cliente usa tipo (artista/curador);
  admin no es un `tipo`. Habrá que exponer perfil_id/es_admin en /auth/me + DashboardProvider.
Luego T15 (tests admin + roles). OJO dev: crear admin = promover perfil_id=1 vía SQL + re-login.
Skill: frontend-skill (T11-T14), testing-skill (T15).