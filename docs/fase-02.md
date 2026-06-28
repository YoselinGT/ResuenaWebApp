# Fase 02 — Modelo de datos + migraciones PostgreSQL

> **Estado:** `[ ]` pendiente · **Días estimados:** 3 · **Modelo:** `claude-opus-4-7`
> **Skill:** `dba-skill`
> **Pre-requisitos:** Fase 01 `[x]`

---

## Contexto

Esta fase define **todo el esquema relacional** que sostiene el resto del proyecto: usuarios (artistas y profesionales), RBAC, créditos/wallet, campañas musicales, control de entregas y bitácora de auditoría.

La BD local vive en el contenedor `postgres`. Se usa **Alembic** para versionar migraciones y **SQLAlchemy 2** (async) para modelos.

Particularidades importantes:
- Dos tipos de usuario distintos: **Artistas/Sellos** y **Profesionales** (bloggers, playlisters, influencers, creadores de reels).
- Los profesionales pasan por un flujo de aprobación admin antes de poder operar.
- Los créditos se compran con dinero real (Stripe) y circulan internamente.
- Las campañas tienen un ciclo de vida definido: borrador → enviada → aceptada/rechazada → entregada.

---

## Tareas

- [ ] **T1.** Inicializar Alembic (`alembic init alembic` con template async).
- [ ] **T2.** Configurar `alembic.ini` y `alembic/env.py` para usar `DATABASE_URL` de settings (asyncpg).
- [ ] **T3.** Crear modelos SQLAlchemy en `src/models/`:
  - `perfiles` (id, nombre UK, descripcion, activo) — Artista, Profesional, Admin
  - `usuarios` (id UUID, nombre_completo, correo UK, password_hash, tipo ENUM(artista,profesional), perfil_id FK, activo, blocked_until, intentos_fallidos, foto_path, sello_discografico nullable, created_at, updated_at)
  - `solicitudes_profesional` (id, usuario_id FK, tipo_profesional ENUM(blogger,playlister,influencer,reel_creator), url_portfolio, redes_sociales JSON, estado ENUM(pendiente,aprobada,rechazada), revisor_id FK nullable, notas_revision, created_at, updated_at)
  - `generos_musicales` (id, nombre UK, activo)
  - `categorias_profesional` (id, genero_id FK, nombre UK, activo)
  - `profesional_categorias` (profesional_id, categoria_id) — tabla puente
  - `creditos_transacciones` (id UUID, usuario_id FK, tipo ENUM(compra,gasto,devolucion,retiro), monto INT, referencia_stripe nullable, campaña_id FK nullable, descripcion, created_at)
  - `wallets` (usuario_id PK FK, saldo_creditos INT, saldo_pendiente_retiro INT, updated_at)
  - `campanas` (id UUID, artista_id FK, titulo, descripcion, url_audio, url_imagen, url_material ZIP nullable, genero_id FK, estado ENUM(borrador,enviada,en_revision,completada,cancelada), creditos_usados INT, created_at, updated_at)
  - `campana_profesionales` (id, campana_id FK, profesional_id FK, estado ENUM(pendiente,aceptada,rechazada,entregada,expirada), fecha_limite, creditos_retenidos INT, created_at, updated_at)
  - `entregas_contenido` (id UUID, campana_profesional_id FK, tipo ENUM(blog,playlist,reel,link), url_entrega nullable, contenido_html TEXT nullable, puntuacion_autenticidad INT, metadatos_escritura JSON, aprobada_por_artista bool, created_at)
  - `solicitudes_retiro` (id UUID, profesional_id FK, monto INT, estado ENUM(pendiente,aprobada,rechazada,pagada), metodo_pago JSON, notas_admin nullable, created_at, updated_at)
  - `bitacora_eventos` (id, autor_id FK nullable, accion, entidad, entidad_id, detalle JSON, correlation_id, created_at) — índice por (autor_id, created_at)
  - `ips_bloqueadas` (id, ip UK, motivo, blocked_until, created_at)
  - `tokens` (id UUID, token UK, tipo ENUM(registro,reset,confirmacion_email), usuario_id FK nullable, expires_at, consumed_at nullable, created_at)
  - `parametros_config` (id, clave UK, valor_cifrado TEXT, es_secreto bool, descripcion, updated_by FK nullable, updated_at)
