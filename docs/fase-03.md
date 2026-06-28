# Fase 03 — Autenticación (registro artista/profesional + login + OTP + reset)

> **Estado:** `[ ]` pendiente · **Días estimados:** 4 · **Modelo:** `claude-opus-4-7`
> **Skills:** `security-skill`, `developer-skill`
> **Pre-requisitos:** Fase 02 `[x]`

---

## Contexto

Esta fase implementa el **módulo más sensible** del sistema y el **onboarding completo** de perfil. Resuena tiene dos tipos de usuario con flujos de registro distintos:

- **Artistas / Sellos discográficos:** se registran directamente, confirman email, completan onboarding de perfil (géneros, idiomas, regiones, redes sociales) y pueden operar de inmediato.
- **Profesionales/Curadores (bloggers, playlisters, influencers, reels):** se registran, confirman email, completan onboarding de perfil (géneros, idiomas, regiones, tipo de contenido, medios/canales), envían solicitud de aplicación. Un admin revisa y aprueba o rechaza.

Flujos cubiertos:
1. Registro artista → email de confirmación → onboarding perfil (4 pasos) → login.
2. Registro profesional → email de confirmación → onboarding perfil (5 pasos) → espera de aprobación.
3. Login con credenciales → OTP por email → sesión.
4. Solicitud de reset → email con token → cambio de password con patrón fuerte.

Onboarding artista (4 pasos post-confirmación):
- **Paso 1 — Géneros:** selección múltiple de `generos_musicales` → guarda en `usuario_generos` (tipo=preferido).
- **Paso 2 — Idiomas:** selección de idiomas del catálogo `idiomas` → guarda en `usuario_preferencias_idiomas`.
- **Paso 3 — Regiones:** selección de países de `regiones` → guarda en `usuario_preferencias_regiones`.
- **Paso 4 — Redes sociales:** URLs de sus plataformas → guarda en `usuario_redes`.

Onboarding curador (5 pasos post-confirmación):
- **Paso 1 — Géneros:** igual que artista.
- **Paso 2 — Idiomas:** igual que artista.
- **Paso 3 — Regiones:** igual que artista.
- **Paso 4 — Tipo de contenido / Medios:** agrega sus canales a `curador_medios` (nombre, tipo, URL, audiencia estimada) con géneros especializados por canal via `curador_medio_generos`.
- **Paso 5 — Redes sociales:** igual que artista.

Reglas críticas:
- **BCrypt** para passwords (cost 12+).
- **Patrón fuerte:** mínimo 8 caracteres, 1 mayúscula, 1 minúscula, 1 número, 1 símbolo.
- **Tokens UUID** de un solo uso con `expires_at` y `consumed_at`.
- **Estado pre-autenticado** server-side para que el usuario no pueda saltarse el OTP.
- **Contador de intentos fallidos** → bloqueo por 6h al superar umbral configurable.
- **Bitácora** obligatoria: login fallido, login exitoso (post-OTP), reset, registro confirmado, onboarding completado, aplicación profesional enviada.
- **Onboarding incompleto:** el usuario puede guardar pasos parciales; el sistema recuerda hasta dónde llegó. No se bloquea el acceso, pero se muestra banner de "completa tu perfil".

---

## Tareas

