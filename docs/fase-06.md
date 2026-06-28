# Fase 06 — Sistema de créditos + Pasarela de pago (Stripe)

> **Estado:** `[ ]` pendiente · **Días estimados:** 4 · **Modelo:** `claude-opus-4-7`
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

- [ ] **T1.** Servicio `wallet_service.py`: `get_balance(usuario_id)`, `add_credits(usuario_id, monto, descripcion, ref)`, `deduct_credits(usuario_id, monto, descripcion, ref)`. Todas las operaciones atómicas con bloqueo de fila (`SELECT FOR UPDATE`).
- [ ] **T2.** Servicio `stripe_service.py`: `create_checkout_session(usuario_id, cantidad_creditos)` → crea Stripe Checkout Session en modo test. `handle_webhook(payload, signature)` → procesa `checkout.session.completed`.
- [ ] **T3.** Endpoint `GET /creditos/paquetes`: retorna lista de paquetes disponibles (5, 10, 20, 50 créditos con precio por paquete). Configurable desde `parametros_config`.
- [ ] **T4.** Endpoint `POST /creditos/checkout`: crea Stripe Checkout Session, retorna `{checkout_url}`. Artistas únicamente.
- [ ] **T5.** Endpoint `POST /creditos/webhook` (sin auth JWT): recibe webhook de Stripe, verifica firma `stripe-signature`, llama a `stripe_service.handle_webhook`. Si `checkout.session.completed`: acredita créditos al wallet del artista. Idempotente por `referencia_stripe`.
- [ ] **T6.** Endpoint `GET /creditos/balance`: retorna `{saldo_creditos, saldo_pendiente_retiro}` del usuario en sesión.
- [ ] **T7.** Endpoint `GET /creditos/historial`: transacciones paginadas del usuario (tipo, monto, descripción, fecha).
- [ ] **T8.** Vista `(dashboard)/artista/creditos/page.tsx`: balance prominente, lista de paquetes con botón "Comprar" (redirect a Stripe Checkout), historial de transacciones server-paginated.
- [ ] **T9.** Página `(dashboard)/artista/creditos/success/page.tsx`: pantalla de confirmación post-pago (Stripe redirige aquí). Revalida balance.
- [ ] **T10.** Página `(dashboard)/artista/creditos/cancel/page.tsx`: cancelación de pago.
- [ ] **T11.** Tests: compra simulada (webhook mock) → balance incrementa; deducción → saldo negativo bloqueado; idempotencia (mismo `referencia_stripe` dos veces → solo acredita una vez).

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

- [ ] T1 — wallet_service (operaciones atómicas)
- [ ] T2 — stripe_service (checkout + webhook handler)
- [ ] T3 — GET /creditos/paquetes
- [ ] T4 — POST /creditos/checkout
- [ ] T5 — POST /creditos/webhook
- [ ] T6 — GET /creditos/balance
- [ ] T7 — GET /creditos/historial
- [ ] T8 — Vista artista/creditos
- [ ] T9 — Página success
- [ ] T10 — Página cancel
- [ ] T11 — Tests

**Última sesión:** —
**Próximo paso al reanudar:** T1 — implementar `wallet_service.py` con `get_or_create_wallet`, `add_credits`, `deduct_credits` usando `SELECT FOR UPDATE` para atomicidad.
