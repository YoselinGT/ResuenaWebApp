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
| 06c | Migración retroactiva: precio_creditos en medios         | `[x]`  | 1 | `claude-opus-4-7`   | 06b   |
| 07  | Géneros musicales + Configuración de categorías          | `[ ]`  | 2 | `claude-sonnet-4-6` | 05    |
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
Fecha último avance:      2026-07-10
Última fase tocada:       Fase 06c — Migración retroactiva: precio_creditos en medios (COMPLETADA, 6/6)
Último archivo modificado: tests/integration/test_curador_medios.py (T6)
Próxima acción al reanudar: Fase 07 — Géneros musicales + Configuración de categorías
                            (modelo claude-sonnet-4-6, skill developer-skill).
Notas de handoff:         Fase 06c completa. Migración 0007_precio_medios.py agrega:
                          curador_medios.precio_creditos (INT NOT NULL DEFAULT 1, CHECK >=1),
                          curador_medios.descripcion_precio (VARCHAR 100 nullable),
                          campana_medios.precio_snapshot (INT NOT NULL DEFAULT 1),
                          creditos_transacciones.monto_usd (NUMERIC 10,2 nullable).
                          DTOs actualizados: MedioConStatsDTO, MedioCreateBody, MedioUpdateBody.
                          Service crear/editar persisten precio_creditos y descripcion_precio.
                          Modelos ORM actualizados: CuradorMedio, CampanaMedio, CreditoTransaccion.
                          5 tests nuevos en test_curador_medios.py (pasan individualmente,
                          fallas al correr en batch son pre-existentes por event loop de asyncpg).
```