- [x] **T1.** Servicio de password (`src/services/password_service.py`): `hash(password)`, `verify(password, hash)`, `validate_pattern(password) -> bool`.
- [x] **T2.** Servicio de tokens (`src/services/token_service.py`): `create(tipo, usuario_id, ttl_minutes)`, `consume(token)`.
- [x] **T3.** Servicio de email (`src/services/email_service.py`) usando `aiosmtplib` + Jinja2 apuntando a MailHog. Templates: OTP, confirmación artista, confirmación profesional, reset, notificación aprobación/rechazo.
- [x] **T4.** Servicio de OTP (`src/services/otp_service.py`): código numérico 6 dígitos, guardado en Redis con TTL 10 min asociado a `pre_auth_session_id`.
- [x] **T5.** Endpoint `POST /auth/register/artista`: valida datos, crea usuario en estado `pendiente`, envía email de confirmación.
- [x] **T6.** Endpoint `POST /auth/register/profesional`: igual que T5 pero con `tipo=profesional`. Crea registro en `solicitudes_profesional` con estado `pendiente` tras confirmación de email.
- [x] **T7.** Endpoint `GET /auth/confirm/{token}`: consume token, activa usuario. Para profesionales: redirige a `/aplicar` para completar el formulario de solicitud.
- [x] **T8.** Endpoint `POST /auth/aplicar` (solo profesionales confirmados): recibe `{tipo_profesional, url_portfolio}`, persiste en `solicitudes_curador`, notifica al admin por email.
- [x] **T9.** Endpoint `POST /auth/login`: valida credenciales, verifica estado (activo, no bloqueado, aprobado si profesional), genera `pre_auth_session_id` + dispara OTP.
- [x] **T10.** Endpoint `POST /auth/otp/verify`: valida código, crea sesión JWT (cookie HttpOnly + Secure + SameSite=Lax).
- [x] **T11.** Endpoint `POST /auth/forgot-password`: genera token de reset (TTL 1h), envía email. Siempre retorna 200.
- [x] **T12.** Endpoint `POST /auth/reset-password/{token}`: valida token + patrón, actualiza `password_hash`, marca token consumido.
- [x] **T13.** Endpoint `POST /auth/logout`: invalida cookie + redirect.
- [x] **T14.** Middleware de auth (`src/middleware/auth.py`): valida JWT de cookie en cada request, inyecta `request.state.user`.

### Servicios de perfil / onboarding

- [x] **T17.** Servicio de catálogos (`src/services/catalogo_service.py`):
  - `get_generos() → list[Genero]` — retorna géneros activos del catálogo.
  - `get_idiomas() → list[Idioma]` — retorna catálogo `idiomas`.
  - `get_regiones() → list[Region]` — retorna catálogo `regiones`.
  - `get_tipos_curador_medio() → list[str]` — retorna valores válidos del ENUM `curador_medios.tipo`.

- [x] **T18.** Servicio de onboarding (`src/services/onboarding_service.py`):
  - `get_progreso(usuario_id) → OnboardingProgressDTO` — devuelve qué pasos están completos.
  - `save_generos(usuario_id, genero_ids: list[int], tipo: str)` — upsert en `usuario_generos`.
  - `save_idiomas(usuario_id, codigos: list[str])` — upsert en `usuario_preferencias_idiomas`.
  - `save_regiones(usuario_id, codigos: list[str])` — upsert en `usuario_preferencias_regiones`.
  - `save_redes(usuario_id, redes: list[RedSocialDTO])` — upsert en `usuario_redes`.
  - `save_preferencias(usuario_id, apertura_musical, acepta_todos_idiomas, tipo_lanzamientos)` — upsert en `usuario_preferencias`.

- [x] **T19.** Servicio de medios curador (`src/services/curador_medio_service.py`):
  - `add_medio(curador_id, data: CuradorMedioDTO) → CuradorMedio` — crea fila en `curador_medios` + géneros en `curador_medio_generos`.
  - `update_medio(medio_id, curador_id, data)` — actualiza, reemplaza géneros.
  - `delete_medio(medio_id, curador_id)` — soft-delete (activo=False).
  - `list_medios(curador_id) → list[CuradorMedioDTO]` — lista todos los canales del curador.

- [x] **T20.** Endpoints de onboarding (`src/api/onboarding.py`):
  - `GET  /onboarding/progreso` — retorna pasos completados.
  - `PUT  /onboarding/generos` — body: `{genero_ids: list[int]}`.
  - `PUT  /onboarding/idiomas` — body: `{codigos: list[str]}`.
  - `PUT  /onboarding/regiones` — body: `{codigos: list[str]}`.
  - `PUT  /onboarding/preferencias` — body: `{apertura_musical, acepta_todos_idiomas, tipo_lanzamientos}`.
  - `GET  /onboarding/redes` — lista redes del usuario.
  - `POST /onboarding/redes` — agrega red social.
  - `DELETE /onboarding/redes/{red_id}` — elimina red social.
  - `GET  /onboarding/medios` — lista canales del curador (solo curadores).
  - `POST /onboarding/medios` — agrega canal (solo curadores).
  - `PUT  /onboarding/medios/{medio_id}` — edita canal.
  - `DELETE /onboarding/medios/{medio_id}` — elimina canal.
  - `GET  /catalogos/generos` — catálogo público.
  - `GET  /catalogos/idiomas` — catálogo público.
  - `GET  /catalogos/regiones` — catálogo público.

