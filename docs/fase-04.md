# Fase 04 — Layout Dashboard + Perfiles de usuario

> **Estado:** `[x]` completada · **Días estimados:** 3 · **Modelo:** `claude-sonnet-4-6`
> **Skills:** `frontend-skill`, `developer-skill`
> **Pre-requisitos:** Fase 03 `[x]`

---

## Contexto

Esta fase construye el **shell visual** de la aplicación protegida y las vistas de perfil. Resuena tiene tres tipos de usuario con dashboards distintos:

- **Artista/Sello:** ve su wallet de créditos, campañas activas, historial.
- **Curador:** ve campañas disponibles para él, sus entregas pendientes, su balance.
- **Admin:** ve solicitudes de aprobación pendientes, panel de gestión.

El sidebar muestra distintas opciones según el tipo de usuario (estático en esta fase; dinámico futuro). Mi Cuenta es compartida con campos específicos por tipo.

---

## Tareas


- [x] **T1.** Server component `(dashboard)/layout.tsx`: valida sesión JWT, si no válido `redirect('/login')`. Inyecta datos del usuario al árbol. Detecta tipo de usuario y expone al contexto.
- [x] **T2.** Componente `Sidebar` (`components/layout/Sidebar.tsx`): menú distinto según `tipo` de usuario, responsive con overlay móvil + Framer Motion.
- [x] **T3.** Componente `Header` (`components/layout/Header.tsx`): título "Resuena" + avatar + menú "Mi Perfil / Salir".
- [x] **T4.** Página `(dashboard)/home/page.tsx`: widget de bienvenida con KPI básico según tipo (artista: créditos disponibles; curador: campañas pendientes; admin: solicitudes pendientes).
- [x] **T5.** Endpoint `GET /users/me`: retorna datos del usuario en sesión (sin password_hash). Para curadores incluye estado de aprobación.
- [x] **T6.** Endpoint `PATCH /users/me`: acepta `{nombre_completo?}` (sello omitido por decisión) con sanitización XSS. Bitácora con diff.
- [x] **T7.** Endpoint `POST /users/me/photo`: multipart, valida MIME `image/jpeg`, redimensiona con Pillow (200×200 crop center), sube a S3 (prefijo `perfiles-avatar/`) vía `StorageService`, actualiza `foto_path` con la clave S3 (no la URL completa — las URLs se generan como presigned en tiempo de lectura).
- [x] **T8.** Endpoint `DELETE /users/me/photo`: elimina objeto de S3 vía `StorageService` + limpia `foto_path`.
- [x] **T9.** Endpoint `GET /config/public`: retorna `{titulo_plataforma, mensaje_bienvenida}`.
- [x] **T10.** Página `(dashboard)/mi-perfil/page.tsx`: formulario con preview de imagen, campos read-only (correo, tipo) y editable (nombre; sello omitido por decisión). Para curadores: sección read-only con estado de solicitud.
- [x] **T11.** Logout `POST /auth/logout`: invalida cookie + redirect. (ya existe de Fase 03, integrar en Header).
- [x] **T12.** `StorageService` (`src/infra/storage.py`) — **capa de abstracción sobre proveedores de almacenamiento en la nube**:
  - Interfaz base `StorageProvider` (Protocol) con métodos: `upload(key, data, content_type) -> str`, `delete(key)`, `presigned_url(key, expires_seconds) -> str`.
  - Implementación `S3Provider` usando `aioboto3` (async). Configurable vía `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_S3_BUCKET`. En dev, `AWS_ENDPOINT_URL=http://localstack:4566` redirige a LocalStack sin cambiar una línea de código.
  - `StorageService` instancia el provider correcto según `STORAGE_PROVIDER` env var (`s3` por defecto). Preparado para agregar `GCSProvider` o `AzureProvider` en el futuro implementando el mismo Protocol.
  - Buckets usados: `avatars`, `campanas-audio`, `campanas-imagenes`, `campanas-material`.
  - Las URLs públicas nunca se guardan en BD — solo la clave S3 (ej. `avatars/user-uuid.jpg`). Las URLs se generan como presigned con TTL configurable al momento de servir.
