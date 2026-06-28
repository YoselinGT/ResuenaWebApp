# Fase 12 — Sistema de balance + Solicitudes de retiro

> **Estado:** `[ ]` pendiente · **Días estimados:** 3 · **Modelo:** `claude-sonnet-4-6`
> **Skills:** `developer-skill`, `frontend-skill`
> **Pre-requisitos:** Fase 09 `[x]`

---

## Contexto

Los profesionales acumulan créditos en su wallet al entregar campañas. Cuando quieren convertir esos créditos a dinero real, deben solicitar un retiro. El admin gestiona las solicitudes manualmente (transfiere el dinero por el medio acordado y marca como pagado).

Reglas de negocio:
- Monto mínimo de retiro configurable (default: 5 créditos = $200 MXN considerando comisión).
- `saldo_pendiente_retiro` se incrementa cuando el profesional solicita retiro y se decrementa de `saldo_creditos`. Si el admin rechaza, se revierte.
- El admin puede marcar como pagado indicando el método de pago real (SPEI, PayPal, etc.).
- El profesional recibe notificación en cada cambio de estado de su solicitud.

---

## Tareas

- [ ] **T1.** Endpoint `GET /profesional/balance`: retorna `{saldo_creditos, saldo_pendiente_retiro, historial_reciente[]}`.
- [ ] **T2.** Endpoint `POST /profesional/retiro`: body `{monto_creditos, metodo_pago: {tipo, datos}}`. Valida monto mínimo y que no supere `saldo_creditos - saldo_pendiente_retiro`. Mueve créditos a `saldo_pendiente_retiro`. Crea `solicitudes_retiro`. Notifica admin por email.
- [ ] **T3.** Endpoint `GET /admin/retiros`: lista de solicitudes paginada, filtrable por estado. Solo Admin.
- [ ] **T4.** Endpoint `POST /admin/retiros/:id/aprobar`: body `{notas_admin?, comprobante_url?}`. Marca como `pagada`. Notifica al profesional.
- [ ] **T5.** Endpoint `POST /admin/retiros/:id/rechazar`: body `{motivo}`. Revierte `saldo_pendiente_retiro` → `saldo_creditos`. Notifica al profesional con motivo.
- [ ] **T6.** Vista `(dashboard)/profesional/balance/page.tsx`: balance prominente (créditos disponibles + pendientes de retiro). Formulario de solicitud de retiro. Historial de solicitudes con estado badge.
- [ ] **T7.** Vista `(dashboard)/admin/retiros/page.tsx`: tabla de solicitudes con acciones Aprobar/Rechazar + modal de confirmación.
- [ ] **T8.** Tests: retiro con monto mayor al disponible → 422; aprobación → `saldo_pendiente_retiro` cero para esa solicitud; rechazo → créditos revertidos.

---

## Archivos a crear

| Ruta | |
|------|-|
| `src/api/retiros.py` | |
| `src/services/retiro_service.py` | |
| `app/(dashboard)/profesional/balance/page.tsx` | |
| `app/(dashboard)/admin/retiros/page.tsx` | |
| `components/balance/RetiroForm.tsx` | |
| `components/balance/SolicitudRetiroCard.tsx` | |
| `tests/integration/test_retiros.py` | |

---

## Tests / validaciones

- `POST /profesional/retiro` con `monto > saldo_disponible` → 422.
- Dos solicitudes activas simultáneas superando el saldo → segunda rechazada.
- `POST /admin/retiros/:id/rechazar` → `saldo_creditos` restaurado exactamente.
- Admin que intenta aprobar solicitud ya pagada → 409.

---

## PROGRESO

- [ ] T1 — GET /profesional/balance
- [ ] T2 — POST /profesional/retiro
- [ ] T3 — GET /admin/retiros
- [ ] T4 — POST aprobar
- [ ] T5 — POST rechazar
- [ ] T6 — Vista profesional balance
- [ ] T7 — Vista admin retiros
- [ ] T8 — Tests

**Última sesión:** —
**Próximo paso al reanudar:** T1 — endpoint `GET /profesional/balance` con guard `require_profesional_aprobado`.