- [x] **T21.** DTOs Pydantic (`src/models/dto/onboarding.py`):
  - `RedSocialDTO` (tipo ENUM, url str).
  - `CuradorMedioDTO` (nombre, tipo, url, descripcion, genero_ids, audiencia_estimada).
  - `OnboardingProgressDTO` (pasos completados por nombre: generos, idiomas, regiones, redes, medios, preferencias).

- [ ] **T15.** Vistas Next.js — Auth:
  - `app/(auth)/login/page.tsx` — formulario + modal OTP.
  - `app/(auth)/registro/artista/page.tsx` — registro artista.
  - `app/(auth)/registro/profesional/page.tsx` — registro profesional.
  - `app/(auth)/aplicar/page.tsx` — formulario de aplicación profesional (post-confirmación).
  - `app/(auth)/confirm/[token]/page.tsx` — server component confirma token.
  - `app/(auth)/forgot/page.tsx` — solicitud de reset.
  - `app/(auth)/reset/[token]/page.tsx` — formulario nueva password.
  - `app/(auth)/pendiente/page.tsx` — pantalla "tu solicitud está en revisión".

- [ ] **T22.** Vistas Next.js — Onboarding wizard:
  > Diseño: heredar `globals.css` del proyecto Resuena. Ver sección "Sistema de diseño" en este archivo. Assets en `resuena/` → copiar a `public/` antes de implementar.
  - `app/(onboarding)/layout.tsx` — layout del wizard con stepper lateral/superior, progress bar, logo.
  - `app/(onboarding)/generos/page.tsx` — grid de géneros seleccionables con chips/pills; multi-select; mínimo 1 requerido.
  - `app/(onboarding)/idiomas/page.tsx` — lista con banderas o códigos ISO; multi-select.
  - `app/(onboarding)/regiones/page.tsx` — mapa visual o listado de países; multi-select con búsqueda.
  - `app/(onboarding)/redes/page.tsx` — lista de plataformas (Spotify, Instagram, YouTube, etc.) con campo URL por cada una; validación de formato URL.
  - `app/(onboarding)/medios/page.tsx` — solo curadores: formulario para agregar canales (nombre, tipo, URL, audiencia, géneros especializados). Permite agregar N canales.
  - `app/(onboarding)/completado/page.tsx` — pantalla de éxito con CTA al dashboard.
  - `components/onboarding/StepperNav.tsx` — navegación lateral/superior del wizard con estado por paso.
  - `components/onboarding/GenreChip.tsx` — chip seleccionable con nombre de género.
  - `components/onboarding/MedioForm.tsx` — formulario de canal del curador con multi-select de géneros especializados.
  - `components/onboarding/RedSocialRow.tsx` — fila de red social con ícono + input URL + validación.
  - `hooks/useOnboardingProgress.ts` — hook que consume `GET /onboarding/progreso` y controla navegación entre pasos.

- [ ] **T16.** Tests: flujos happy path + edge cases (token expirado, OTP incorrecto, password débil, profesional no aprobado intenta login, onboarding parcial → banner de completar perfil).

---

## Archivos a crear

