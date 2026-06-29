# Fase 04b — Sellos discográficos + Gestión de medios del curador

> **Estado:** `[x]` completada · **Días estimados:** 3 · **Modelo:** `claude-sonnet-4-6`
> **Skills:** `developer-skill`, `frontend-skill`
> **Pre-requisitos:** Fase 03 `[x]`, Fase 04 `[x]`

---

## Contexto

Esta fase implementa dos módulos de gestión que completan los perfiles de usuario:

### 1. Sellos discográficos

Un sello es una entidad que agrupa artistas bajo una misma marca. En Resuena:
- Cualquier artista puede **crear un sello** y convertirse en su owner.
- El sello puede **invitar artistas** (que ya existen en la plataforma) con roles distintos: `owner`, `manager`, `artista`.
- Un artista puede **pertenecer a un solo sello activo** a la vez (o ser independiente).
- El sello puede **lanzar campañas en nombre de un artista** — la campaña registra tanto el `artista_id` como el `sello_id`.
- El wallet de créditos sigue siendo del artista, no del sello. El sello no tiene wallet propio.
- Los managers del sello pueden crear campañas en nombre de artistas del sello, pero los créditos se deducen del wallet del artista correspondiente.

Casos de uso:
- Artista independiente que forma su propio sello para manejar a otros artistas que firma.
- Manager que opera campañas para varios artistas bajo un mismo sello.
- Artista que se une al sello de otro para que lo gestionen.

### 2. Gestión de medios del curador (post-onboarding)

Durante el onboarding (Fase 03) el curador registra sus medios iniciales. Esta fase añade la gestión completa post-onboarding:
- Agregar nuevos medios después del registro.
- Editar información de un medio existente (nombre, URL, géneros, descripción).
- Activar / desactivar un medio sin eliminarlo (si está en una campaña activa, no se puede desactivar).
- Ver estadísticas básicas de cada medio (campañas recibidas, aceptadas, entregadas).

Un curador puede tener cualquier número de medios. Cada medio es independiente y puede recibir campañas de forma separada.

---

## Tareas

### Sellos discográficos — Backend

- [x] **T1.** Endpoint `POST /sellos` — crea un sello. Solo artistas. Body: `{nombre, descripcion?, logo? (multipart), website?}`. El artista creador queda como `owner` en `sello_artistas`. Un artista no puede crear un segundo sello si ya es owner de uno activo.
- [x] **T2.** Endpoint `GET /sellos/mio` — retorna el sello del artista en sesión (si pertenece a uno) con lista de artistas miembros y sus roles.
- [x] **T3.** Endpoint `PATCH /sellos/:id` — edita nombre, descripción, website, logo. Solo owner o manager.
- [x] **T4.** Endpoint `POST /sellos/:id/invitar` — body `{correo, rol: manager|artista}`. Busca al usuario por correo, valida que es artista activo y no pertenece a otro sello. Envía email de invitación con token.
- [x] **T5.** Endpoint `POST /sellos/aceptar-invitacion/{token}` — el artista invitado acepta. Crea la fila en `sello_artistas`.
- [x] **T6.** Endpoint `DELETE /sellos/:id/miembros/:artista_id` — elimina a un artista del sello. Solo owner. No puede eliminarse a sí mismo (tendría que transferir ownership primero).
- [x] **T7.** Endpoint `POST /sellos/:id/transferir-ownership` — body `{nuevo_owner_id}`. Cambia el rol del owner actual a `manager` y el del nuevo a `owner`.
- [x] **T8.** Endpoint `POST /sellos/:id/salir` — el artista sale del sello por voluntad propia. No aplica si es el único owner.
- [x] **T9.** Endpoint `GET /sellos/:id/artistas` — lista artistas del sello con su rol y estado.
- [x] **T10.** Template de email `invitacion_sello.html` — email con el nombre del sello, quien invita, rol asignado y botón para aceptar.

### Sellos discográficos — Frontend

- [x] **T11.** Vista `(dashboard)/artista/sello/page.tsx` — panel de gestión del sello. Si no tiene sello: CTA "Crear mi sello" + opción "Unirme a un sello" (si tiene invitación pendiente). Si tiene sello: ver miembros, roles, botón invitar, estadísticas básicas (campañas lanzadas como sello).
- [x] **T12.** Modal `CrearSelloModal.tsx` — formulario: nombre, descripción, logo (upload), website. Inline en la misma página.
- [x] **T13.** Componente `MiembrosDelSello.tsx` — tabla con avatar, nombre, rol badge, fecha de ingreso, acción "Eliminar" (solo para owner). Rol badge con colores: owner=morado, manager=azul, artista=gris.
- [x] **T14.** Vista `(dashboard)/artista/sello/invitacion/[token]/page.tsx` — server component que muestra la invitación (nombre del sello, quien invita, rol) con botones "Aceptar" / "Rechazar".
- [x] **T15.** Sección en `mi-perfil` para artistas: badge "Miembro de [Nombre Sello]" con link al panel. Si es independiente: link "Crear o unirse a un sello".

