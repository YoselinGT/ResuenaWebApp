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
| 05  | Admin — Aprobación de curadores + RBAC                   | `[~]`  | 4 | `claude-opus-4-7` | 04    |
| 06  | Sistema de créditos + Pasarela de pago (Stripe)          | `[ ]`  | 4 | `claude-opus-4-7` | 05    |
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
Última fase tocada:       Fase 04b — Sellos + Gestión de medios (COMPLETADA, 26/26 tareas)
Último archivo modificado: tests/integration/test_curador_medios.py (T26)
Próxima acción al reanudar: Fase 05 — Admin: Aprobación de curadores + RBAC
                            (modelo claude-opus-4-7, skill security-skill).
Notas de handoff:         Fase 04b completa en rama `fase-04b` (derivada de `fase-04`).
                          SELLOS (backend src/api/sellos.py + src/services/sello_service.py):
                          POST /sellos (multipart+logo, owner en sello_artistas, invariante 1
                          sello activo/artista), GET /sellos/mio, GET /sellos/{id}/artistas,
                          PATCH /sellos/{id} (guard _require_rol owner/manager), invitar/aceptar/
                          rechazar (tabla invitaciones_sello, migración 0005; GET /sellos/invitacion/
                          {token} lee sin consumir), transferir-ownership, salir (único owner→409),
                          DELETE miembro (soft-delete). MEDIOS (src/api/curador_medios.py +
                          curador_medios_service.py): GET/POST (guard require_curador_aprobado) /
                          PATCH / toggle-activo (409 si campañas pendiente|aceptada) / stats. Util
                          compartida src/utils/images.py (process_jpeg_square; user_service refactor).
                          FRONTEND: app/(dashboard)/artista/sello/* + curador/medios/* + componentes
                          en components/sellos y components/curador; links sidebar "Mi sello"/"Mis
                          medios"; secciones en mi-perfil. Migraciones head = 0005. Tests: 56 passed
                          (13 nuevos). ruff (src+tests) + tsc limpios.
                          OJO dev: aprobar curador = update solicitudes_curador set estado='aprobada'
                          (admin approval llega en Fase 05). LECCIONES: endpoint 204 NO debe anotar
                          `-> None` (FastAPI lo trata como body→crash en import); migración con ENUM
                          de columna nueva usar create_type=False + create() explícito (si no, doble
                          CREATE TYPE); zsh `UID`/`GID`/`EUID`/`EGID` son especiales (no usar como vars).
                          OJO (heredado): `portal-vendedores` choca en 8025 (MailHog).
                          DEUDA: (1) sello_discografico como texto en perfil sigue omitido; (2)
                          onboarding sin GET de selecciones previas; (3) stats de medios
                          generos_frecuentes/tiempo_respuesta y "campañas como sello" → Fase 08.
```
