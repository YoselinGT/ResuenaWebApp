# PLAN — Resuena · Plataforma de Gestión de Campañas Musicales

> **Stack:** FastAPI · Next.js 14 (App Router) · PostgreSQL · Redis · RabbitMQ · MailHog (dev)
> **Metodología:** Fases secuenciales con Claude Code / OpenCode — ver `docs/AGENTES.md`
> **Repositorio:** `resuena/`

---

## Tabla de Fases

| # | Fase | Estado | Días est. | Modelo | Dependencias |
|---|------|--------|-----------|--------|--------------|
| 01 | Bootstrap + Infraestructura | `[x]` | 3 | `claude-opus-4-7` | — |
| 02 | Modelo de datos + migraciones PostgreSQL | `[~]` | 3 | `claude-opus-4-7` | 01 |
| 03 | Autenticación (registro artista/profesional + login + OTP + reset) | `[ ]` | 4 | `claude-opus-4-7` | 02 |
| 04 | Layout Dashboard + Perfiles de usuario | `[ ]` | 3 | `claude-sonnet-4-6` | 03 |
| 05 | Admin — Aprobación de profesionales + RBAC | `[ ]` | 4 | `claude-opus-4-7` | 04 |
| 06 | Sistema de créditos + Pasarela de pago (Stripe) | `[ ]` | 4 | `claude-opus-4-7` | 05 |
| 07 | Géneros musicales + Configuración de categorías | `[ ]` | 2 | `claude-sonnet-4-6` | 05 |
| 08 | Campañas musicales — Creación + carga de archivos | `[ ]` | 4 | `claude-sonnet-4-6` | 06 07 |
| 09 | Flujo de envío + Aceptación / Rechazo de campañas | `[ ]` | 4 | `claude-opus-4-7` | 08 |
| 10 | Editor de contenido para bloggers (anti-IA) | `[ ]` | 4 | `claude-opus-4-7` | 09 |
| 11 | Panel de entregas (reels, links, HTML Blogger) | `[ ]` | 3 | `claude-sonnet-4-6` | 10 |
| 12 | Sistema de balance + Solicitudes de retiro | `[ ]` | 3 | `claude-sonnet-4-6` | 09 |
| 13 | Dashboard administrativo + Reportes | `[ ]` | 3 | `claude-sonnet-4-6` | 12 |
| 14 | Observabilidad + Sentry + Bitácora estructurada | `[ ]` | 3 | `claude-sonnet-4-6` | 04 |
| 15 | Testing + CI/CD Bitbucket + Documentación | `[ ]` | 4 | `claude-sonnet-4-6` | 14 |

---

## Módulos del Sistema

```
Resuena
├── Autenticación & Perfiles       (Fases 03-04)
│   ├── Artistas / Sellos discográficos
│   └── Profesionales (bloggers, playlisters, influencers, reels)
├── Administración                 (Fases 05, 07, 13)
│   ├── Aprobación de profesionales
│   ├── Géneros y categorías
│   └── Dashboard + Reportes
├── Créditos & Pagos              (Fases 06, 12)
│   ├── Compra de créditos (Stripe)
│   ├── Wallet / balance
│   └── Solicitudes de retiro
├── Campañas Musicales            (Fases 08-09)
│   ├── Creación + material promocional
│   ├── Selección de profesionales
│   └── Flujo aceptar / rechazar (devolución automática)
├── Contenido & Entregas          (Fases 10-11)
│   ├── Editor anti-IA para bloggers
│   └── Panel de entregas (reels, links)
└── Infraestructura               (Fases 01-02, 14-15)
    ├── Docker + PostgreSQL + Redis + RabbitMQ
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
Última fase tocada:       Fase 01 — Bootstrap + Infraestructura (COMPLETADA, 12/12 tareas)
Último archivo modificado: docs/fase-01.md (cierre de fase)
Próxima acción al reanudar: Fase 02 — definir Base SQLAlchemy + conectar target_metadata en
                            alembic/env.py + primera migración autogenerada.
Notas de handoff:         Stack validado 7/7 con `docker compose up -d`. boto3 fijado a 1.35.74
                          (conflicto con aioboto3). Scaffold mínimo de Alembic ya creado.
                          OJO: el stack `portal-vendedores` se detuvo para liberar puertos;
                          reiniciarlo con `docker compose -p portal-vendedores start` si se necesita.
```
