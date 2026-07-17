# Fase 12 — Sistema de balance + Solicitudes de retiro

> **Estado:** `[ ]` pendiente · **Días estimados:** 3 · **Modelo:** `claude-sonnet-4-6`
> **Skills:** `developer-skill`, `frontend-skill`
> **Pre-requisitos:** Fase 09 `[x]`

---

## Contexto

Los curadores acumulan créditos en su wallet al entregar campañas. Cuando quieren convertir esos créditos a dinero real, deben solicitar un retiro. El admin gestiona las solicitudes manualmente (transfiere el dinero por el medio acordado y marca como pagado).

Reglas de negocio:
- **Mínimo de retiro: $50 USD** en valor de créditos acumulados. Todo en USD, sin MXN.
  Fórmula: `valor_credito_curador_usd = precio_credito_individual_usd × (1 - comision_resuena_pct/100)`
  Con defaults: `$2.00 × 0.50 = $1.00 USD/crédito`. Mínimo: 50 créditos.
- **Sin reembolso de dinero.** Los créditos que recibe el curador provienen de campañas entregadas. No hay refunds a Stripe.
- **Transferencia manual.** El admin transfiere el valor en USD al método acordado (PayPal, transferencia bancaria internacional). No hay Stripe Connect.
- `saldo_pendiente_retiro` se incrementa al solicitar y se decrementa de `saldo_creditos`. Si el admin rechaza, se revierte.
- El curador recibe notificación en cada cambio de estado.

---

## Tareas

- [ ] **T1.** Endpoint `GET /curador/balance`: retorna `{saldo_creditos, saldo_pendiente_retiro, valor_usd_aproximado, puede_retirar, minimo_creditos_equivalente, historial_reciente[]}`.
- [ ] **T2.** Endpoint `POST /curador/retiro`: body `{monto_creditos, metodo_pago: {tipo, datos}}`. Valida: (a) `monto_creditos × valor_credito_usd >= retiro_minimo_usd` (default $50 USD); (b) monto no supera `saldo_creditos - saldo_pendiente_retiro`. Si no alcanza el mínimo → 422 con mensaje claro indicando cuántos créditos más necesita. Mueve créditos a `saldo_pendiente_retiro`. Crea `solicitudes_retiro`. Notifica admin.
- [ ] **T3.** Endpoint `GET /admin/retiros`: lista de solicitudes paginada, filtrable por estado. Solo Admin.
- [ ] **T4.** Endpoint `POST /admin/retiros/:id/aprobar`: body `{notas_admin?, comprobante_url?}`. Marca como `pagada`. Notifica al curador.
- [ ] **T5.** Endpoint `POST /admin/retiros/:id/rechazar`: body `{motivo}`. Revierte `saldo_pendiente_retiro` → `saldo_creditos`. Notifica al curador con motivo.
- [ ] **T6.** Vista `(dashboard)/curador/balance/page.tsx`: balance prominente (créditos disponibles + pendientes de retiro). Formulario de solicitud de retiro. Historial de solicitudes con estado badge.
- [ ] **T7.** Vista `(dashboard)/admin/retiros/page.tsx`: tabla de solicitudes con acciones Aprobar/Rechazar + modal de confirmación.
- [ ] **T8.** Tests: retiro con monto mayor al disponible → 422; aprobación → `saldo_pendiente_retiro` cero para esa solicitud; rechazo → créditos revertidos.

---

## Archivos a crear

| Ruta | |
|------|-|
| `src/api/retiros.py` | |
| `src/services/retiro_service.py` | |
| `app/(dashboard)/curador/balance/page.tsx` | |
| `app/(dashboard)/admin/retiros/page.tsx` | |
| `components/balance/RetiroForm.tsx` | |
| `components/balance/SolicitudRetiroCard.tsx` | |
| `tests/integration/test_retiros.py` | |

---

## Tests / validaciones

- `POST /curador/retiro` con `monto > saldo_disponible` → 422.
- Dos solicitudes activas simultáneas superando el saldo → segunda rechazada.
- `POST /admin/retiros/:id/rechazar` → `saldo_creditos` restaurado exactamente.
- Admin que intenta aprobar solicitud ya pagada → 409.

---

## PROGRESO

- [ ] T1 — GET /curador/balance
- [ ] T2 — POST /curador/retiro
- [ ] T3 — GET /admin/retiros
- [ ] T4 — POST aprobar
- [ ] T5 — POST rechazar
- [ ] T6 — Vista curador balance
- [ ] T7 — Vista admin retiros
- [ ] T8 — Tests

**Última sesión:** —
**Próximo paso al reanudar:** T1 — endpoint `GET /curador/balance` con guard `require_curador_aprobado`.