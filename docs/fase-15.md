# Fase 15 — Testing + CI/CD Bitbucket + Documentación

> **Estado:** `[ ]` pendiente · **Días estimados:** 4 · **Modelo:** `claude-sonnet-4-6`
> **Skills:** `testing-skill`, `deployment-skill`, `document-skill`
> **Pre-requisitos:** Fase 14 `[x]` (todas las fases anteriores completas)

---

## Contexto

Esta fase cierra el proyecto y lo deja **listo para producción**. Combina tres entregables transversales:

1. **Testing completo** — cobertura ≥70% backend, flujos críticos en e2e, pruebas de carga sobre el endpoint de envío de campaña.
2. **CI/CD** — Bitbucket Pipelines que ejecute lint + test + build + deploy a servidor Linux.
3. **Documentación** — Swagger generado, colección Postman, manual de usuario por rol, manual de errores, diagramas.

---

## Tareas

### Testing

- [ ] **T1.** Suite unitaria completa con `pytest`: cobertura ≥70% en `src/services/`. Foco: `password_service`, `wallet_service`, `autenticidad_service`, `similaridad_service`, `stripe_service`.
- [ ] **T2.** Suite de integración con base de datos de prueba (Testcontainers PostgreSQL + Redis + RabbitMQ). Cubrir flujos: auth completo (artista + profesional), aprobación, compra créditos, envío campaña, entrega, retiro.
- [ ] **T3.** Playwright e2e para flujos críticos:
  - Registro artista → confirmación → login → comprar créditos (Stripe test) → crear campaña → enviar.
  - Registro profesional → confirmación → aplicación → aprobación admin → recibir campaña → aceptar → entregar.
  - Reset de password completo.
  - Editor blogger: escribir reseña, verificar bloqueo de paste, exportar HTML.
- [ ] **T4.** Pruebas de carga ligeras con `locust` sobre `POST /campanas/:id/enviar` y `POST /auth/login`.
- [ ] **T5.** Configurar `pytest-cov` con threshold 70% que falle el pipeline si baja.

### CI/CD

- [ ] **T6.** `bitbucket-pipelines.yml` con etapas: lint → test → build → deploy:dev → deploy:prod (manual).
- [ ] **T7.** Variables de pipeline (secretos): `DB_URL`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_S3_BUCKET`, `SENTRY_DSN`, `SSH_KEY`.
- [ ] **T8.** Script `deploy/deploy.sh`: pull imagen → `docker compose pull && up -d` → healthchecks → `alembic upgrade head`.
- [ ] **T9.** Smoke tests post-deploy: `/health` → 200, `POST /auth/login` inválido → 401.

### Documentación

- [ ] **T10.** Personalizar Swagger/OpenAPI: descripciones, tags por módulo (auth, campanas, creditos, profesional, admin), ejemplos. Exportar `docs/api/openapi.json`.
- [ ] **T11.** Colección Postman desde OpenAPI. Guardar en `docs/postman/resuena.json` + envs `local.env.json`, `dev.env.json`.
- [ ] **T12.** Manual de usuario artista (`docs/manuales/usuario-artista.md`): registro → créditos → crear campaña → seguimiento → aprobar entregas.
- [ ] **T13.** Manual de usuario profesional (`docs/manuales/usuario-profesional.md`): registro → aplicación → recibir campañas → editor blogger → retiro.
- [ ] **T14.** Manual de usuario admin (`docs/manuales/usuario-admin.md`): aprobar profesionales → gestionar retiros → configurar parámetros → revisar bitácora.
- [ ] **T15.** Manual de errores (`docs/manuales/errores.md`): tabla código → mensaje → causa → resolución.
- [ ] **T16.** Manual técnico (`docs/manuales/tecnico.md`): arquitectura por capas, ER de BD, secuencias de flujos críticos (compra créditos, envío campaña, scoring de autenticidad).
- [ ] **T17.** Diagramas Mermaid en `docs/diagramas/`: `arquitectura.md`, `er-bd.md`, `seq-campana.md`, `seq-creditos.md`, `seq-autenticidad.md`.
- [ ] **T18.** Guía de instalación en servidor Linux (`docs/manuales/deploy-linux.md`): Docker, PostgreSQL, configuración de credenciales AWS (IAM role o vars de entorno), política de bucket S3, ZeroTier/VPN, SSL.
- [ ] **T19.** `CHANGELOG.md` con versión 1.0.0.
- [ ] **T20.** Actualizar `README.md` raíz con badges (build, coverage), quickstart, links a manuales.

---

## Archivos a crear

| Ruta | |
|------|-|
| `tests/conftest.py` | |
| `tests/unit/test_*.py` (varios) | |
| `tests/integration/test_*.py` (varios) | |
| `tests/e2e/*.spec.ts` (Playwright) | |
| `tests/load/locustfile.py` | |
| `playwright.config.ts` | |
| `bitbucket-pipelines.yml` | |
| `deploy/deploy.sh` | |
| `deploy/smoke-test.sh` | |
| `docs/api/openapi.json` | |
| `docs/postman/resuena.json` | |
| `docs/postman/local.env.json` | |
| `docs/postman/dev.env.json` | |
| `docs/manuales/usuario-artista.md` | |
| `docs/manuales/usuario-profesional.md` | |
| `docs/manuales/usuario-admin.md` | |
| `docs/manuales/errores.md` | |
| `docs/manuales/tecnico.md` | |
| `docs/manuales/deploy-linux.md` | |
| `docs/diagramas/arquitectura.md` | |
| `docs/diagramas/er-bd.md` | |
| `docs/diagramas/seq-campana.md` | |
| `docs/diagramas/seq-creditos.md` | |
| `docs/diagramas/seq-autenticidad.md` | |
| `CHANGELOG.md` | |

---

## Tests / validaciones

- `pytest -q --cov=src --cov-fail-under=70` pasa.
- Playwright completa los 4 flujos e2e sin intervención.
- Push a `develop` → pipeline deploya a servidor dev y smoke test pasa.
- Swagger en `/docs` lista todos los endpoints documentados.
- Colección Postman importable y ejecutable contra local con env correspondiente.
- Manuales legibles en GitHub/visor markdown sin errores de formato.

---

## Skill recomendado por tarea

- **T1-T5:** `testing-skill`.
- **T6-T9:** `deployment-skill`.
- **T10-T20:** `document-skill`.

---

## PROGRESO

- [ ] T1 — Pytest unit (cobertura ≥70%)
- [ ] T2 — Pytest integration (Testcontainers)
- [ ] T3 — Playwright e2e (4 flujos)
- [ ] T4 — Locust carga
- [ ] T5 — Coverage threshold
- [ ] T6 — bitbucket-pipelines.yml
- [ ] T7 — Variables pipeline
- [ ] T8 — deploy.sh
- [ ] T9 — smoke-test.sh
- [ ] T10 — Swagger personalizado
- [ ] T11 — Colección Postman
- [ ] T12 — Manual usuario artista
- [ ] T13 — Manual usuario profesional
- [ ] T14 — Manual usuario admin
- [ ] T15 — Manual errores
- [ ] T16 — Manual técnico
- [ ] T17 — Diagramas Mermaid
- [ ] T18 — Guía deploy Linux
- [ ] T19 — CHANGELOG
- [ ] T20 — README final

**Última sesión:** —
**Próximo paso al reanudar:** T1 — suite pytest unitaria, empezar por `test_wallet_service.py` (operaciones atómicas y bloqueos) y `test_autenticidad_service.py` (scoring).
