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
Fecha último avance:      2026-06-30
Última fase tocada:       Fase 06 — Sistema de créditos + Pasarela de pago (Stripe) (COMPLETADA, 11/11)
Último archivo modificado: tests/integration/test_creditos.py (T11)
Próxima acción al reanudar: Fase 07 — Géneros musicales + Configuración de categorías
                            (modelo claude-sonnet-4-6, skill developer-skill).
Notas de handoff:         Fase 06 completa en rama `fase-06` (desde main con 05 mergeada).
                          BACKEND créditos: src/services/wallet_service.py (saldo atómico SELECT
                          FOR UPDATE, wallet on-demand, add_credits idempotente por referencia,
                          deduct_credits→InsufficientCreditsError 409, list_paquetes/get_precio_credito
                          desde parametros_config, list_historial), src/services/stripe_service.py
                          (create_checkout_session async via to_thread + handle_webhook verifica firma
                          → WebhookInvalidError 400 → add_credits idempotente por payment_intent).
                          src/api/creditos.py: GET /creditos/paquetes, GET /balance, GET /historial,
                          POST /checkout (require_artista, valida paquete), POST /webhook (SIN JWT,
                          body crudo + stripe-signature). DTOs en src/models/dto/creditos.py.
                          Excepción InsufficientCreditsError (→409) en exceptions.py+errors.py.
                          FRONTEND: app/(dashboard)/artista/creditos (page + success + cancel),
                          components/creditos/PaqueteCard + HistorialTransacciones; sidebar artista
                          "Créditos" → /artista/creditos. Tests: 79 passed (13 nuevos:
                          test_wallet_service 5 + test_creditos 8). ruff(src+tests)+tsc limpios.
                          STRIPE: stripe==11.4.1 instalado; .env tiene STRIPE_SECRET_KEY real (test);
                          checkout en vivo verificado (URL real cs_test_). OJO: STRIPE_WEBHOOK_SECRET
                          sigue placeholder whsec_... (firma validada localmente con HMAC; para
                          webhooks reales de Stripe usar el secret del dashboard/CLI). El endpoint
                          /webhook va sin sesión (no depende de get_current_user). Migraciones head=0005.
                          OJO (heredado): portal-vendedores choca en 8025 (MailHog); admin se crea
                          promoviendo perfil_id=1 + re-login. zsh: UID/GID son reservadas.
                          DEUDA: (1) sello_discografico texto en perfil; (2) onboarding sin GET de
                          selecciones previas; (3) stats medios + "campañas como sello" → Fase 08.
```