### Gestión de medios del curador — Backend

- [x] **T16.** Endpoint `GET /curador/medios` — lista todos los medios del curador en sesión con stats: campañas recibidas, aceptadas, entregadas, tasa de aceptación.
- [x] **T17.** Endpoint `POST /curador/medios` — agrega un nuevo medio post-onboarding. Body: `{nombre, tipo, url, descripcion?, generos_especializados: [id]}`. Guard: `require_curador_aprobado`.
- [x] **T18.** Endpoint `PATCH /curador/medios/:id` — edita nombre, URL, descripción, géneros. Valida que el medio pertenece al curador en sesión.
- [x] **T19.** Endpoint `POST /curador/medios/:id/toggle-activo` — activa o desactiva el medio. Si hay campañas en estado `pendiente` o `aceptada` vinculadas a ese medio → 409 con mensaje claro "Tienes campañas activas en este medio".
- [x] **T20.** Endpoint `GET /curador/medios/:id/stats` — stats detalladas de un medio: campañas por mes (últimos 6 meses), géneros más frecuentes recibidos, tiempo promedio de respuesta.

### Gestión de medios del curador — Frontend

- [x] **T21.** Vista `(dashboard)/curador/medios/page.tsx` — panel de medios. Grid de cards, una por medio. Cada card muestra: tipo (ícono), nombre, URL, géneros especializados (chips), stats compactas (recibidas/aceptadas), toggle activo/inactivo. Botón "Añadir medio" arriba a la derecha.
- [x] **T22.** Modal `MedioFormModal.tsx` — formulario para crear o editar un medio: tipo (selector con íconos), nombre, URL, descripción, géneros especializados (multi-select chips). Reutilizable para crear y editar.
- [x] **T23.** Componente `MedioCard.tsx` — card individual del medio con diseño consistente al sistema de diseño. Toggle de estado con confirmación si hay campañas activas.
- [x] **T24.** Sección en `mi-perfil` para curadores: lista compacta de medios con link al panel completo.

### Tests

- [x] **T25.** Tests sellos: crear sello → owner correcto; invitar artista ya en otro sello → 409; artista acepta invitación → fila en `sello_artistas`; manager crea campaña en nombre de artista del sello → `campanas.sello_id` no nulo; owner no puede eliminarse a sí mismo.
- [x] **T26.** Tests medios: curador añade medio post-onboarding → fila en `curador_medios`; toggle de medio con campaña activa → 409; artista intenta `POST /curador/medios` → 403; stats de medio recién creado → todos los contadores en 0.

---

## Archivos a crear

| Ruta | |
|------|-|
| `src/api/sellos.py` | |
| `src/api/curador_medios.py` | |
| `src/services/sello_service.py` | |
| `src/services/curador_medios_service.py` | |
| `src/models/dto/sellos.py` | |
| `src/models/dto/curador_medios.py` | |
| `src/infra/email_templates/invitacion_sello.html` | |
| `app/(dashboard)/artista/sello/page.tsx` | |
| `app/(dashboard)/artista/sello/invitacion/[token]/page.tsx` | |
| `app/(dashboard)/curador/medios/page.tsx` | |
| `components/sellos/CrearSelloModal.tsx` | |
| `components/sellos/MiembrosDelSello.tsx` | |
| `components/curador/MedioCard.tsx` | |
| `components/curador/MedioFormModal.tsx` | |
| `tests/integration/test_sellos.py` | |
| `tests/integration/test_curador_medios.py` | |

---

## Tests / validaciones

- Artista sin sello crea uno → aparece como owner en `sello_artistas`.
- Artista que ya es owner intenta crear otro sello → 409.
- Invitar artista que pertenece a otro sello → 409 con mensaje claro.
- Manager del sello crea campaña con `artista_id` de un artista del sello → acepta; con artista de otro sello → 403.
- Curador aprobado añade 3 medios nuevos post-onboarding → 3 filas en `curador_medios`.
- Toggle inactivo en medio con campaña en estado `pendiente` → 409.
- Toggle inactivo en medio sin campañas activas → medio desactivado, no aparece en `GET /medios/disponibles`.
- Stats de medio: después de 2 campañas aceptadas y 1 entregada → `{recibidas: 3, aceptadas: 2, entregadas: 1}`.

