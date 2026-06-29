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
| 04 | Layout Dashboard + Perfiles de usuario                   | `[x]` | 3 | `claude-sonnet-4-6` | 03 |
| 05 | Admin — Aprobación de curadores + RBAC                   | `[~]` | 4 | `claude-opus-4-7` | 04 |
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
Fecha último avance:      2026-06-29
Última fase tocada:       Fase 04 — Layout Dashboard + Perfiles (COMPLETADA, 13/13 tareas)
Último archivo modificado: tests/integration/test_users_me.py (T13)
Próxima acción al reanudar: Fase 05 — Admin: Aprobación de curadores + RBAC
                            (modelo claude-opus-4-7, skill security-skill).
Notas de handoff:         Fase 04 completa. Shell de dashboard: `app/(dashboard)/layout.tsx`
                          (Server Component, guard vía /auth/me → redirect /login), Sidebar
                          (rail desktop + overlay móvil Framer Motion, menú por tipo, store
                          zustand `useSidebar`), Header + UserMenu + Avatar (logout). Home con
                          KPI por tipo. mi-perfil con PhotoUploader. Backend: GET/PATCH /users/me
                          (sanitize XSS + bitácora con diff; sello OMITIDO por decisión),
                          POST/DELETE /users/me/photo (libmagic JPEG + Pillow 200×200 →
                          perfiles-avatar/<id>.jpg; foto_path guarda la CLAVE), GET /config/public
                          (migración 0004, head de alembic = 0004). StorageService
                          (Protocol+S3Provider aioboto3 SigV4+factory) en src/infra/storage.py;
                          setting AWS_PUBLIC_ENDPOINT_URL=http://localhost:4566 para presigned
                          alcanzables desde el navegador en dev. lib/api ganó patch+upload;
                          lib/server-api.ts para Server Components. Redirect post-login/OTP/
                          onboarding → /home. Tests: 43 passed (11 nuevos, provider stub vía
                          dependency override). Correr: `docker compose exec -e TESTING=1 api pytest`.
                          OJO: configs frontend montados en contenedor app (tras editarlos:
                          `docker compose up -d --force-recreate app`). api recreado para activar
                          AWS_PUBLIC_ENDPOINT_URL.
                          OJO (heredado): `portal-vendedores` choca en 8025 (MailHog).
                          DEUDA: (1) sello como entidad propia pendiente (sello_discografico
                          omitido en perfil); (2) onboarding sin GET de selecciones previas de
                          géneros/idiomas/regiones (el wizard no pre-rellena al revisitar).
```
