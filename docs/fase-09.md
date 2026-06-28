# Fase 09 — Flujo de envío + Aceptación / Rechazo de campañas

> **Estado:** `[ ]` pendiente · **Días estimados:** 4 · **Modelo:** `claude-opus-4-7`
> **Skills:** `developer-skill`, `dba-skill`
> **Pre-requisitos:** Fase 08 `[x]`

---

## Contexto

Esta fase implementa el **corazón del flujo de negocio**: una vez que la campaña es enviada, los profesionales deben responder dentro de `dias_limite_respuesta` días (configurable, default 6). Este flujo es crítico porque involucra movimiento de créditos, timers y notificaciones.

Escenarios posibles por profesional vinculado:
1. **Acepta** → retención de créditos permanece; el profesional queda comprometido a entregar contenido.
2. **Rechaza** → crédito devuelto al artista; notificación al artista.
3. **No responde en plazo** → expiración automática, crédito devuelto al artista; notificación a ambas partes.
4. **Entrega el contenido** → crédito transferido al profesional (menos comisión); artista puede revisar y aprobar.

El artista también puede **cancelar** una campaña (solo si está en estado `enviada` y ningún profesional ha aceptado aún). Esto devuelve todos los créditos retenidos.

Patrón resiliente con **RabbitMQ** para la expiración automática: un mensaje con `x-message-ttl` se encola al enviar la campaña. Si el worker detecta que el profesional sigue `pendiente` al procesar, ejecuta la expiración.

---

## Tareas

- [ ] **T1.** Endpoint `GET /profesional/campanas`: el profesional ve sus campañas pendientes/activas (paginado). Incluye audio embebido, imagen, descripción del artista.
- [ ] **T2.** Endpoint `GET /profesional/campanas/:campana_profesional_id`: detalle de la asignación con countdown del tiempo restante.
- [ ] **T3.** Endpoint `POST /profesional/campanas/:campana_profesional_id/aceptar`: cambia estado a `aceptada`. Notifica al artista por email. Bitácora.
- [ ] **T4.** Endpoint `POST /profesional/campanas/:campana_profesional_id/rechazar`: body opcional `{motivo}`. Devuelve crédito al artista (`wallet_service.add_credits`). Cambia estado a `rechazada`. Notifica artista. Bitácora.
- [ ] **T5.** Endpoint `POST /artista/campanas/:id/cancelar`: solo si ningún profesional ha aceptado. Devuelve todos los créditos retenidos. Cambia estado campaña a `cancelada`. Bitácora.
- [ ] **T6.** Publisher RabbitMQ (`src/infra/rabbit_publisher.py`): publica mensaje de expiración en cola `campana.expiracion` con TTL = `dias_limite_respuesta * 86400 * 1000` ms.
- [ ] **T7.** Worker de expiración (`src/workers/expiracion_worker.py`): consume `campana.expiracion`, verifica si `campana_profesional.estado == 'pendiente'`, si sí: devuelve crédito, cambia a `expirada`, notifica artista y profesional. DLQ: `campana.expiracion.dlq`.
- [ ] **T8.** Endpoint `POST /profesional/campanas/:campana_profesional_id/entregar`: body `{tipo, url_entrega?, contenido_html?}`. Valida según tipo (blogger requiere contenido_html, reel requiere url_entrega, etc.). Crea registro en `entregas_contenido` con `puntuacion_autenticidad = null` (se calcula en Fase 10). Cambia estado a `entregada`. Transfiere crédito al profesional menos comisión. Notifica artista.
- [ ] **T9.** Endpoint `POST /artista/campanas/:id/entregas/:entrega_id/aprobar`: artista aprueba entrega. Marca `aprobada_por_artista = true`. Bitácora.
- [ ] **T10.** Vista `(dashboard)/profesional/campanas/page.tsx`: tabla de campañas con countdown, estado badge, acciones (Aceptar/Rechazar).
- [ ] **T11.** Vista `(dashboard)/profesional/campanas/[id]/page.tsx`: reproductor de audio, info de campaña, countdown prominente, botones de acción + formulario de entrega (según tipo).
- [ ] **T12.** Actualizar vista `(dashboard)/artista/campanas/[id]/page.tsx`: sección de entregas recibidas con opción de aprobar.
- [ ] **T13.** Setup DLQ en RabbitMQ: declarar `campana.expiracion.dlq` vinculada con la cola principal.
- [ ] **T14.** Tests: aceptar campaña → estado correcto + email; rechazar → crédito devuelto; worker expira correctamente tras TTL simulado; entrega blogger sin html → 422; transferencia de crédito con comisión correcta.

---

## Archivos a crear

| Ruta | |
|------|-|
| `src/api/profesional_campanas.py` | |
| `src/api/artista_campanas_acciones.py` | |
| `src/services/campana_flujo_service.py` | |
| `src/infra/rabbit_publisher.py` | |
| `src/infra/rabbit_topology.py` | colas + DLX idempotente |
| `src/workers/expiracion_worker.py` | |
| `app/(dashboard)/profesional/campanas/page.tsx` | |
| `app/(dashboard)/profesional/campanas/[id]/page.tsx` | |
| `components/campanas/CountdownTimer.tsx` | |
| `components/campanas/EntregaForm.tsx` | |
| `tests/integration/test_campana_flujo.py` | |
| `tests/unit/test_expiracion_worker.py` | |

---

## Tests / validaciones

- `POST /profesional/campanas/:id/aceptar` sin cookie → 401.
- Artista acepta después de que profesional ya rechazó → 409.
- Worker con `estado='aceptada'` → no hace nada (solo expira `pendiente`).
- Entrega de reel sin `url_entrega` → 422.
- Transferencia: crédito artista -0 (ya retenido), wallet profesional +0.8 (80% con comisión 20%), `creditos_transacciones` tiene 2 filas (retiro de retención + acreditación al profesional).
- DLQ: worker falla 3 veces → mensaje aparece en `campana.expiracion.dlq`.

---

## Skill recomendado por tarea

- **T1-T5, T8, T9:** `developer-skill`.
- **T6, T7, T13:** `developer-skill` (mensajería RabbitMQ).
- **T10-T12:** `frontend-skill`.
- **T14:** `testing-skill`.

---

## PROGRESO

- [ ] T1 — GET /profesional/campanas
- [ ] T2 — GET /profesional/campanas/:id
- [ ] T3 — POST aceptar
- [ ] T4 — POST rechazar
- [ ] T5 — POST artista cancelar
- [ ] T6 — Publisher RabbitMQ
- [ ] T7 — Worker expiración + DLQ
- [ ] T8 — POST entregar
- [ ] T9 — POST artista aprobar entrega
- [ ] T10 — Vista profesional campanas (lista)
- [ ] T11 — Vista profesional campanas (detalle + entrega)
- [ ] T12 — Vista artista campanas (entregas recibidas)
- [ ] T13 — Setup DLQ
- [ ] T14 — Tests

**Última sesión:** —
**Próximo paso al reanudar:** T1 — endpoint `GET /profesional/campanas` con guard `require_profesional_aprobado`, paginado, ordenado por `fecha_limite ASC`.
