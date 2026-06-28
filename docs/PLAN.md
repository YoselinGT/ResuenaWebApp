# PLAN — Resuena · Plataforma de Gestión de Campañas Musicales

> **Stack:** FastAPI · Next.js 14 (App Router) · PostgreSQL · Redis · RabbitMQ · MailHog (dev)
> **Metodología:** Fases secuenciales con Claude Code / OpenCode — ver `docs/AGENTES.md`
> **Repositorio:** `resuena/`

---

## Tabla de Fases

| # | Fase                                                     | Estado | Días est. | Modelo | Dependencias |
|---|----------------------------------------------------------|--------|-----------|--------|--------------|
| 01 | Bootstrap + Infraestructura                              | `[x]` | 3 | `claude-opus-4-7` | — |
| 02 | Modelo de datos + migraciones PostgreSQL                 | `[x]` | 3 | `claude-opus-4-7` | 01 |
| 03 | Autenticación + Onboarding 9 pasos + login + OTP + reset | `[~]` | 5 | `claude-opus-4-7` | 02 |
| 04 | Layout Dashboard + Perfiles de usuario                   | `[ ]` | 3 | `claude-sonnet-4-6` | 03 |
| 05 | Admin — Aprobación de curadores + RBAC                   | `[ ]` | 4 | `claude-opus-4-7` | 04 |
| 06 | Sistema de créditos + Pasarela de pago (Stripe)          | `[ ]` | 4 | `claude-opus-4-7` | 05 |
| 07 | Géneros musicales + Configuración de categorías          | `[ ]` | 2 | `claude-sonnet-4-6` | 05 |
| 08 | Campañas musicales — Creación + carga de archivos        | `[ ]` | 4 | `claude-sonnet-4-6` | 06 07 |
| 09 | Flujo de envío + Aceptación / Rechazo de campañas        | `[ ]` | 4 | `claude-opus-4-7` | 08 |
| 10 | Editor de contenido para bloggers (anti-IA)              | `[ ]` | 4 | `claude-opus-4-7` | 09 |
| 11 | Panel de entregas (reels, links, HTML Blogger)           | `[ ]` | 3 | `claude-sonnet-4-6` | 10 |
| 12 | Sistema de balance + Solicitudes de retiro               | `[ ]` | 3 | `claude-sonnet-4-6` | 09 |
| 13 | Dashboard administrativo + Reportes                      | `[ ]` | 3 | `claude-sonnet-4-6` | 12 |
| 14 | Observabilidad + Sentry + Bitácora estructurada          | `[ ]` | 3 | `claude-sonnet-4-6` | 04 |
| 15 | Testing + CI/CD Bitbucket + Documentación                | `[ ]` | 4 | `claude-sonnet-4-6` | 14 |

---

## Módulos del Sistema

```
Resuena
├── Autenticación & Perfiles       (Fases 03-04)
│   ├── Artistas / Sellos discográficos
│   └── Curadores (playlists, blogs, redes, reels, radio) con N medios cada uno
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
Fecha último avance:      2026-06-27
Última fase tocada:       Fase 02 — Modelo de datos + migraciones (COMPLETADA, 9/9 tareas)
Último archivo modificado: docs/db/schema.md (T8)
Próxima acción al reanudar: Fase 03 — Autenticación + Onboarding 9 pasos + login + OTP + reset
                            (modelo claude-opus-4-7, skill security-skill).
Notas de handoff:         25 tablas + 13 enums + seeds (3 perfiles, 20 géneros, 8 idiomas,
                          20 regiones, 7 params) aplicados con `alembic upgrade head`. Ciclo de
                          rollback idempotente validado. Migraciones 0001 (schema+catálogos) y
                          0002 (seed). Doc en docs/db/schema.md.
                          OJO: el stack `portal-vendedores` ocupa puertos (8025 MailHog choca);
                          MailHog de Resuena queda detenido. Para liberar: detener portal-vendedores.
```
