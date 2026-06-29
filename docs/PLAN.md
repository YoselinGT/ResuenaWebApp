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
| 03 | Autenticación + Onboarding 9 pasos + login + OTP + reset | `[x]` | 5 | `claude-opus-4-7` | 02 |
| 04 | Layout Dashboard + Perfiles de usuario                   | `[~]` | 3 | `claude-sonnet-4-6` | 03 |
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
Fecha último avance:      2026-06-28
Última fase tocada:       Fase 03 — Autenticación + Onboarding (COMPLETADA, 21/21 tareas)
Último archivo modificado: app/onboarding/completado/page.tsx (T22)
Próxima acción al reanudar: Fase 04 — Layout Dashboard + Perfiles de usuario
                            (modelo claude-sonnet-4-6, skill frontend-skill).
Notas de handoff:         Fase 03 backend (T1-T14, T16-T21) + frontend (T15, T22) completos y
                          validados. Frontend Next.js 14: sistema de diseño dark Resuena en
                          globals.css (#0f0c1f/#5c269c), Inter Variable self-hosted, assets en
                          public/brand. API consumida vía rewrite same-origin /api/* → api:8000
                          (next.config.mjs) para que la cookie HttpOnly+SameSite=Lax sea
                          first-party sin CORS. 8 vistas auth en app/(auth) (group → /login,
                          /registro/...), wizard en app/onboarding (segmento literal, porque
                          /auth/confirm redirige a /onboarding/generos). Validado por proxy con
                          sesión real: register→confirm→me + flujo curador 5/5 pasos.
                          OJO: configs del frontend (next.config.mjs, tailwind.config.ts,
                          postcss.config.mjs, tsconfig.json) ahora montados en el contenedor app;
                          tras editarlos: `docker compose up -d --force-recreate app`. tsc limpio.
                          OJO (heredado): el stack `portal-vendedores` choca en 8025 (MailHog).
                          Para liberar: detener portal-vendedores.
                          DEUDA: falta GET de selecciones previas de géneros/idiomas/regiones en
                          onboarding (solo flags en /onboarding/progreso) — el wizard no pre-rellena
                          esos pasos al revisitarlos.
```
