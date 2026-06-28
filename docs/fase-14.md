# Fase 14 — Observabilidad + Sentry + Bitácora estructurada

> **Estado:** `[ ]` pendiente · **Días estimados:** 3 · **Modelo:** `claude-sonnet-4-6`
> **Skills:** `observability-logging-skill`, `developer-skill`
> **Pre-requisitos:** Fase 04 `[x]` (puede iniciar e ir instrumentando incrementalmente)

---

## Contexto

Esta fase unifica la observabilidad: structlog estructurado, correlation IDs propagados, captura de excepciones en Sentry y un visor de bitácora desde el admin.

Reglas:
- Cada request entra con `X-Correlation-Id` (si no llega, se genera UUID).
- Cada log incluye: `correlation_id`, `user_id?`, `route`, `method`, `latency_ms`, `status`.
- Errores de pago (Stripe webhook fallido), errores de S3 (upload/delete fallido), errores de RabbitMQ → reportados a Sentry con prioridad alta.
- Bitácora visible en `(dashboard)/admin/bitacora` con filtros.
- **Nunca** loguear: passwords, tokens completos, datos bancarios, contenido de reseñas en su totalidad.

---

## Tareas

- [ ] **T1.** Middleware `correlation.py` — extrae/genera `X-Correlation-Id` y lo guarda en `contextvars`.
- [ ] **T2.** Configurar structlog (`config/logging.py`) con processors JSON + nivel por env.
- [ ] **T3.** Middleware `request_logging.py` — loguea al final de cada request con timing, status, route.
- [ ] **T4.** Frontend: `lib/fetcher.ts` que genera UUID por request y envía `X-Correlation-Id`.
- [ ] **T5.** Integrar SDK Sentry en backend (`infra/sentry.py`) y frontend stub (`lib/sentry-client.ts`). `send_default_pii=False`.
- [ ] **T6.** Alertas en Sentry: error rate >5%, latencia p95 >2s, webhooks Stripe fallidos, mensajes en DLQ.
- [ ] **T7.** Reglas de redacción (`docs/observability/redaction-rules.md`): tabla de datos prohibidos en logs.
- [ ] **T8.** Endpoint `GET /admin/bitacora` paginado con filtros (autor, accion, fecha, correlation_id). Solo Admin.
- [ ] **T9.** Vista `(dashboard)/admin/bitacora/page.tsx`: tabla read-only con drill-down al detalle JSON.
- [ ] **T10.** Auditar que cada acción crítica (login, aprobación profesional, compra créditos, pago Stripe, envío campaña, entrega, retiro) tiene su entrada en bitácora.
- [ ] **T11.** Rate limiting global: 100 req/min por IP con `slowapi`. Excepciones para `/health` y `/creditos/webhook`.
- [ ] **T12.** Bloqueo por IP: 404 repetidos (>10 en 24h) → IP a `ips_bloqueadas`. Middleware `ip_block.py` verifica en Redis.

---

## Archivos a crear

| Ruta | |
|------|-|
| `src/middleware/correlation.py` | |
| `src/middleware/request_logging.py` | |
| `src/middleware/ip_block.py` | |
| `src/middleware/rate_limit.py` | |
| `src/config/logging.py` | |
| `src/infra/sentry.py` | |
| `src/services/ip_tracker.py` | |
| `src/api/bitacora.py` | |
| `src/services/bitacora_query_service.py` | |
| `lib/fetcher.ts` | |
| `lib/sentry-client.ts` | |
| `app/(dashboard)/admin/bitacora/page.tsx` | |
| `components/admin/BitacoraDetailModal.tsx` | |
| `docs/observability/redaction-rules.md` | |

---

## Tests / validaciones

- Request desde frontend → ambos logs (FE + BE) muestran el mismo `correlation_id`.
- `grep "password"` en logs → 0 resultados con valores reales.
- IP con 11 hits a ruta inexistente → 403 en el 12°.
- 101 requests rápidos a `/health` → 429 en el 101°.
- Bitácora contiene `compra_creditos`, `aprobacion_profesional`, `envio_campana`.

---

## PROGRESO

- [ ] T1 — Middleware correlation
- [ ] T2 — Config structlog
- [ ] T3 — Middleware request_logging
- [ ] T4 — lib/fetcher.ts
- [ ] T5 — Sentry backend + frontend stub
- [ ] T6 — Alertas Sentry
- [ ] T7 — Reglas de redacción
- [ ] T8 — GET /admin/bitacora
- [ ] T9 — Vista bitácora admin
- [ ] T10 — Auditoría de cobertura bitácora
- [ ] T11 — Rate limiting
- [ ] T12 — IP blocking

**Última sesión:** —
**Próximo paso al reanudar:** T1 — middleware `correlation.py` ASGI puro que extrae/genera UUID y lo inyecta en structlog contextvars y en header de respuesta.
