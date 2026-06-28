# Fase 03 — Autenticación (registro artista/profesional + login + OTP + reset)

> **Estado:** `[ ]` pendiente · **Días estimados:** 4 · **Modelo:** `claude-opus-4-7`
> **Skills:** `security-skill`, `developer-skill`
> **Pre-requisitos:** Fase 02 `[x]`

---

## Contexto

Esta fase implementa el **módulo más sensible** del sistema. Resuena tiene dos tipos de usuario con flujos de registro distintos:

- **Artistas / Sellos discográficos:** se registran directamente, confirman email y pueden operar de inmediato (comprar créditos, crear campañas).
- **Profesionales (bloggers, playlisters, influencers, reels):** se registran, confirman email, luego envían su solicitud de aplicación (portfolio, redes sociales, tipo). Un admin revisa y aprueba o rechaza. Solo después de aprobación pueden recibir campañas.

Flujos cubiertos:
1. Registro artista → email de confirmación → login.
2. Registro profesional → email de confirmación → formulario de aplicación → espera de aprobación.
3. Login con credenciales → OTP por email → sesión.
4. Solicitud de reset → email con token → cambio de password con patrón fuerte.

Reglas críticas:
- **BCrypt** para passwords (cost 12+).
- **Patrón fuerte:** mínimo 8 caracteres, 1 mayúscula, 1 minúscula, 1 número, 1 símbolo.
- **Tokens UUID** de un solo uso con `expires_at` y `consumed_at`.
- **Estado pre-autenticado** server-side para que el usuario no pueda saltarse el OTP.
- **Contador de intentos fallidos** → bloqueo por 6h al superar umbral configurable.
- **Bitácora** obligatoria: login fallido, login exitoso (post-OTP), reset, registro confirmado, aplicación profesional enviada.

---

## Tareas

- [ ] **T1.** Servicio de password (`src/services/password_service.py`): `hash(password)`, `verify(password, hash)`, `validate_pattern(password) -> bool`.
- [ ] **T2.** Servicio de tokens (`src/services/token_service.py`): `create(tipo, usuario_id, ttl_minutes)`, `consume(token)`.
- [ ] **T3.** Servicio de email (`src/services/email_service.py`) usando `aiosmtplib` + Jinja2 apuntando a MailHog. Templates: OTP, confirmación artista, confirmación profesional, reset, notificación aprobación/rechazo.
- [ ] **T4.** Servicio de OTP (`src/services/otp_service.py`): código numérico 6 dígitos, guardado en Redis con TTL 10 min asociado a `pre_auth_session_id`.
- [ ] **T5.** Endpoint `POST /auth/register/artista`: valida datos, crea usuario en estado `pendiente`, envía email de confirmación.
- [ ] **T6.** Endpoint `POST /auth/register/profesional`: igual que T5 pero con `tipo=profesional`. Crea registro en `solicitudes_profesional` con estado `pendiente` tras confirmación de email.
- [ ] **T7.** Endpoint `GET /auth/confirm/{token}`: consume token, activa usuario. Para profesionales: redirige a `/aplicar` para completar el formulario de solicitud.
- [ ] **T8.** Endpoint `POST /auth/aplicar` (solo profesionales confirmados): recibe `{tipo_profesional, url_portfolio, redes_sociales}`, persiste en `solicitudes_profesional`, notifica al admin por email.
- [ ] **T9.** Endpoint `POST /auth/login`: valida credenciales, verifica estado (activo, no bloqueado, aprobado si profesional), genera `pre_auth_session_id` + dispara OTP.
- [ ] **T10.** Endpoint `POST /auth/otp/verify`: valida código, crea sesión JWT (cookie HttpOnly + Secure + SameSite=Lax).
- [ ] **T11.** Endpoint `POST /auth/forgot-password`: genera token de reset (TTL 1h), envía email. Siempre retorna 200.
- [ ] **T12.** Endpoint `POST /auth/reset-password/{token}`: valida token + patrón, actualiza `password_hash`, marca token consumido.
- [ ] **T13.** Endpoint `POST /auth/logout`: invalida cookie + redirect.
- [ ] **T14.** Middleware de auth (`src/middleware/auth.py`): valida JWT de cookie en cada request, inyecta `request.state.user`.
- [ ] **T15.** Vistas Next.js:
  - `app/(auth)/login/page.tsx` — formulario + modal OTP.
  - `app/(auth)/registro/artista/page.tsx` — registro artista.
  - `app/(auth)/registro/profesional/page.tsx` — registro profesional.
  - `app/(auth)/aplicar/page.tsx` — formulario de aplicación profesional (post-confirmación).
  - `app/(auth)/confirm/[token]/page.tsx` — server component confirma token.
  - `app/(auth)/forgot/page.tsx` — solicitud de reset.
  - `app/(auth)/reset/[token]/page.tsx` — formulario nueva password.
  - `app/(auth)/pendiente/page.tsx` — pantalla "tu solicitud está en revisión".
- [ ] **T16.** Tests: flujos happy path + edge cases (token expirado, OTP incorrecto, password débil, profesional no aprobado intenta login).

---

## Archivos a crear

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

---

## Tests / validaciones

- Registro artista → confirmar email → login exitoso (con OTP).
- Registro profesional → confirmar → aplicar → pantalla "en revisión" al intentar login.
- 5 logins fallidos → bloqueo por 6h, siguiente intento retorna 423 con `blocked_until`.
- Token de confirmación expirado → 410 Gone.
- OTP incorrecto → 401 sin invalidar `pre_auth_session_id`.
- Reset con token consumido → 400.
- Bitácora contiene los 5 tipos de eventos esperados.

---

## Skill recomendado por tarea

- **T1, T2, T4, T9, T10, T12, T14:** `security-skill`.
- **T3, T5, T6, T7, T8, T11, T13:** `developer-skill`.
- **T15:** `frontend-skill`.
- **T16:** `testing-skill`.

---

## PROGRESO

- [ ] T1 — password_service
- [ ] T2 — token_service
- [ ] T3 — email_service + 5 templates
- [ ] T4 — otp_service
- [ ] T5 — POST /auth/register/artista
- [ ] T6 — POST /auth/register/profesional
- [ ] T7 — GET /auth/confirm/{token}
- [ ] T8 — POST /auth/aplicar
- [ ] T9 — POST /auth/login
- [ ] T10 — POST /auth/otp/verify
- [ ] T11 — POST /auth/forgot-password
- [ ] T12 — POST /auth/reset-password/{token}
- [ ] T13 — POST /auth/logout
- [ ] T14 — Middleware auth
- [ ] T15 — 8 vistas Next.js
- [ ] T16 — Tests pytest

**Última sesión:** —
**Próximo paso al reanudar:** T1 — implementar `password_service.py` (BCrypt cost 12 + validador de patrón fuerte ≥8 chars con mayúscula, minúscula, número y símbolo).