| Ruta | |
|------|-|
**Auth**
| Ruta | |
|------|-|
| `src/api/auth.py` | |
| `src/services/auth_service.py` | |
| `src/services/otp_service.py` | |
| `src/services/token_service.py` | |
| `src/services/email_service.py` | |
| `src/services/password_service.py` | |
| `src/services/bitacora_service.py` | |
| `src/infra/email_templates/otp.html` | |
| `src/infra/email_templates/confirm_artista.html` | |
| `src/infra/email_templates/confirm_profesional.html` | |
| `src/infra/email_templates/reset.html` | |
| `src/infra/email_templates/aprobacion.html` | |
| `src/infra/email_templates/rechazo.html` | |
| `src/middleware/auth.py` | |
| `src/models/dto/auth.py` | Pydantic DTOs |
| `app/(auth)/login/page.tsx` | |
| `app/(auth)/registro/artista/page.tsx` | |
| `app/(auth)/registro/profesional/page.tsx` | |
| `app/(auth)/aplicar/page.tsx` | |
| `app/(auth)/confirm/[token]/page.tsx` | |
| `app/(auth)/forgot/page.tsx` | |
| `app/(auth)/reset/[token]/page.tsx` | |
| `app/(auth)/pendiente/page.tsx` | |
| `components/auth/PasswordStrengthMeter.tsx` | |
| `components/auth/OTPModal.tsx` | |
| `tests/unit/test_password_service.py` | |
| `tests/integration/test_auth_endpoints.py` | |

**Onboarding / Perfil**
| Ruta | |
|------|-|
| `src/api/onboarding.py` | endpoints onboarding + catálogos |
| `src/services/catalogo_service.py` | géneros, idiomas, regiones, tipos medio |
| `src/services/onboarding_service.py` | progreso + guardado por paso |
| `src/services/curador_medio_service.py` | CRUD canales del curador |
| `src/models/dto/onboarding.py` | RedSocialDTO, CuradorMedioDTO, OnboardingProgressDTO |
| `app/(onboarding)/layout.tsx` | layout wizard con stepper |
| `app/(onboarding)/generos/page.tsx` | paso 1 — géneros |
| `app/(onboarding)/idiomas/page.tsx` | paso 2 — idiomas |
| `app/(onboarding)/regiones/page.tsx` | paso 3 — regiones/países |
| `app/(onboarding)/redes/page.tsx` | paso 4 — redes sociales |
| `app/(onboarding)/medios/page.tsx` | paso 5 (solo curadores) — canales |
| `app/(onboarding)/completado/page.tsx` | pantalla de éxito |
| `components/onboarding/StepperNav.tsx` | navegación lateral del wizard |
| `components/onboarding/GenreChip.tsx` | chip seleccionable de género |
| `components/onboarding/MedioForm.tsx` | formulario de canal del curador |
| `components/onboarding/RedSocialRow.tsx` | fila de red social + validación URL |
| `hooks/useOnboardingProgress.ts` | hook progreso + navegación |
| `tests/integration/test_onboarding_endpoints.py` | |

---

## Tests / validaciones

**Auth:**
- Registro artista → confirmar email → login exitoso (con OTP).
- Registro profesional → confirmar → aplicar → pantalla "en revisión" al intentar login.
- 5 logins fallidos → bloqueo por 6h, siguiente intento retorna 423 con `blocked_until`.
- Token de confirmación expirado → 410 Gone.
- OTP incorrecto → 401 sin invalidar `pre_auth_session_id`.
- Reset con token consumido → 400.
- Bitácora contiene los 6 tipos de eventos esperados.

**Onboarding:**
- Artista completa 4 pasos → `OnboardingProgressDTO` marca los 4 completos.
- Curador completa 5 pasos incluyendo 2 medios → `curador_medios` tiene 2 filas, `curador_medio_generos` tiene las filas correctas.
- Guardar géneros con `genero_id` inexistente → 422 (FK violation manejada en service).
- Guardar idioma con `codigo` no en catálogo → 422.
- Curador intenta agregar medio con `tipo` no válido → 422.
- Onboarding parcial (solo géneros guardados) → `GET /onboarding/progreso` retorna solo `generos: true`.
- Artista intenta acceder a `POST /onboarding/medios` → 403 Forbidden.
- `GET /catalogos/generos` retorna 20 géneros del seed.

---

## Sistema de diseño

> Fuente de verdad: `globals.css` del proyecto Resuena (nextjs-frontend). Copiar íntegro al nuevo frontend — no rediseñar.

