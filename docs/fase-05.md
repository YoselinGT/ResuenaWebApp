# Fase 05 — Admin — Aprobación de curadores + RBAC

> **Estado:** `[ ]` pendiente · **Días estimados:** 4 · **Modelo:** `claude-opus-4-7`
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

- [ ] **T1.** Middleware `require_admin` en `src/middleware/roles.py`: verifica `user.perfil_id == 1`.
- [ ] **T2.** Middleware `require_artista`: verifica `perfil_id == 2` y `activo`.
- [ ] **T3.** Middleware `require_curador_aprobado`: verifica `perfil_id == 3`, `activo`, y que `solicitudes_curador.estado == 'aprobada'`.
- [ ] **T4.** Endpoint `GET /admin/solicitudes` (paginado): lista solicitudes de curadores filtrable por estado (pendiente/aprobada/rechazada), tipo_curador, fecha. Solo Admin.
- [ ] **T5.** Endpoint `GET /admin/solicitudes/:id`: detalle completo de la solicitud.
- [ ] **T6.** Endpoint `POST /admin/solicitudes/:id/aprobar`: cambia estado a `aprobada`, registra `revisor_id`, envía email de bienvenida al curador. Bitácora.
- [ ] **T7.** Endpoint `POST /admin/solicitudes/:id/rechazar`: body `{motivo}`, cambia estado a `rechazada`, envía email con motivo. Bitácora.
- [ ] **T8.** Endpoint `GET /admin/usuarios`: listado paginado de todos los usuarios con filtros (tipo, activo, fecha).
- [ ] **T9.** Endpoint `PATCH /admin/usuarios/:id`: editar nombre, estado activo. No edita correo ni contraseña. Bloquea admin ID 1.
- [ ] **T10.** Endpoint `POST /admin/usuarios/:id/toggle-status`: activa/desactiva usuario.
- [ ] **T11.** Vista `(dashboard)/admin/solicitudes/page.tsx`: tabla con filtros, badge de estado, botones Aprobar/Rechazar con modal de confirmación (rechazo pide motivo).
- [ ] **T12.** Vista `(dashboard)/admin/solicitudes/[id]/page.tsx`: detalle con portfolio, redes sociales, tipo. Botones de acción.
- [ ] **T13.** Vista `(dashboard)/admin/usuarios/page.tsx`: tabla con acciones inline.
- [ ] **T14.** Redireccionamiento guard en frontend: artistas que intentan acceder a `/admin/*` → 403; curadores no aprobados que intentan acceder a funcionalidades → pantalla de "en revisión".
- [ ] **T15.** Tests: aprobar curador → puede recibir campañas; rechazar → no puede hacer login hasta re-aplicar; admin no puede editarse a sí mismo campos críticos.

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

- [ ] T1 — require_admin middleware
- [ ] T2 — require_artista middleware
- [ ] T3 — require_curador_aprobado middleware
- [ ] T4 — GET /admin/solicitudes
- [ ] T5 — GET /admin/solicitudes/:id
- [ ] T6 — POST aprobar
- [ ] T7 — POST rechazar
- [ ] T8 — GET /admin/usuarios
- [ ] T9 — PATCH /admin/usuarios/:id
- [ ] T10 — Toggle status
- [ ] T11 — Vista solicitudes (lista)
- [ ] T12 — Vista solicitudes (detalle)
- [ ] T13 — Vista usuarios admin
- [ ] T14 — Guards frontend
- [ ] T15 — Tests

**Última sesión:** —
**Próximo paso al reanudar:** T1 — implementar `require_admin`, `require_artista`, `require_curador_aprobado` en `src/middleware/roles.py`.