---

## Notas de diseño

**Por qué el wallet no es del sello:** simplifica el modelo financiero. Los créditos siempre pertenecen al artista; el sello es solo una capa de gestión y marca. Esto evita tener que manejar transferencias internas entre sello y artista.

**Por qué un artista solo puede pertenecer a un sello activo:** evita conflictos de permisos y simplifica la UI. Si un artista quiere cambiar de sello, primero debe salir del actual.

**Por qué no eliminar medios, solo desactivar:** preserva el historial de campañas pasadas. Un medio desactivado no aparece en búsquedas ni acepta nuevas campañas, pero sus campañas completadas siguen accesibles.

---

## Skill recomendado por tarea

- **T1-T10, T16-T20:** `developer-skill`.
- **T11-T15, T21-T24:** `frontend-skill`.
- **T25-T26:** `testing-skill`.

---

## PROGRESO

- [x] T1 — POST /sellos (multipart + logo; owner en sello_artistas; 409 si ya pertenece/nombre dup)
- [x] T2 — GET /sellos/mio (sello + miembros con rol/foto; null si no pertenece)
- [x] T3 — PATCH /sellos/:id (guard owner/manager vía _require_rol; bitácora diff)
- [x] T4 — POST /sellos/:id/invitar (tabla invitaciones_sello 0005 + email; validaciones 404/422/409/403)
- [x] T5 — POST /sellos/aceptar-invitacion/{token} (SELECT FOR UPDATE; crea/reactiva membresía; 403/400/410/409)
- [x] T6 — DELETE miembro del sello (solo owner; self→409; soft-delete; 403/404)
- [x] T7 — POST transferir ownership (owner→manager / nuevo→owner; 403/404/422)
- [x] T8 — POST salir del sello (soft-delete; único owner→409; no-miembro→404)
- [x] T9 — GET artistas del sello (activos+inactivos con estado; requiere ser miembro; 403/401/404)
- [x] T10 — Template email invitación (invitacion_sello.html + email_service.send_invitacion_sello)
- [x] T11 — Vista artista/sello (panel: empty-state crear / sello+miembros+invitar+salir; link en sidebar)
- [x] T12 — CrearSelloModal (multipart vía api.upload)
- [x] T13 — MiembrosDelSello (rol badges; owner: transferir/eliminar)
- [x] T14 — Vista aceptar/rechazar invitación (+ GET /sellos/invitacion/{token} y POST rechazar-invitacion)
- [x] T15 — Sección sello en mi-perfil (SelloPerfilCard: badge miembro / CTA crear)
- [x] T16 — GET /curador/medios (con stats: recibidas/aceptadas/entregadas/tasa)
- [x] T17 — POST /curador/medios (require_curador_aprobado; 403 no-aprobado/artista)
- [x] T18 — PATCH /curador/medios/:id (edición parcial + géneros)
- [x] T19 — Toggle activo/inactivo (409 si campañas pendiente/aceptada)
- [x] T20 — GET /curador/medios/:id/stats (stats + por_mes 6 meses)
- [x] T21 — Vista curador/medios (grid MedioCard + añadir; link sidebar)
- [x] T22 — MedioFormModal (crear/editar; reusa MedioForm)
- [x] T23 — MedioCard (tipo+ícono, chips géneros, stats, toggle con 409)
- [x] T24 — Sección medios en mi-perfil (MediosPerfilCard)
- [x] T25 — Tests sellos (test_sellos.py, 7 tests)
- [x] T26 — Tests curador medios (test_curador_medios.py, 6 tests)

**Última sesión:** 2026-06-29 — Rama `fase-04b` (desde `fase-04`). T1 completado:
`src/utils/images.py` (`process_jpeg_square` reusable: libmagic JPEG + Pillow center-crop; refactor
de `user_service` para usarlo — suite sigue 43 passed), `src/models/dto/sellos.py` (`SelloOutDTO`),
`src/services/sello_service.py` (`create_sello`: invariante 1 sello activo/artista → 409, nombre
único → 409, nombre inválido → 422; owner en `sello_artistas`; logo opcional 256×256 →
`sellos-logo/<id>.jpg` vía StorageService; bitácora "Creación de sello"), `src/api/sellos.py`
(`POST /sellos` multipart Form+File, guard `require_tipo(artista)`), router registrado. Validado:
artista→201 (rol owner); 2º sello→409; curador→403; sin sesión→401; con logo→logo_url presigned +
owner activo en sello_artistas + logo_path=clave; nombre duplicado→409. ruff limpio.

