# Fase 06 — Sistema de créditos + Pasarela de pago (Stripe)

> **Estado:** `[x]` completada · **Días estimados:** 4 · **Modelo:** `claude-opus-4-7`
> **Skills:** `security-skill`, `developer-skill`
> **Pre-requisitos:** Fase 05 `[x]`

---

## Contexto

Los créditos son la moneda interna de Resuena. Los artistas compran créditos con dinero real (Stripe) y los gastan al enviar campañas. Los profesionales acumulan créditos al aceptar y entregar campañas, y luego solicitan retiro.

Reglas de negocio:
- 1 crédito = precio configurable (default $50 MXN).
- Al enviar una campaña a N profesionales → se retienen N créditos del wallet del artista.
- Si el profesional rechaza → crédito devuelto al artista.
- Si el profesional acepta y entrega → crédito transferido al balance del profesional.
- Si el profesional no responde en `dias_limite_respuesta` días → campaña expirada, crédito devuelto.
- La plataforma retiene un `porcentaje_comision` (default 20%) al momento de la transferencia al profesional.
- Idempotencia obligatoria en todas las transacciones (usar `referencia_stripe` o UUID de operación).

---

## Tareas

- [x] **T1.** Servicio `wallet_service.py`: `get_balance(usuario_id)`, `add_credits(usuario_id, monto, descripcion, ref)`, `deduct_credits(usuario_id, monto, descripcion, ref)`. Todas las operaciones atómicas con bloqueo de fila (`SELECT FOR UPDATE`).
- [x] **T2.** Servicio `stripe_service.py`: `create_checkout_session(usuario_id, cantidad_creditos)` → crea Stripe Checkout Session en modo test. `handle_webhook(payload, signature)` → procesa `checkout.session.completed`.
- [x] **T3.** Endpoint `GET /creditos/paquetes`: retorna lista de paquetes disponibles (5, 10, 20, 50 créditos con precio por paquete). Configurable desde `parametros_config`.
- [x] **T4.** Endpoint `POST /creditos/checkout`: crea Stripe Checkout Session, retorna `{checkout_url}`. Artistas únicamente.
- [x] **T5.** Endpoint `POST /creditos/webhook` (sin auth JWT): recibe webhook de Stripe, verifica firma `stripe-signature`, llama a `stripe_service.handle_webhook`. Si `checkout.session.completed`: acredita créditos al wallet del artista. Idempotente por `referencia_stripe`.
- [x] **T6.** Endpoint `GET /creditos/balance`: retorna `{saldo_creditos, saldo_pendiente_retiro}` del usuario en sesión.
- [x] **T7.** Endpoint `GET /creditos/historial`: transacciones paginadas del usuario (tipo, monto, descripción, fecha).
- [x] **T8.** Vista `(dashboard)/artista/creditos/page.tsx`: balance prominente, lista de paquetes con botón "Comprar" (redirect a Stripe Checkout), historial de transacciones server-paginated.
- [x] **T9.** Página `(dashboard)/artista/creditos/success/page.tsx`: pantalla de confirmación post-pago (Stripe redirige aquí). Revalida balance.
- [x] **T10.** Página `(dashboard)/artista/creditos/cancel/page.tsx`: cancelación de pago.
- [x] **T11.** Tests: compra simulada (webhook mock) → balance incrementa; deducción → saldo negativo bloqueado; idempotencia (mismo `referencia_stripe` dos veces → solo acredita una vez).

---

## Archivos a crear

| Ruta | |
|------|-|
| `src/services/wallet_service.py` | |
| `src/services/stripe_service.py` | |
| `src/api/creditos.py` | |
| `src/models/dto/creditos.py` | |
| `app/(dashboard)/artista/creditos/page.tsx` | |
| `app/(dashboard)/artista/creditos/success/page.tsx` | |
| `app/(dashboard)/artista/creditos/cancel/page.tsx` | |
| `components/creditos/PaqueteCard.tsx` | |
| `components/creditos/HistorialTransacciones.tsx` | |
| `tests/integration/test_creditos.py` | |
| `tests/unit/test_wallet_service.py` | |

---

## Tests / validaciones

