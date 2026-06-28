# Fase 13 — Dashboard administrativo + Reportes

> **Estado:** `[ ]` pendiente · **Días estimados:** 3 · **Modelo:** `claude-sonnet-4-6`
> **Skills:** `developer-skill`, `frontend-skill`, `dba-skill`
> **Pre-requisitos:** Fase 12 `[x]`

---

## Contexto

Esta fase entrega los dashboards y reportes de alto nivel para cada tipo de usuario.

**Admin:** visión global de la plataforma — campañas activas, profesionales pendientes de aprobación, retiros pendientes, métricas de conversión y volumen.

**Artista:** visión de sus campañas — tasa de aceptación por tipo de profesional, entregas recibidas, créditos gastados vs. contenido obtenido.

**Profesional:** visión de su actividad — campañas completadas, ingresos acumulados, puntuación promedio de autenticidad.

---

## Tareas

- [ ] **T1.** Endpoint `GET /admin/dashboard/kpis`: retorna `{usuarios_totales, artistas, profesionales_aprobados, profesionales_pendientes, campanas_activas, creditos_en_circulacion, retiros_pendientes_monto}`.
- [ ] **T2.** Endpoint `GET /admin/reports/campanas`: campañas paginadas con filtros (estado, genero, fecha_desde, fecha_hasta). Export CSV.
- [ ] **T3.** Endpoint `GET /admin/reports/profesionales`: rendimiento de profesionales — campañas aceptadas/rechazadas/expiradas, puntuación promedio autenticidad, balance acumulado.
- [ ] **T4.** Endpoint `GET /artista/dashboard/kpis`: `{campanas_activas, entregas_recibidas, entregas_aprobadas, creditos_disponibles, creditos_gastados_mes}`.
- [ ] **T5.** Endpoint `GET /artista/reports/campanas`: sus campañas con métricas de respuesta (tasa aceptación, tiempo promedio de respuesta).
- [ ] **T6.** Endpoint `GET /profesional/dashboard/kpis`: `{campanas_pendientes, campanas_completadas_mes, ingresos_mes, puntuacion_promedio}`.
- [ ] **T7.** Vista `(dashboard)/admin/page.tsx` (home del admin): grid de KPI cards + tabla de solicitudes pendientes + tabla de retiros pendientes.
- [ ] **T8.** Vista `(dashboard)/admin/reportes/page.tsx`: tablas exportables de campañas y profesionales con filtros.
- [ ] **T9.** Vista `(dashboard)/artista/page.tsx` (home artista): KPIs + gráfica de campañas por estado (Recharts donut) + lista de últimas campañas.
- [ ] **T10.** Vista `(dashboard)/profesional/page.tsx` (home profesional): KPIs + campañas pendientes de respuesta con countdown + ingresos del mes.
- [ ] **T11.** Componentes reutilizables: `KPICard`, `ExportButton` (CSV), `CampanaStatusChart` (Recharts).
- [ ] **T12.** Tests: KPIs retornan valores correctos según datos de prueba; export CSV con filtros produce datos correctos.

---

## Archivos a crear

| Ruta | |
|------|-|
| `src/api/dashboard.py` | |
| `src/api/reportes.py` | |
| `src/services/dashboard_service.py` | |
| `src/services/reportes_service.py` | |
| `app/(dashboard)/admin/page.tsx` | |
| `app/(dashboard)/admin/reportes/page.tsx` | |
| `app/(dashboard)/artista/page.tsx` | |
| `app/(dashboard)/profesional/page.tsx` | |
| `components/dashboard/KPICard.tsx` | |
| `components/dashboard/ExportButton.tsx` | |
| `components/dashboard/CampanaStatusChart.tsx` | |
| `tests/integration/test_dashboard.py` | |

---

## Tests / validaciones

- Admin sin campañas → todos los KPIs en 0, no error.
- Export CSV con filtro `genero=Rock` → solo campañas de Rock.
- KPI `creditos_en_circulacion` = suma de todos los `saldo_creditos` + `saldo_pendiente_retiro`.

---

## PROGRESO

- [ ] T1 — GET /admin/dashboard/kpis
- [ ] T2 — GET /admin/reports/campanas
- [ ] T3 — GET /admin/reports/profesionales
- [ ] T4 — GET /artista/dashboard/kpis
- [ ] T5 — GET /artista/reports/campanas
- [ ] T6 — GET /profesional/dashboard/kpis
- [ ] T7 — Vista admin home
- [ ] T8 — Vista admin reportes
- [ ] T9 — Vista artista home
- [ ] T10 — Vista profesional home
- [ ] T11 — Componentes reutilizables
- [ ] T12 — Tests

**Última sesión:** —
**Próximo paso al reanudar:** T1 — endpoint `GET /admin/dashboard/kpis` con guard `require_admin`.