- [x] **T13.** Tests: MIME inválido rechazado, upload a S3/LocalStack correcto (objeto existe en bucket), presigned URL generada con TTL, `PATCH /users/me` ignora campos no editables.

---

## Archivos a crear

| Ruta | |
|------|-|
| `app/(dashboard)/layout.tsx` | |
| `app/(dashboard)/home/page.tsx` | |
| `app/(dashboard)/mi-perfil/page.tsx` | |
| `components/layout/Sidebar.tsx` | |
| `components/layout/Header.tsx` | |
| `components/layout/UserMenu.tsx` | |
| `components/ui/Avatar.tsx` | |
| `components/forms/PhotoUploader.tsx` | |
| `src/api/users.py` | |
| `src/api/config_public.py` | |
| `src/services/user_service.py` | |
| `src/infra/storage.py` | StorageProvider (Protocol) + S3Provider (aioboto3) + StorageService factory |
| `src/utils/sanitize.py` | |
| `lib/server-api.ts` | helper server components → API |
| `tests/integration/test_users_me.py` | |

---

## Tests / validaciones

- Acceder a `/home` sin sesión → redirige a `/login`.
- Artista y curador ven sidebars distintos al mismo tiempo en diferentes sesiones.
- Subir PNG → 415. Subir JPG → objeto en S3/LocalStack con clave `avatars/{user_id}.jpg`, `foto_path` actualizado en BD.
- `PATCH /users/me` con `{correo: "x@x.com"}` → campo ignorado.
- `GET /users/me` retorna `foto_url` como presigned URL con TTL (no URL permanente).
- Bitácora registra "Actualización de perfil propio".
- Cambiar `STORAGE_PROVIDER` a un provider stub en tests → `StorageService` usa el stub sin tocar código de negocio.

---

## Skill recomendado por tarea

- **T1-T4, T10:** `frontend-skill`.
- **T5-T9, T11, T12:** `developer-skill`.
- **T13:** `testing-skill`.

---

## PROGRESO

- [x] T1 — layout.tsx (session guard) + lib/server-api.ts + DashboardProvider (contexto)
- [x] T2 — Sidebar (responsive, por tipo de usuario) + store zustand `useSidebar` (compartido con Header)
- [x] T3 — Header + UserMenu + Avatar (logout T11 integrado)
- [x] T4 — Home page (KPI por tipo + mensaje_bienvenida) + redirect post-login/OTP/onboarding → /home
- [x] T5 — GET /users/me (foto_url presigned + estado_curador)
- [x] T6 — PATCH /users/me (sanitize XSS + bitácora con diff; sello omitido)
- [x] T7 — POST /users/me/photo (libmagic JPEG + Pillow 200×200 + S3 perfiles-avatar/)
- [x] T8 — DELETE /users/me/photo (borra objeto S3 + limpia foto_path, idempotente)
- [x] T9 — GET /config/public (público; seed en migración 0004)
- [x] T10 — Página mi-perfil + PhotoUploader + api.patch/api.upload en lib/api
- [x] T11 — Logout integrado en Header (UserMenu → POST /auth/logout → /login)
- [x] T12 — storage.py (StorageProvider Protocol + S3Provider aioboto3 SigV4 + StorageService factory)
- [x] T13 — Tests (tests/integration/test_users_me.py, 11 tests; provider stub vía dependency override)

