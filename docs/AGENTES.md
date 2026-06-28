# AGENTES — Guía de modelos LLM por tipo de tarea · Resuena

> Esta guía aplica tanto a sesiones con **Claude Code** como con **OpenCode**.
> El objetivo: usar el modelo correcto para cada tarea, optimizando costo, latencia y calidad.

---

## Tabla maestra — Claude Code (Anthropic)

| Modelo | Cuándo usarlo | Ejemplos en este proyecto |
|--------|--------------|--------------------------|
| `claude-opus-4-7` | Arquitectura, decisiones cross-cutting, refactors complejos, debugging difícil, código que mezcla seguridad + concurrencia + datos | Fases 01 (infra), 02 (BD), 03 (auth), 05 (RBAC + aprobación), 06 (créditos + Stripe), 09 (flujo campañas + RabbitMQ), 10 (editor anti-IA) |
| `claude-sonnet-4-6` | Desarrollo de features (CRUDs, endpoints, vistas), code review, generación de tests, documentación técnica | Fases 04 (layout), 07 (géneros), 08 (campañas CRUD), 11 (entregas), 12 (balance), 13 (reportes), 14 (observabilidad), 15 (testing+docs) |
| `claude-haiku-4-5-20251001` | Tareas mecánicas: renombres masivos, formateo, generación de fixtures triviales, búsquedas exhaustivas en código | Tareas T menores dentro de cualquier fase: actualizar imports, agregar typings faltantes, regenerar Postman desde OpenAPI |

---

## Tabla maestra — OpenCode

| Modelo | Cuándo usarlo | Equivalente Claude |
|--------|--------------|-------------------|
| `o3-mini` | Razonamiento profundo, arquitectura, debugging complejo | ≈ `claude-opus-4-7` |
| `gpt-4o` | Features estándar, code review, documentación | ≈ `claude-sonnet-4-6` |
| `gpt-4o-mini` | Tareas mecánicas y búsqueda | ≈ `claude-haiku-4-5-...` |

---

## Criterios de selección

### Por complejidad del problema

| Complejidad | Indicador | Modelo Claude | Modelo OpenCode |
|-------------|-----------|--------------|----------------|
| **Alta** | Cruza ≥3 capas, involucra concurrencia/cifrado, requiere razonamiento de invariantes | `claude-opus-4-7` | `o3-mini` |
| **Media** | Una feature concreta, una vista, un CRUD, tests dirigidos | `claude-sonnet-4-6` | `gpt-4o` |
| **Baja** | Renombres, formateo, generación de stubs, búsqueda | `claude-haiku-4-5-...` | `gpt-4o-mini` |

### Por tipo de tarea

| Tipo | Modelo Claude | Modelo OpenCode |
|------|--------------|----------------|
| Diseño de arquitectura | `claude-opus-4-7` | `o3-mini` |
| Implementación de endpoint | `claude-sonnet-4-6` | `gpt-4o` |
| Implementación de vista | `claude-sonnet-4-6` | `gpt-4o` |
| Migración SQL / índices | `claude-opus-4-7` | `o3-mini` |
| Bug en producción crítico | `claude-opus-4-7` | `o3-mini` |
| Test unitario | `claude-sonnet-4-6` | `gpt-4o` |
| Refactor de un módulo aislado | `claude-sonnet-4-6` | `gpt-4o` |
| Refactor cross-module | `claude-opus-4-7` | `o3-mini` |
| Documentación (manual, README) | `claude-sonnet-4-6` | `gpt-4o` |
| Lógica de pagos / webhooks Stripe | `claude-opus-4-7` | `o3-mini` |
| Editor anti-IA (detección patrones escritura) | `claude-opus-4-7` | `o3-mini` |
| Flujo mensajería RabbitMQ + DLQ | `claude-opus-4-7` | `o3-mini` |
| Renombrar variable globalmente | `claude-haiku-4-5-...` | `gpt-4o-mini` |
| Generar fixtures / mocks triviales | `claude-haiku-4-5-...` | `gpt-4o-mini` |
| Búsqueda exhaustiva en código | `claude-haiku-4-5-...` | `gpt-4o-mini` |
| Revisión de seguridad | `claude-opus-4-7` | `o3-mini` |

---

