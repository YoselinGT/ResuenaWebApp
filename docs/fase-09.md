# Fase 09 — Flujo de envío + Aceptación / Rechazo de campañas

> **Estado:** `[ ]` pendiente · **Días estimados:** 4 · **Modelo:** `claude-opus-4-7`
> **Skills:** `developer-skill`, `dba-skill`
> **Pre-requisitos:** Fase 08 `[x]`

---

## Contexto

Esta fase implementa el **corazón del flujo de negocio**: una vez que la campaña es enviada, los curadores deben responder dentro de `dias_limite_respuesta` días (configurable, default 6). Este flujo es crítico porque involucra movimiento de créditos, timers y notificaciones.

Escenarios posibles por curador vinculado:
1. **Acepta** → retención de créditos permanece; el curador queda comprometido a entregar contenido.
2. **Rechaza** → crédito devuelto al artista; notificación al artista.
3. **No responde en plazo** → expiración automática, crédito devuelto al artista; notificación a ambas partes.
4. **Entrega el contenido** → crédito transferido al curador según comisión configurada (`comision_resuena_pct`, default 50%); artista puede revisar y aprobar.

El artista también puede **cancelar** una campaña (solo si está en estado `enviada` y ningún curador ha aceptado aún). Esto devuelve todos los créditos retenidos.

Patrón resiliente con **RabbitMQ** para la expiración automática: un mensaje con `x-message-ttl` se encola al enviar la campaña. Si el worker detecta que el curador sigue `pendiente` al procesar, ejecuta la expiración.

---

## Tareas

- [ ] **T1.** Endpoint `GET /curador/campanas`: el curador ve sus campañas pendientes/activas (paginado). Incluye audio embebido, imagen, descripción del artista.
- [ ] **T2.** Endpoint `GET /curador/campanas/:campana_medio_id`: detalle de la asignación con countdown del tiempo restante.
- [ ] **T3.** Endpoint `POST /curador/campanas/:campana_medio_id/aceptar`: cambia estado a `aceptada`. Notifica al artista por email. Bitácora.
- [ ] **T4.** Endpoint `POST /curador/campanas/:campana_medio_id/rechazar`: body opcional `{motivo}`. Devuelve exactamente `precio_snapshot` créditos al wallet del artista (nunca dinero). Crea transacción `devolucion`. Cambia estado a `rechazada`. Notifica artista. Bitácora.
- [ ] **T5.** Endpoint `POST /artista/campanas/:id/cancelar`: solo si ningún curador ha aceptado. Devuelve todos los créditos retenidos. Cambia estado campaña a `cancelada`. Bitácora.
- [ ] **T6.** Publisher RabbitMQ (`src/infra/rabbit_publisher.py`): publica mensaje de expiración en cola `campana.expiracion` con TTL = `dias_limite_respuesta * 86400 * 1000` ms.
- [ ] **T7.** Worker de expiración (`src/workers/expiracion_worker.py`): consume `campana.expiracion`, verifica si `campana_profesional.estado == 'pendiente'`, si sí: devuelve crédito, cambia a `expirada`, notifica artista y curador. DLQ: `campana.expiracion.dlq`.
- [ ] **T8.** Endpoint `POST /curador/campanas/:campana_medio_id/entregar`: body `{tipo, url_entrega?, contenido_html?}`. Valida según tipo. Crea registro en `entregas_contenido`. Cambia estado a `entregada`. Transfiere créditos al curador: `floor(precio_snapshot × (1 - comision_efectiva/100))` donde `comision_efectiva` = `comision_pct` del paquete (o `comision_resuena_pct` global si es NULL). Registra `monto_usd` en la transacción. Notifica artista. **Nunca procesa refunds de Stripe.**
- [ ] **T9.** Endpoint `POST /artista/campanas/:id/entregas/:entrega_id/aprobar`: artista aprueba entrega. Marca `aprobada_por_artista = true`. Bitácora.
- [ ] **T10.** Vista `(dashboard)/curador/campanas/page.tsx`: tabla de campañas con countdown, estado badge, acciones (Aceptar/Rechazar).
- [ ] **T11.** Vista `(dashboard)/curador/campanas/[id]/page.tsx`: reproductor de audio, info de campaña, countdown prominente, botones de acción + formulario de entrega (según tipo).
- [ ] **T12.** Actualizar vista `(dashboard)/artista/campanas/[id]/page.tsx`: sección de entregas recibidas con opción de aprobar.
- [ ] **T13.** Setup DLQ en RabbitMQ: declarar `campana.expiracion.dlq` vinculada con la cola principal.
- [ ] **T14.** Tests: aceptar campaña → estado correcto + email; rechazar → crédito devuelto; worker expira correctamente tras TTL simulado; entrega blogger sin html → 422; transferencia de crédito con comisión correcta.

---

## Archivos a crear

| Ruta | |
|------|-|
| `src/api/curador_campanas.py` | |
| `src/api/artista_campanas_acciones.py` | |
| `src/services/campana_flujo_service.py` | |
| `src/infra/rabbit_publisher.py` | |
| `src/infra/rabbit_topology.py` | colas + DLX idempotente |
| `src/workers/expiracion_worker.py` | |
| `app/(dashboard)/curador/campanas/page.tsx` | |
| `app/(dashboard)/curador/campanas/[id]/page.tsx` | |
| `components/campanas/CountdownTimer.tsx` | |
| `components/campanas/EntregaForm.tsx` | |
| `tests/integration/test_campana_flujo.py` | |
| `tests/unit/test_expiracion_worker.py` | |

---

## Tests / validaciones

- `POST /curador/campanas/:id/aceptar` sin cookie → 401.
- Artista acepta después de que curador ya rechazó → 409.
- Worker con `estado='aceptada'` → no hace nada (solo expira `pendiente`).
- Entrega de reel sin `url_entrega` → 422.
- Transferencia: crédito artista -0 (ya retenido), wallet curador: precio_snapshot × 50% (comision_resuena_pct=50), `creditos_transacciones` tiene 2 filas (retiro de retención + acreditación al curador).
- DLQ: worker falla 3 veces → mensaje aparece en `campana.expiracion.dlq`.

---

## Skill recomendado por tarea

- **T1-T5, T8, T9:** `developer-skill`.
- **T6, T7, T13:** `developer-skill` (mensajería RabbitMQ).
- **T10-T12:** `frontend-skill`.
- **T14:** `testing-skill`.

---

## PROGRESO

- [ ] T1 — GET /curador/campanas
- [ ] T2 — GET /curador/campanas/:id
- [ ] T3 — POST aceptar
- [ ] T4 — POST rechazar
- [ ] T5 — POST artista cancelar
- [ ] T6 — Publisher RabbitMQ
- [ ] T7 — Worker expiración + DLQ
- [ ] T8 — POST entregar
- [ ] T9 — POST artista aprobar entrega
- [ ] T10 — Vista curador campanas (lista)
- [ ] T11 — Vista curador campanas (detalle + entrega)
- [ ] T12 — Vista artista campanas (entregas recibidas)
- [ ] T13 — Setup DLQ
- [ ] T14 — Tests

**Última sesión:** —
**Próximo paso al reanudar:** T1 — endpoint `GET /curador/campanas` con guard `require_curador_aprobado`, paginado, ordenado por `fecha_limite ASC`.