**Última sesión:** 2026-06-28 — T1 completado. Creados `lib/server-api.ts` (cliente para Server
Components: reenvía la cookie de sesión a `http://api:8000/api/*` directamente, porque el rewrite
`/api/*` solo aplica a peticiones del navegador, no a fetches server-side), `components/layout/
DashboardProvider.tsx` (contexto cliente `useDashboardUser` hidratado desde el server) y
`app/(dashboard)/layout.tsx` (Server Component que valida sesión vía `/auth/me` y `redirect('/login')`
si falla). `(dashboard)` es route group → rutas en raíz (`/home`, `/mi-perfil`). DashboardUser.tipo
incluye `'admin'` para forward-compat (el backend `/auth/me` hoy solo devuelve artista/curador).
Validado en runtime con página temporal: sin sesión → 307 a /login; con sesión → 200 renderiza.
tsc limpio. OJO: no se usó el paquete `server-only` (no instalado; evitar dep nueva); `lib/server-api.ts`
solo debe importarse desde Server Components. OJO Next: carpetas con prefijo `_` son privadas (no
ruteables).
T2 completado: `components/layout/Sidebar.tsx` — rail fijo en desktop (`md+`) + overlay deslizable en
móvil con Framer Motion (AnimatePresence, backdrop, cierre por Escape/click/navegación, lock de
scroll). Menú estático por tipo (artista/curador/admin) vía `useDashboardUser`; varias rutas
(`/campanas`, `/creditos`, `/entregas`, `/balance`, `/admin/*`) apuntan a páginas de fases futuras.
El toggle móvil vive en un store zustand `useSidebar` exportado desde Sidebar.tsx (lo consumirá el
Header en T3). Montado en el layout. Validado: SSR muestra los items correctos por tipo (artista:
campañas/créditos; curador: campañas disponibles/entregas/balance). tsc limpio.

T3 + T11 completados: `components/ui/Avatar.tsx` (foto o iniciales), `components/layout/UserMenu.tsx`
(dropdown con nombre/correo/tipo, "Mi perfil" y "Salir" → `POST /auth/logout` + redirect a /login;
cierra por click-fuera/Escape) y `components/layout/Header.tsx` (sticky; hamburguesa móvil →
`useSidebar().toggle()` + logo móvil + UserMenu). Header montado en el layout. Validado: SSR muestra
nombre + iniciales + "Salir" + hamburguesa; logout por proxy → 200 y `/auth/me` posterior → 401.
tsc limpio. Shell de dashboard (layout+sidebar+header) COMPLETO.

T12 completado: `src/infra/storage.py` — `StorageProvider` (Protocol runtime_checkable: upload/
delete/presigned_url) + `S3Provider` (aioboto3 async, SigV4, path-style con endpoint custom) +
`StorageService` (fachada, única vía permitida) + factory `get_storage_service()` por
`STORAGE_PROVIDER`. Un solo bucket (`AWS_S3_BUCKET=resuena-dev`) con prefijos; los callers pasan
claves tipo `perfiles-avatar/<uuid>.jpg`. Nuevo setting `aws_public_endpoint_url`
(`AWS_PUBLIC_ENDPOINT_URL=http://localhost:4566` en dev): las presigned se firman contra el host
alcanzable por el navegador; uploads/deletes siguen usando el endpoint interno (`localstack:4566`).
Se añadió a settings.py, .env y .env.example; **api recreado** para activarlo. Validado contra
LocalStack: upload→presigned(TTL, SigV4)→GET coincide→delete→404. ruff limpio.

T5 completado: `src/models/dto/users.py` (UserMeDTO + UserUpdateDTO ya listo para T6),
`src/services/user_service.py` (`get_me`: foto_url presigned vía StorageService con TTL 1h +
`estado_curador` = estado de la solicitud más reciente, solo curadores), `src/api/users.py`
(`GET /users/me`, requiere sesión; StorageService inyectado por Depends), router registrado en
`src/api/__init__.py`. Validado: sin sesión→401; artista→estado_curador null; curador sin
aplicar→null; curador que aplica→"pendiente". ruff limpio.

T6 completado: `src/utils/sanitize.py` (`clean_text`: quita etiquetas HTML, control chars y
corchetes angulares, colapsa espacios), `UserUpdateDTO` reducido a `nombre_completo` (sello omitido
por decisión de producto 2026-06-28: el sello es entidad propia, se hará en fase futura),
`user_service.update_me` (sanitiza, diff, bitácora "Actualización de perfil propio" con
`{cambios:{campo:{antes,despues}}}`, no-op sin cambios), `PATCH /users/me`. Validado: nombre
actualizado; correo/tipo ignorados (no están en el DTO → pydantic los descarta); `<script>` saneado;
markup-only→422; bitácora con diff (2 eventos) y PATCH sin cambios no agrega evento. ruff limpio.