- Webhook con firma inválida → 400.
- Webhook `checkout.session.completed` válido → wallet artista +N créditos, transacción en BD.
- Webhook duplicado (mismo `payment_intent`) → balance no cambia (idempotencia).
- `deduct_credits` con saldo insuficiente → lanza `InsufficientCreditsError`, sin transacción creada.
- `GET /creditos/balance` con artista sin wallet → retorna `{saldo_creditos: 0}` (wallet creado on-demand).
- Profesional intenta `POST /creditos/checkout` → 403.

---

## Notas de implementación

- Usar `STRIPE_SECRET_KEY` y `STRIPE_WEBHOOK_SECRET` de `.env` (modo test).
- El endpoint `/creditos/webhook` debe estar fuera del middleware JWT — Stripe no manda cookies.
- El wallet se crea automáticamente (`get_or_create`) en la primera transacción.
- `saldo_creditos` jamás debe bajar de 0 (CHECK constraint en BD + validación en servicio).

---

## Skill recomendado por tarea

- **T1:** `developer-skill` + `dba-skill` (SELECT FOR UPDATE, atomicidad).
- **T2, T5:** `security-skill` + `developer-skill` (webhooks Stripe, firma HMAC).
- **T3, T4, T6, T7:** `developer-skill`.
- **T8-T10:** `frontend-skill`.
- **T11:** `testing-skill`.

---

## PROGRESO

- [x] T1 — wallet_service (get_balance, add_credits idempotente, deduct_credits; SELECT FOR UPDATE)
- [x] T2 — stripe_service (create_checkout_session + handle_webhook con firma + idempotencia)
- [x] T3 — GET /creditos/paquetes (5/10/20/50 × precio_credito_mxn)
- [x] T4 — POST /creditos/checkout (require_artista; valida paquete; URL real Stripe)
- [x] T5 — POST /creditos/webhook (body crudo + firma; 400 inválida; acredita idempotente)
- [x] T6 — GET /creditos/balance (wallet on-demand 0)
- [x] T7 — GET /creditos/historial (transacciones paginadas)
- [x] T8 — Vista artista/creditos (balance + PaqueteCard + checkout redirect + HistorialTransacciones)
- [x] T9 — Página success (revalida balance con reintentos)
- [x] T10 — Página cancel
- [x] T11 — Tests (test_wallet_service.py 5 + test_creditos.py 8)

**Última sesión:** 2026-06-29 — Rama `fase-06` (desde main). T1: `src/services/wallet_service.py`
(`get_balance` on-demand transitorio; `_lock_wallet` con `INSERT … ON CONFLICT DO NOTHING` +
`SELECT FOR UPDATE`; `add_credits` idempotente por `referencia`; `deduct_credits` bloquea saldo<monto
con `InsufficientCreditsError`→409). Nueva excepción `InsufficientCreditsError` + mapeo 409 en
errors.py. Validado contra BD: +10/+10dup→10/-3→7/overdraft→409. ruff limpio.
**Próximo paso al reanudar:** **T8-T10** (frontend de créditos). Endpoints listos: GET /creditos/paquetes,
GET /creditos/balance, GET /creditos/historial, POST /creditos/checkout ({cantidad_creditos}→{checkout_url}).
- T8 `app/(dashboard)/artista/creditos/page.tsx`: balance prominente + PaqueteCard (botón Comprar →
  POST checkout → window.location = checkout_url) + HistorialTransacciones (server-paginated).
- T9 `app/(dashboard)/artista/creditos/success/page.tsx`: confirmación post-pago (revalida balance).
- T10 `app/(dashboard)/artista/creditos/cancel/page.tsx`.
Componentes PaqueteCard + HistorialTransacciones. Link "Créditos" del sidebar artista ya apunta a
/creditos — OJO: las páginas están bajo /artista/creditos; alinear el href del sidebar (cambiar a
/artista/creditos) o la ruta. Luego T11 (tests: webhook firma inválida 400, acreditación, idempotencia,
deduct insuficiente, balance sin wallet=0, curador checkout 403). Skill: frontend-skill (T8-T10),
testing-skill (T11). OJO: STRIPE_WEBHOOK_SECRET sigue placeholder (firma validada localmente).