### Paleta de colores

| Token CSS | Valor | Uso |
|---|---|---|
| `--bg-base` | `#0f0c1f` | Fondo de todas las páginas |
| `--bg-surface` | `#13102a` | Cards, modales, paneles |
| `--accent-purple` | `#5c269c` | Botones primarios, links activos |
| `--accent-purple-light` | `#7b3fcf` | Hover, gradientes |
| `--accent-glow` | `rgba(92,38,156,0.4)` | Box-shadow / glow en elementos activos |
| `--text-primary` | `#f0eaf8` | Texto principal |
| `--text-secondary` | `#9b8ab4` | Labels, placeholders, texto de apoyo |
| `--border-subtle` | `rgba(255,255,255,0.08)` | Bordes de cards y separadores |

### Tipografía

- **Fuente:** Inter Variable (`Inter-VariableFont_opsz,wght.ttf`)
- **Ruta de assets:** `resuena/Inter/Inter-VariableFont_opsz,wght.ttf` (y su variante italic)
- **Pesos usados:** Regular (400), Medium (500), SemiBold (600), Bold (700)
- Configurar en `layout.tsx` con `next/font/local` apuntando a los `.ttf` del repositorio

### Logos disponibles

| Archivo | Uso recomendado |
|---|---|
| `resuena/logotipofull-01.png` | Header del wizard onboarding, página "pendiente" |
| `resuena/RESUENA copia.svg` | Preferido donde aplique SVG (escalable, sin aliasing) |
| `resuena/256 sin fondo.png` | Icono sin fondo para fondos oscuros |
| `resuena/80x80.png` | Favicon o icono pequeño |
| `resuena/favicon.png` | `<link rel="icon">` en layout raíz |
| `resuena/icono 256x256 don fondo.png` | Avatar / icono de app en pantallas de carga |

Copiar estos assets a `public/` del proyecto NextJS antes de T15 y T22.

### Clases de utilidad ya definidas en globals.css

| Clase | Descripción |
|---|---|
| `.onboarding-shell` | Fondo con gradiente radial morado — usar en `layout.tsx` del wizard |
| `.onboarding-progress-bar` | Barra de progreso animada con glow — usa `--progress-width` como CSS var |
| `.animate-onboarding-in` | Entrada del paso actual (slide desde derecha, 320ms) |
| `.auth-enter` | Entrada del formulario auth (fade + slide desde abajo, 340ms) |
| `.auth-shake` | Sacudida horizontal para errores de validación |
| `.auth-envelope` | Animación del sobre en pantalla "revisa tu correo" |
| `.auth-success-check` | Escala de entrada del checkmark de éxito |
| `.auth-wave-bar` | Barras de onda de sonido (decorativo) — usa `--auth-wave-duration` y `--auth-wave-delay` |
| `.credits-skeleton-shimmer` | Skeleton loader con shimmer para secciones de créditos |

### Reglas de aplicación

- **Fondo base:** todo `<body>` y layouts raíz usan `background: var(--bg-base)`.
- **Superficie:** cards y modales usan `background: var(--bg-surface)` con `border: 1px solid var(--border-subtle)`.
- **Botón primario:** `background: var(--accent-purple)`, hover → `var(--accent-purple-light)`, con `box-shadow: 0 0 16px var(--accent-glow)` en hover.
- **Inputs:** borde `var(--border-subtle)`, focus → borde `var(--accent-purple)` + ring `var(--accent-glow)`.
- **Texto:** `color: var(--text-primary)` en headings/body, `var(--text-secondary)` en labels y helpers.
- **Nunca usar fondo blanco** en ninguna vista — el sistema es 100% dark.

---

## Skill recomendado por tarea

- **T1, T2, T4, T9, T10, T12, T14:** `security-skill`.
- **T3, T5, T6, T7, T8, T11, T13:** `developer-skill`.
- **T17, T18, T19, T20, T21:** `developer-skill` + `dba-skill`.
- **T15, T22:** `frontend-skill` — esperar diseño de referencia antes de implementar.
- **T16:** `testing-skill`.

