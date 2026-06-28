# Fase 04 — Layout Dashboard + Perfiles de usuario

> **Estado:** `[ ]` pendiente · **Días estimados:** 3 · **Modelo:** `claude-sonnet-4-6`
> **Skills:** `frontend-skill`, `developer-skill`
> **Pre-requisitos:** Fase 03 `[x]`

---

## Contexto

Esta fase construye el **shell visual** de la aplicación protegida y las vistas de perfil. Resuena tiene tres tipos de usuario con dashboards distintos:

- **Artista/Sello:** ve su wallet de créditos, campañas activas, historial.
- **Profesional:** ve campañas disponibles para él, sus entregas pendientes, su balance.
- **Admin:** ve solicitudes de aprobación pendientes, panel de gestión.

El sidebar muestra distintas opciones según el tipo de usuario (estático en esta fase; dinámico futuro). Mi Cuenta es compartida con campos específicos por tipo.

---

## Tareas

- [ ] **T1.** Server component `(dashboard)/layout.tsx`: valida sesión JWT, si no válido `redirect('/login')`. Inyecta datos del usuario al árbol. Detecta tipo de usuario y expone al contexto.
- [ ] **T2.** Componente `Sidebar` (`components/layout/Sidebar.tsx`): menú distinto según `tipo` de usuario, responsive con overlay móvil + Framer Motion.
- [ ] **T3.** Componente `Header` (`components/layout/Header.tsx`): título "Resuena" + avatar + menú "Mi Perfil / Salir".
- [ ] **T4.** Página `(dashboard)/home/page.tsx`: widget de bienvenida con KPI básico según tipo (artista: créditos disponibles; profesional: campañas pendientes; admin: solicitudes pendientes).
- [ ] **T5.** Endpoint `GET /users/me`: retorna datos del usuario en sesión (sin password_hash). Para profesionales incluye estado de aprobación.
- [ ] **T6.** Endpoint `PATCH /users/me`: acepta `{nombre_completo?, sello_discografico?}` con sanitización XSS. Bitácora con diff.
- [ ] **T7.** Endpoint `POST /users/me/photo`: multipart, valida MIME `image/jpeg`, redimensiona con Pillow (200×200 crop center), sube a S3 bucket `avatars` vía `StorageService`, actualiza `foto_path` con la clave S3 (no la URL completa — las URLs se generan como presigned en tiempo de lectura).
- [ ] **T8.** Endpoint `DELETE /users/me/photo`: elimina objeto de S3 vía `StorageService` + limpia `foto_path`.
- [ ] **T9.** Endpoint `GET /config/public`: retorna `{titulo_plataforma, mensaje_bienvenida}`.
- [ ] **T10.** Página `(dashboard)/mi-perfil/page.tsx`: formulario con preview de imagen, campos read-only (correo, tipo) y editables (nombre, sello si es artista). Para profesionales: sección read-only con estado de solicitud.
- [ ] **T11.** Logout `POST /auth/logout`: invalida cookie + redirect. (ya existe de Fase 03, integrar en Header).
- [ ] **T12.** `StorageService` (`src/infra/storage.py`) — **capa de abstracción sobre proveedores de almacenamiento en la nube**:
  - Interfaz base `StorageProvider` (Protocol) con métodos: `upload(key, data, content_type) -> str`, `delete(key)`, `presigned_url(key, expires_seconds) -> str`.
  - Implementación `S3Provider` usando `aioboto3` (async). Configurable vía `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_S3_BUCKET`. En dev, `AWS_ENDPOINT_URL=http://localstack:4566` redirige a LocalStack sin cambiar una línea de código.
  - `StorageService` instancia el provider correcto según `STORAGE_PROVIDER` env var (`s3` por defecto). Preparado para agregar `GCSProvider` o `AzureProvider` en el futuro implementando el mismo Protocol.
  - Buckets usados: `avatars`, `campanas-audio`, `campanas-imagenes`, `campanas-material`.
  - Las URLs públicas nunca se guardan en BD — solo la clave S3 (ej. `avatars/user-uuid.jpg`). Las URLs se generan como presigned con TTL configurable al momento de servir.
- [ ] **T13.** Tests: MIME inválido rechazado, upload a S3/LocalStack correcto (objeto existe en bucket), presigned URL generada con TTL, `PATCH /users/me` ignora campos no editables.

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
- Artista y profesional ven sidebars distintos al mismo tiempo en diferentes sesiones.
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

- [ ] T1 — layout.tsx (session guard)
- [ ] T2 — Sidebar (responsive, por tipo de usuario)
- [ ] T3 — Header
- [ ] T4 — Home page (KPIs básicos)
- [ ] T5 — GET /users/me
- [ ] T6 — PATCH /users/me
- [ ] T7 — POST /users/me/photo (S3 vía StorageService)
- [ ] T8 — DELETE /users/me/photo
- [ ] T9 — GET /config/public
- [ ] T10 — Página mi-perfil
- [ ] T11 — Logout integrado en Header
- [ ] T12 — storage.py (StorageProvider Protocol + S3Provider + StorageService factory)
- [ ] T13 — Tests

**Última sesión:** —
**Próximo paso al reanudar:** T1 — server component `(dashboard)/layout.tsx` con validación de sesión y redirect a `/login` si no hay cookie válida.
