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
| 06  | Sistema de créditos + Pasarela de pago (Stripe)          | `[~]`  | 4 | `claude-opus-4-7` | 05    |
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
Fecha último avance:      2026-06-29
Última fase tocada:       Fase 05 — Admin: Aprobación de curadores + RBAC (COMPLETADA, 15/15)
Último archivo modificado: tests/integration/test_admin_solicitudes.py (T15)
Próxima acción al reanudar: Fase 06 — Sistema de créditos + Pasarela de pago (Stripe)
                            (modelo claude-opus-4-7, skill security-skill + developer-skill).
Notas de handoff:         Fase 05 completa en rama `fase-05` (desde main con 04b mergeada).
                          RBAC: src/middleware/roles.py (require_admin perfil 1, require_artista
                          perfil 2+activo, require_curador_aprobado perfil 3+activo+solicitud
                          aprobada; este último centralizado, curador_medios.py lo importa).
                          ADMIN backend (src/api/admin_solicitudes.py + admin_usuarios.py +
                          services/admin_service.py): GET /admin/solicitudes (filtros estado/tipo/
                          desde/hasta + paginación), GET /admin/solicitudes/{id} (con redes),
                          POST .../aprobar (email send_aprobacion + bitácora aprobacion_curador +
                          revisor_id), POST .../rechazar (body {motivo}→notas_revision, email
                          send_rechazo, bitácora rechazo_curador), GET /admin/usuarios (filtros),
                          PATCH /admin/usuarios/{id} ({nombre_completo?,activo?}; ignora correo/
                          pass; protege admin→403), POST /admin/usuarios/{id}/toggle-status.
                          FRONTEND: es_admin añadido a /auth/me + DashboardUser + Sidebar (menú
                          admin). Vistas app/(dashboard)/admin/solicitudes (lista + detalle [id]) y
                          admin/usuarios; componentes admin/SolicitudCard + RechazarModal; guards
                          (no-admin→/home; curador no aprobado→pantalla "en revisión" en /home).
                          Tests: 66 passed (10 nuevos: test_roles 4 + test_admin_solicitudes 6).
                          ruff(src+tests)+tsc limpios. Migraciones head = 0005 (sin cambios en F05).
                          OJO: crear admin = promover perfil_id=1 vía SQL + re-login (mint JWT con
                          perfil_id=1); NO hay auto-registro de admin. El helper make_admin en tests
                          hace exactamente eso.
                          OJO (heredado): portal-vendedores choca en 8025 (MailHog).
                          DEUDA: (1) sello_discografico texto en perfil omitido; (2) onboarding sin
                          GET de selecciones previas; (3) stats medios generos_frecuentes/tiempo +
                          "campañas como sello" → Fase 08.
```