- [ ] **T4.** Generar migración inicial con `alembic revision --autogenerate -m "initial schema"`.
- [ ] **T5.** Revisar migración: confirmar tipos correctos, índices, UKs, FKs con `ON DELETE` apropiado. Usar UUID como PK en tablas principales.
- [ ] **T6.** Seed inicial (`alembic/versions/<id>_seed_defaults.py`):
  - Perfil ID 1 "Admin" (protegido) + Perfil ID 2 "Artista" + Perfil ID 3 "Profesional".
  - Géneros musicales base (Pop, Rock, Urbano, Electrónica, Regional Mexicano, Jazz, Clásica, Indie, R&B, Cumbia, Salsa, Metal).
  - Parámetros config: `creditos_por_profesional` (default: 1), `dias_limite_respuesta` (default: 6), `precio_credito_mxn` (default: 50), `minimo_palabras_resena` (default: 150), `porcentaje_comision` (default: 20).
- [ ] **T7.** Aplicar migraciones (`alembic upgrade head`) y validar — tablas creadas, seeds aplicados.
- [ ] **T8.** Documentar en `docs/db/schema.md`: diagrama ER (Mermaid), descripción de cada tabla, reglas de integridad referencial.
- [ ] **T9.** Rollback probado: `alembic downgrade base` + `upgrade head` ciclo completo sin pérdida.

---

## Archivos a crear

| Ruta | Propósito |
|------|-----------|
| `alembic.ini` | config raíz |
| `alembic/env.py` | env async |
| `alembic/versions/0001_initial_schema.py` | migración inicial |
| `alembic/versions/0002_seed_defaults.py` | seed perfiles + géneros + params |
| `src/models/base.py` | `DeclarativeBase` + mixins (timestamps, UUID PK) |
| `src/models/usuarios.py` | |
| `src/models/perfiles.py` | |
| `src/models/solicitudes_profesional.py` | |
| `src/models/generos.py` | |
| `src/models/categorias.py` | |
| `src/models/creditos.py` | transacciones + wallets |
| `src/models/campanas.py` | |
| `src/models/campana_profesionales.py` | |
| `src/models/entregas.py` | |
| `src/models/solicitudes_retiro.py` | |
| `src/models/bitacora_eventos.py` | |
| `src/models/ips_bloqueadas.py` | |
| `src/models/tokens.py` | |
| `src/models/parametros_config.py` | |
| `src/infra/db.py` | engine async + session factory |
| `docs/db/schema.md` | diagrama ER + descripción |

---

## Tests / validaciones

- `alembic upgrade head` → exit code 0, sin errores.
- `alembic downgrade base` → revierte sin errores.
- `SELECT * FROM perfiles WHERE nombre='Admin'` retorna 1 fila.
- `SELECT COUNT(*) FROM generos_musicales` retorna 12.
- Insertar usuario con `perfil_id` inexistente → falla por FK.
- Insertar 2 usuarios con mismo correo → falla por UK.
- Insertar wallet con `saldo_creditos < 0` → falla (CHECK constraint).

---

## Skill recomendado por tarea

- **T1, T2, T4, T5, T7, T9:** `dba-skill` (Alembic, migraciones, PostgreSQL).
- **T3:** `dba-skill` + `developer-skill` (SQLAlchemy modelos).
- **T6:** `dba-skill` + `business-analyst-skill` (qué seedear según spec).
- **T8:** `document-skill`.

---

## PROGRESO

- [ ] T1 — Inicializar Alembic
- [ ] T2 — Configurar env async
- [ ] T3 — Crear modelos (16 entidades)
- [ ] T4 — Migración inicial
- [ ] T5 — Revisar migración
- [ ] T6 — Seed defaults
- [ ] T7 — Aplicar y validar
- [ ] T8 — schema.md
- [ ] T9 — Probar rollback

**Última sesión:** —
**Próximo paso al reanudar:** T1 — inicializar Alembic dentro del contenedor `api` con template async.
