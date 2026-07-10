# PLAN — Resuena · Plataforma de Gestión de Campañas Musicales

> **Stack:** FastAPI · Next.js 14 (App Router) · PostgreSQL · Redis · RabbitMQ · MailHog (dev)
> **Metodología:** Fases secuenciales con Claude Code / OpenCode — ver `docs/AGENTES.md`
> **Repositorio:** `resuena/`

---

## Tabla de Fases

| #   | Fase                                                     | Estado | Días est. | Modelo | Dependencias |
|-----|----------------------------------------------------------|--------|-----------|--------|-------|
| 01  | Bootstrap + Infraestructura                              | `[x]`  | 3 | `claude-opus-4-7` | —     |
| 02  | Modelo de datos + migraciones PostgreSQL                 | `[x]`  | 3 | `claude-opus-4-7` | 01    |
| 03  | Autenticación + Onboarding 9 pasos + login + OTP + reset | `[x]`  | 5 | `claude-opus-4-7` | 02    |
| 04  | Layout Dashboard + Perfiles de usuario                   | `[x]`  | 3 | `claude-sonnet-4-6` | 03    |
| 04b | Sellos discográficos + Gestión de medios del curador     | `[x]`  | 3 | `claude-sonnet-4-6` | 03 04 |
| 05  | Admin — Aprobación de curadores + RBAC                   | `[x]`  | 4 | `claude-opus-4-7` | 04    |
| 06  | Sistema de créditos + Pasarela de pago (Stripe)          | `[x]`  | 4 | `claude-opus-4-7` | 05    |
| 06b | Admin: Gestión de paquetes de créditos (Stripe USD)      | `[x]`  | 2 | `claude-sonnet-4-6` | 02 06 |
| 07  | Géneros musicales + Configuración de categorías          | `[~]`  | 2 | `claude-sonnet-4-6` | 05    |
| 08  | Campañas musicales — Creación + carga de archivos        | `[ ]`  | 4 | `claude-sonnet-4-6` | 06 07 |
| 09  | Flujo de envío + Aceptación / Rechazo de campañas        | `[ ]`  | 4 | `claude-opus-4-7` | 08    |
| 10  | Editor de contenido para bloggers (anti-IA)              | `[ ]`  | 4 | `claude-opus-4-7` | 09    |
| 11  | Panel de entregas (reels, links, HTML Blogger)           | `[ ]`  | 3 | `claude-sonnet-4-6` | 10    |
| 12  | Sistema de balance + Solicitudes de retiro               | `[ ]`  | 3 | `claude-sonnet-4-6` | 09    |
| 13  | Dashboard administrativo + Reportes                      | `[ ]`  | 3 | `claude-sonnet-4-6` | 12    |
| 14  | Observabilidad + Sentry + Bitácora estructurada          | `[ ]`  | 3 | `claude-sonnet-4-6` | 04    |
| 15  | Testing + CI/CD Bitbucket + Documentación                | `[ ]`  | 4 | `claude-sonnet-4-6` | 14    |

---

## Módulos del Sistema

```
Resuena
├── Autenticación & Perfiles       (Fases 03-04-04b)
│   ├── Artistas (independientes o bajo un sello)
│   ├── Sellos discográficos (N artistas por sello, roles: owner/manager/artista)
│   ├── Curadores con N medios de difusión independientes
├── Administración                 (Fases 05, 07, 13)
│   ├── Aprobación de curadores
│   ├── Géneros y categorías
│   └── Dashboard + Reportes
├── Créditos & Pagos              (Fases 06, 12)
│   ├── Compra de créditos (Stripe)
│   ├── Wallet / balance
│   └── Solicitudes de retiro
├── Campañas Musicales            (Fases 08-09)
│   ├── Creación + material promocional
│   ├── Selección de curadores
│   └── Flujo aceptar / rechazar (devolución automática)
├── Contenido & Entregas          (Fases 10-11)
│   ├── Editor anti-IA para bloggers
│   └── Panel de entregas (reels, links)
└── Infraestructura               (Fases 01-02, 14-15)
    ├── Docker + PostgreSQL + Redis + RabbitMQ
    ├── Sistema de diseño dark mode (paleta #0f0c1f/#5c269c, ondas de sonido)
    ├── Almacenamiento en nube — S3 (prod) / LocalStack (dev)
    │   └── Abstracción StorageProvider: S3Provider activo,
    │       preparado para GCS/Azure sin cambios de código
    ├── Observabilidad (structlog + Sentry)
    └── CI/CD Bitbucket + Testing
```

---

## Convenciones de estado

- `[ ]` — pendiente
- `[~]` — en progreso (fase activa)
- `[x]` — completada
- `[!]` — bloqueada (indica dependencia sin resolver)

---

## CHECKPOINT

```
Fecha último avance:      2026-07-07
Última fase tocada:       Fase 06b — Admin: Gestión de paquetes de créditos (Stripe USD) (COMPLETADA, 17/17)
Último archivo modificado: tests/integration/test_admin_paquetes.py (T17)
Próxima acción al reanudar: Fase 07 — Géneros musicales + Configuración de categorías
                            (modelo claude-sonnet-4-6, skill developer-skill).
Notas de handoff:         Fase 06b completa. CREA tablas paquetes_creditos (UUID PK, nombre,
                          cantidad_creditos, precio_total_usd NUMERIC, comision_pct INT nullable,
                          descripcion, activo, visible, destacado, timestamps). Seed 9 params
                          Stripe/USD en parametros_config. Servicio paquetes_service.py con
                          calcular_precio_artista (fórmula despejada por escenario), calcular_campos
                          (campos derivados NUNCA en BD), CRUD completo. Endpoints admin:
                          GET/POST/PATCH /admin/paquetes, GET/PATCH /admin/config/creditos.
                          stripe_service.py migrado a price_data dinámico USD (unit_amount en
                          centavos, currency=usd, metadata con paquete_id/cantidad/precio_neto).
                          webhook lee metadata.cantidad_creditos. Frontend: admin/paquetes page
                          (ConfigGlobalCard + NuevoPaqueteForm + PaqueteCard), artista/creditos
                          page actualizada a USD con ConfirmarCompraModal + disclaimer de fees.
                          Tests: 6 integration + 5 unit. Archivos nuevos: alembic/versions/
                          0006_paquetes_usd.py, src/models/paquetes_creditos.py, src/models/dto/
                          paquetes.py, src/services/paquetes_service.py, src/api/admin_paquetes.py,
                          hooks/usePaqueteCard.ts, components/admin/ConfigGlobalCard.tsx,
                          components/admin/NuevoPaqueteForm.tsx, components/admin/PaqueteCard.tsx,
                          components/creditos/ConfirmarCompraModal.tsx, tests/integration/
                          test_admin_paquetes.py, tests/unit/test_paquetes_service.py.
```