T2 completado: `MiembroDTO` + `SelloDetalleDTO` (extiende SelloOutDTO con `miembros`),
`sello_service.get_mi_sello` (membresía activa → sello + miembros activos con rol/foto presigned,
ordenados owner→manager→artista), `GET /sellos/mio` (`require_artista`, `response_model=...|None`
→ devuelve `null` 200 si no pertenece). Validado: sin sello→200 null; con sello→rol owner +
miembros; curador→403. ruff limpio. NOTA: `sello_artistas` no tiene timestamp → no hay "fecha de
ingreso" (el texto de T13 la menciona; omitida o requeriría migración).

T3 completado: helpers `_membership` y `_require_rol(allowed)` (guard de rol dentro del sello →403),
`_build_detalle` reutilizable (get_mi_sello refactorizado), `sello_service.update_sello` (nombre/
descripcion/website/logo; nombre único excl. self →409, inválido →422; logo vía process_jpeg_square;
bitácora "Actualización de sello" con diff; no-op sin cambios), `PATCH /sellos/{id}` multipart
(declarado tras `/mio`). Validado: owner edita→200; no-miembro→403; miembro rol=artista→403;
manager→200; sello inexistente→404. ruff limpio. (Roles manager/artista insertados por SQL para el
test; las invitaciones llegan en T4/T5.)

T4 + T10 completados: enum `EstadoInvitacionSello`, modelo `invitaciones_sello.py` (token único,
estado, expires_at 7d, consumed_at), **migración 0005** (OJO: el ENUM de columna debe ser
`create_type=False` para que `create_table` no lo cree dos veces; el enum se crea explícito con
`checkfirst`), template `invitacion_sello.html` + `send_invitacion_sello`, DTOs `InvitarBody`
(rol Literal manager|artista) + `InvitacionOutDTO`, `sello_service.invitar` (guard owner/manager;
artista activo→422, no pertenece a otro sello→409, no auto-invitar, sin pendiente duplicada→409;
token `secrets.token_urlsafe`; email link `{frontend_url}/artista/sello/invitacion/{token}`;
bitácora), `POST /sellos/{id}/invitar`. Validado: 201+email, 409 pendiente, 404, 422 curador,
422 rol owner, 403 no editor, 409 ya pertenece. head alembic = 0005. ruff limpio.

T5 completado: `sello_service.aceptar_invitacion` (token con `SELECT FOR UPDATE`; valida
pendiente/no-consumida→400, no expirada→410, invitado==sesión→403, revalida invariante→409;
crea o **reactiva** la fila en `sello_artistas` con el rol de la invitación; marca `aceptada` +
`consumed_at`; bitácora), `POST /sellos/aceptar-invitacion/{token}` (declarado antes de las rutas
`/{sello_id}`). Validado: no-invitado→403; aceptar→200 (miembros owner+manager); re-aceptar→400;
token inválido→400; expirado→410; accept-time ya-pertenece→409; `/mio` refleja la membresía.
ruff limpio.

T6 completado: `sello_service.eliminar_miembro` (guard `_SOLO_OWNER`; no auto-eliminar→409;
soft-delete `activo=False`; bitácora "Eliminación de miembro de sello"), `DELETE
/sellos/{sello_id}/miembros/{artista_id}` (204). Validado: self→409; manager→403; owner elimina
miembro→204 (queda libre, /mio=null); eliminar de nuevo→404. Suite 43 passed.
OJO/LECCIÓN: un endpoint 204 NO debe anotar `-> None` (FastAPI lo trata como response_model NoneType
y falla en import con "Status code 204 must not have a response body" → tumbó la api). Omitir la
anotación de retorno en endpoints 204 (como los DELETE de onboarding).

T7 completado: DTO `TransferOwnershipBody` (nuevo_owner_id UUID), `sello_service.transferir_ownership`
(solo owner; a sí mismo→422; nuevo debe ser miembro activo→404; owner→manager y nuevo→owner en una
transacción; bitácora), `POST /sellos/{id}/transferir-ownership`. Validado: self→422; A transfiere
a B→200 (A manager, B owner vía /mio); A ya manager→403; no-miembro→404. ruff limpio.