T7 completado: `UnsupportedMediaTypeError`→415 (exceptions.py + errors.py), `user_service.set_photo`
+ `_procesar_avatar` (MIME real con libmagic → solo `image/jpeg`; reencode Pillow `ImageOps.fit`
200×200 center-crop, quality 85, descarta metadatos; máx 5 MB), `POST /users/me/photo` (UploadFile).
Clave S3 `perfiles-avatar/<usuario_id>.jpg`; `foto_path` guarda la clave (no la URL). Validado:
PNG→415; JPG 640×360→200, objeto en S3 `image/jpeg` 200×200; `foto_path`=clave; `foto_url` presigned
alcanzable desde el host (200). Deps ya presentes (Pillow/python-magic/libmagic/python-multipart).
ruff limpio.

T8 completado: `user_service.delete_photo` (borra el objeto S3 vía `StorageService.delete` y limpia
`foto_path`; no-op si no hay foto) + `DELETE /users/me/photo`. Validado: upload→DELETE→200 con
`foto_url` null y `foto_path` vacío; objeto ausente en S3 (head_object 404); segundo DELETE
idempotente→200. ruff limpio.

T9 completado: migración **0004** (seed `titulo_plataforma`, `mensaje_bienvenida` en
`parametros_config`, no secretos), `src/services/config_service.py` (`get_public_config`: lee solo
no-secretos, defaults si faltan), `src/api/config_public.py` (`GET /config/public`, **público**),
router registrado. Validado: ruff src/ limpio; migración con mismo estilo template que 0002/0003;
rollback idempotente (downgrade 0003→0 filas, upgrade head→2); endpoint sin sesión→200 con ambos
params. (head de alembic ahora 0004.)

T4 completado: `app/(dashboard)/home/page.tsx` (client) — saludo con primer nombre, KPI principal
por tipo (placeholder 0; artista=créditos, curador=campañas pendientes, admin=solicitudes) + tarjeta
"próximamente"; lee `mensaje_bienvenida` de `GET /config/public` (fallback en SSR). Cableado el
redirect post-login (OTPModal `onSuccess`) y onboarding completado a `/home`. Validado: `/home` sin
sesión→307 a /login; artista→saludo+KPI créditos+sidebar+header con nombre; curador→KPI campañas
pendientes. Shell completo (guard+sidebar+header) probado en runtime sobre página real. tsc limpio.

T10 completado: `lib/api` ampliado con `patch` y `upload` (multipart sin Content-Type),
`components/forms/PhotoUploader.tsx` (Avatar + subir JPEG vía `POST /users/me/photo` / eliminar vía
`DELETE`, valida tipo en cliente, estados loading/error), `app/(dashboard)/mi-perfil/page.tsx`
(carga `GET /users/me`; nombre editable→`PATCH`; correo/tipo read-only; curadores: sección con
`estado_curador`). BUG corregido: el page usaba `api.put` (no existía ruta PUT) → cambiado a
`api.patch`. Validado: guard 307 sin sesión; `/mi-perfil` 200 con sesión; PATCH nombre OK;
upload→foto_url set, delete→null. tsc limpio.

T13 completado: `tests/integration/test_users_me.py` (11 tests, todos verdes). Cubre: `/users/me`
requiere sesión (401); curador con `estado_curador`; `PATCH` ignora `correo`/`tipo`; sanitización
XSS; bitácora "Actualización de perfil propio" con diff; PNG→415 (sin subir nada); JPG→`foto_path`
= `perfiles-avatar/{id}.jpg` + reencode 200×200; `foto_url` presigned con TTL (`FOTO_URL_TTL_SECONDS`);
delete idempotente; **StorageService con `StubProvider`** (Protocol) inyectado por dependency
override — aísla de LocalStack y prueba la swappability; `/config/public` sin sesión. Suite completa:
**43 passed**. Correr con `docker compose exec -e TESTING=1 api pytest`.

**FASE 04 COMPLETA (13/13).** Próximo: cierre de sesión (actualizar PLAN.md/CHECKPOINT, marcar Fase
04 `[x]` y Fase 05 `[~]`, commit) o iniciar **Fase 05 — Admin: Aprobación de curadores + RBAC**
(`claude-opus-4-7`). Recordatorio: redirect post-login ya apunta a `/home`; sello sigue omitido
(decisión 2026-06-28); deuda heredada de onboarding (sin GET de selecciones previas).