## Modelo recomendado por fase (resumen)

| Fase | Título | Modelo principal | Notas |
|------|--------|-----------------|-------|
| 01 | Bootstrap + Infraestructura | `claude-opus-4-7` | Decisiones que afectan todo el resto |
| 02 | Modelo de datos + migraciones | `claude-opus-4-7` | Esquema irreversible una vez en prod |
| 03 | Autenticación (OTP, BCrypt, reset, dos roles) | `claude-opus-4-7` | Seguridad crítica + lógica de dos tipos de usuario |
| 04 | Layout + Perfiles de usuario | `claude-sonnet-4-6` | UI estándar + endpoints comunes |
| 05 | Admin Aprobación + RBAC | `claude-opus-4-7` | Permisos cruzados, flujo de aprobación multi-step |
| 06 | Créditos + Stripe | `claude-opus-4-7` | Lógica financiera + webhooks + idempotencia |
| 07 | Géneros + Categorías | `claude-sonnet-4-6` | CRUDs bien delimitados |
| 08 | Campañas — Creación + archivos | `claude-sonnet-4-6` | Upload multipart + validaciones |
| 09 | Flujo envío + Aceptar/Rechazar | `claude-opus-4-7` | RabbitMQ + devolución créditos + timers |
| 10 | Editor anti-IA para bloggers | `claude-opus-4-7` | Detección de patrones, algoritmos de scoring |
| 11 | Panel de entregas | `claude-sonnet-4-6` | Vistas + CRUD entregas |
| 12 | Balance + Retiros | `claude-sonnet-4-6` | Lógica financiera menos compleja que Stripe |
| 13 | Dashboard admin + Reportes | `claude-sonnet-4-6` | Dashboards y gráficas |
| 14 | Observabilidad | `claude-sonnet-4-6` | Patrones bien conocidos |
| 15 | Testing + CI/CD + Documentación | `claude-sonnet-4-6` | Volumen pero baja densidad de decisiones |

---

## Protocolo de handoff entre agentes distintos

Cuando cambies de modelo o agente (ej. de Opus a Sonnet, o de Claude Code a OpenCode), el contexto **no viaja en memoria** — viaja por los archivos del repo.

### Pasos al CERRAR sesión con el agente actual

1. Ejecuta el **PROMPT DE CIERRE DE SESIÓN** de `docs/SESION-TEMPLATE.md`.
2. Confirma que `docs/PLAN.md` (CHECKPOINT) y `docs/fase-XX.md` (PROGRESO) reflejan el estado real.
3. Si quedan decisiones pendientes que no son tareas, agrégalas en **"Notas de handoff"** al final de `docs/fase-XX.md`.
4. Si el código quedó en un estado intermedio que rompe el build, márcalo explícitamente.
5. Haz commit del estado.

### Pasos al ABRIR sesión con el agente nuevo

1. Ejecuta el **PROMPT DE INICIO DE SESIÓN** de `docs/SESION-TEMPLATE.md`.
2. Lee la sección "Notas de handoff" del `docs/fase-XX.md` activo.
3. Si las notas mencionan algo que no entiendes, **pregunta al usuario antes de codificar**.
4. Si el nuevo modelo es de capacidad menor y la tarea pendiente requiere razonamiento alto, **avisa al usuario**.

### Cuándo escalar el modelo

Si detectas alguna de estas señales, sube al modelo superior **antes de empezar**:
- La tarea cruza ≥3 fases distintas.
- Hay un bug reportado que ya intentaron resolver y volvió.
- La fase involucra pagos, concurrencia o transacciones distribuidas.
- El número de archivos a modificar es ≥15.
- El usuario expresó duda sobre el diseño actual.

### Cuándo bajar el modelo

- La sesión es solo para aplicar feedback de UI/UX puntual.
- Las tareas pendientes son renombres, imports, ajustes de typing.
- Solo falta documentación o tests triviales.

---

## Notas

- Los IDs de modelo evolucionan. Verifica los IDs vigentes en `https://docs.anthropic.com/en/docs/about-claude/models` antes de configurar herramientas que los referencien.
- Para OpenCode, los modelos disponibles dependen de los proveedores configurados.
- Cuando el costo importa más que la calidad marginal, prefiere los modelos inferiores.