T8 completado: `sello_service.salir_del_sello` (miembro sale; soft-delete; si es owner cuenta los
owners activos y bloquea con 409 si es el único; no-miembro→404; bitácora "Salida de sello"),
`POST /sellos/{id}/salir` (204). Validado: único owner→409; manager sale→204 (queda libre, sello a
1 miembro); salir de nuevo→404. ruff limpio.

T9 completado: helper `_to_miembro` (reutilizado por `_build_detalle`), `sello_service.listar_artistas`
(requiere ser miembro→403; lista activos **e inactivos** con rol/estado/foto; activos primero luego
por jerarquía de rol), `GET /sellos/{id}/artistas`. Validado: owner ve `[(owner,True),(artista,False)]`
tras eliminar a un miembro; no-miembro→403; sin sesión→401. **Backend de sellos COMPLETO (T1-T10).**
Suite 43 passed. ruff limpio.

T16-T20 completados: `dto/curador_medios.py`, `services/curador_medios_service.py`
(stats por medio recibidas/aceptadas/entregadas/tasa desde `campana_medios`; list con stats; crear;
editar parcial; toggle con bloqueo 409 si hay campañas pendiente/aceptada; stats detalladas + por_mes
6 meses — generos_frecuentes/tiempo_respuesta quedan para Fase 08), `api/curador_medios.py` con guard
`require_curador_aprobado` (POST exige solicitud aprobada). Validado todo (no-aprobado→403, artista→403,
aprobado→201, list con stats, edit, toggle 200/200/409, stats con por_mes). **BACKEND DE FASE 04b
COMPLETO (T1-T10 sellos + T16-T20 medios).** Suite 43 passed, ruff limpio.
NOTA: aprobar curador en dev requiere `update solicitudes_curador set estado='aprobada'` (la
aprobación por admin llega en Fase 05). LECCIÓN zsh: `UID`/`GID`/`EUID`/`EGID` son variables
especiales de solo-asignación-privilegiada — no usarlas como vars en scripts de prueba.

T11-T13 completados: `components/sellos/CrearSelloModal.tsx` (crear sello multipart vía `api.upload`),
`components/sellos/MiembrosDelSello.tsx` (tabla con avatar + rol badges owner/manager/artista; owner
puede transferir ownership 👑 y eliminar 🗑), `app/(dashboard)/artista/sello/page.tsx` (panel:
empty-state con "Crear mi sello" / sello con header+invitar(owner/manager)+miembros+salir; guard
redirige curador a /home). Link "Mi sello" agregado al sidebar de artista. Validado: guard 307; con
sesión 200; sidebar OK; tsc limpio. (Las acciones consumen endpoints ya probados a nivel API.)
NOTA: "Unirme a un sello" desde el panel no se implementó como acción (no hay GET de invitaciones
pendientes del usuario); la aceptación es vía el enlace del email → vista T14.

T14 completado (opción GET+Rechazar): backend `GET /sellos/invitacion/{token}` (lee sin consumir;
estado `expirada` si venció) + `POST /sellos/rechazar-invitacion/{token}`, DTO `InvitacionDetalleDTO`,
vista `app/(dashboard)/artista/sello/invitacion/[token]/page.tsx` (preview sello/invitador/rol +
Aceptar/Rechazar; **client component**, no server, por el fetch con cookie + interacción). Validado:
preview pendiente, token inválido→400, rechazar→204→estado rechazada, aceptar-rechazada→400, página→200.

T15 completado: `components/sellos/SelloPerfilCard.tsx` (badge "Miembro de [sello]" + rol con link
al panel, o CTA "Crear o unirse a un sello") embebido en mi-perfil para artistas. Validado: /mi-perfil
200, /sellos/mio null→CTA. **FRONTEND DE SELLOS COMPLETO (T11-T15).** tsc limpio, suite 43 passed.

**Próximo paso al reanudar:** **FASE 04b COMPLETA (26/26).** Backend (sellos T1-T10, medios
T16-T20) + frontend (sellos T11-T15, medios T21-T24) + tests T25-T26. Suite 56 passed; ruff +
tsc limpios. Migraciones head = 0005. Pendiente solo el **cierre de sesión** (PLAN.md/CHECKPOINT,
CLAUDE.md fase activa, commit en rama `fase-04b`) y decidir la siguiente fase (05 — Admin:
Aprobación de curadores + RBAC). DEUDA anotada: stats de medios `generos_frecuentes`/
`tiempo_respuesta` y "campañas lanzadas como sello" dependen del esquema de campañas (Fase 08).