---

## PROGRESO

**Auth:**
- [x] T1 — password_service
- [x] T2 — token_service (+ exceptions.py dominio)
- [x] T3 — email_service + 6 templates (+ _base.html)
- [x] T4 — otp_service (+ redis_client.py)
- [x] T5 — POST /auth/register/artista
- [x] T6 — POST /auth/register/profesional
- [x] T7 — GET /auth/confirm/{token} (emite sesión post-confirmación)
- [x] T8 — POST /auth/aplicar
- [x] T9 — POST /auth/login
- [x] T10 — POST /auth/otp/verify
- [x] T11 — POST /auth/forgot-password
- [x] T12 — POST /auth/reset-password/{token}
- [x] T13 — POST /auth/logout
- [x] T14 — Middleware auth (+ get_current_user / require_tipo)
- [ ] T15 — 8 vistas auth Next.js

**Onboarding / Perfil:**
- [x] T17 — catalogo_service (géneros, idiomas, regiones, tipos medio)
- [x] T18 — onboarding_service (progreso + guardado por paso)
- [x] T19 — curador_medio_service (CRUD canales)
- [x] T20 — endpoints /onboarding/* + /catalogos/*
- [x] T21 — DTOs Pydantic onboarding
- [ ] T22 — wizard onboarding Next.js (6 páginas + 4 componentes + 1 hook) — diseño: globals.css de Resuena

**Tests:**
- [ ] T16 — Tests pytest auth + onboarding

**Última sesión:** 2026-06-28 — Servicios base de auth (T1-T4) implementados y validados:
`password_service` (BCrypt cost 12 + pre-hash SHA-256 + patrón fuerte), `token_service` (un solo
uso con SELECT FOR UPDATE) + `exceptions.py` (excepciones de dominio tipadas), `email_service`
(aiosmtplib + Jinja2 → MailHog, 6 templates + _base.html, probado end-to-end), `otp_service`
(6 dígitos en Redis, TTL 10 min) + `redis_client.py`. Se añadieron `aiosmtplib==3.0.2` y
`jinja2==3.1.5` a requirements.txt (imagen api reconstruida). Rama: `fase-03-auth`.

**Próximo paso al reanudar:** Backend de auth (T5-T14) + onboarding (T17-T21) COMPLETOS y validados
end-to-end. Pendiente: T15+T22 (frontend Next.js auth + wizard onboarding), T16 (tests pytest).

Nota T17-T21: `catalogo_service` (géneros/idiomas/regiones/tipos medio), `onboarding_service`
(progreso + save_* idempotentes con validación FK→422), `curador_medio_service` (CRUD con
soft-delete y autorización a nivel de recurso), router `src/api/onboarding.py` (15 endpoints:
/onboarding/* protegidos, /catalogos/* públicos), DTOs `src/models/dto/onboarding.py`. Validado:
artista 5 pasos (progreso reactivo), géneros/idiomas inexistentes → 422, artista→medios 403,
curador 2 medios con géneros (curador_medio_generos correcto), tipo medio inválido → 422,
update/soft-delete OK. Ruff limpio.

Nota T5-T14: implementados `auth_service`, `bitacora_service`, `jwt_service`, DTOs
`src/models/dto/auth.py`, router `src/api/auth.py`, handlers `src/api/errors.py`, middleware
`src/middleware/auth.py`. Migración `0003` añade `tipo_profesional`/`url_portfolio` a
`solicitudes_curador` (lo exige T8). DECISIÓN DE FLUJO: `GET /auth/confirm/{token}` emite la
cookie de sesión (el profesional no aprobado no puede hacer login con OTP, así que necesita la
sesión post-confirmación para `/aplicar` y onboarding). Cookie JWT secure solo en producción
(dev es http). Validado curl end-to-end: happy path + 409 duplicado + 422 débil + 403 pro en
revisión + OTP incorrecto/correcto + reset + token consumido/inválido + bloqueo a los 5 intentos
(423) + /aplicar + 6 tipos de evento en bitácora. Ruff limpio.
