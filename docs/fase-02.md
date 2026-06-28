# Fase 02 — Modelo de datos + migraciones PostgreSQL

> **Estado:** `[x]` completada · **Días estimados:** 3 · **Modelo:** `claude-opus-4-7`
> **Skill:** `dba-skill`
> **Pre-requisitos:** Fase 01 `[x]`

---

## Contexto

Esta fase define **todo el esquema relacional** que sostiene el resto del proyecto. El modelo tiene tres actores principales:

- **Artistas / Sellos discográficos** — crean campañas y compran créditos. Un sello puede gestionar múltiples artistas.
- **Curadores** — reciben campañas y dan visibilidad a través de sus medios. Un curador puede tener múltiples medios (canales), cada uno especializado en un género o audiencia distinta (ej. una página de Facebook de cumbia, otra de rock, un perfil de Instagram de electrónica).
- **Artistas ↔ Curadores a través de medios** — cuando un artista envía una campaña a un curador, elige específicamente a cuál de sus medios desea que llegue, no al curador en general.

Relaciones clave que distinguen este modelo:
- `sellos_discograficos` → tiene muchos `usuarios` (artistas)
- `curador_medios` → un curador tiene N medios, cada uno con su canal, género, audiencia
- `campana_medios` → reemplaza `campana_profesionales`; vincula la campaña con el **medio específico** del curador (no con el curador en abstracto)

---

## Tareas

- [x] **T1.** Inicializar Alembic (`alembic init alembic` con template async).
- [x] **T2.** Configurar `alembic.ini` y `alembic/env.py` para usar `DATABASE_URL` de settings (asyncpg).
- [x] **T3.** Crear modelos SQLAlchemy en `src/models/`:

  **Usuarios y perfiles**
  - `perfiles` (id, nombre UK — Artista / Curador / Admin, descripcion, activo)
  - `usuarios` (id UUID, nombre_completo, correo UK, password_hash, tipo ENUM(artista,curador), perfil_id FK, activo, blocked_until, intentos_fallidos, foto_path, created_at, updated_at)

  **Sellos discográficos**
  - `sellos_discograficos` (id UUID, nombre UK, descripcion, logo_path, website, created_by FK→usuarios, created_at, updated_at)
  - `sello_artistas` (sello_id FK, artista_id FK, rol ENUM(owner,manager,artista), activo) — tabla puente; un artista puede pertenecer a un sello y el sello puede administrar múltiples artistas

  **Curadores y sus medios**
  - `solicitudes_curador` (id UUID, usuario_id FK, estado ENUM(pendiente,aprobada,rechazada), notas_revision, revisor_id FK nullable, created_at, updated_at) — flujo de aprobación admin
  - `curador_medios` (id UUID, curador_id FK→usuarios, nombre, tipo ENUM(playlist,blog,instagram,tiktok,youtube,facebook,twitter,radio,website,eventos,otro), url, descripcion, audiencia_estimada INT nullable, activo, created_at, updated_at) — cada fila es un canal/medio distinto del curador; géneros se gestionan via tabla puente `curador_medio_generos`
  - `curador_medio_generos` (medio_id FK→curador_medios, genero_id FK→generos_musicales, PRIMARY KEY(medio_id, genero_id)) — reemplaza `generos_especializados JSON`; permite filtrar medios por género con JOIN indexado

  **Géneros y categorías**
  - `generos_musicales` (id, nombre UK, activo)
  - `usuario_generos` (usuario_id FK, genero_id FK, tipo ENUM(preferido,excluido)) — géneros preferidos y excluidos de artistas y curadores

  **Catálogos para preferencias**
  - `idiomas` (codigo CHAR(2) PK — ISO 639-1, nombre) — catálogo de idiomas; seed con códigos usados en la plataforma
  - `regiones` (codigo CHAR(2) PK — ISO 3166-1 alpha-2, nombre) — catálogo de países/regiones

  **Preferencias de onboarding**
  - `usuario_preferencias` (usuario_id PK FK, apertura_musical INT default 50, acepta_todos_idiomas BOOL default false, tipo_lanzamientos ENUM(nuevos,post,ambos) nullable, updated_at) — datos recopilados en pasos progresivos; idiomas y regiones se gestionan via tablas puente
  - `usuario_preferencias_idiomas` (usuario_id FK→usuarios, idioma_codigo FK→idiomas, PRIMARY KEY(usuario_id, idioma_codigo)) — reemplaza `idiomas JSON`
  - `usuario_preferencias_regiones` (usuario_id FK→usuarios, region_codigo FK→regiones, PRIMARY KEY(usuario_id, region_codigo)) — reemplaza `regiones JSON`

  **Redes sociales del perfil**
  - `usuario_redes` (id UUID, usuario_id FK, tipo ENUM(spotify,instagram,youtube,tiktok,facebook,twitter,soundcloud,bandcamp,website,otro), url, created_at)

  **Créditos y wallet**
  - `creditos_transacciones` (id UUID, usuario_id FK, tipo ENUM(compra,gasto,devolucion,retiro), monto INT, referencia_stripe nullable, campana_id FK nullable, descripcion, created_at)
  - `wallets` (usuario_id PK FK, saldo_creditos INT CHECK(saldo_creditos >= 0), saldo_pendiente_retiro INT default 0, updated_at)

  **Campañas**
  - `campanas` (id UUID, artista_id FK→usuarios, sello_id FK nullable, titulo, descripcion, url_audio, url_imagen, url_material nullable, genero_id FK, estado ENUM(borrador,enviada,en_revision,completada,cancelada), creditos_usados INT, created_at, updated_at)
  - `campana_medios` (id UUID, campana_id FK, medio_id FK→curador_medios, curador_id FK→usuarios, estado ENUM(pendiente,aceptada,rechazada,entregada,expirada), fecha_limite, creditos_retenidos INT, created_at, updated_at) — vincula campaña con el **medio específico** elegido por el artista

  **Entregas**
  - `entregas_contenido` (id UUID, campana_medio_id FK, tipo ENUM(blog,playlist,reel,link,post), url_entrega nullable, contenido_html TEXT nullable, puntuacion_autenticidad INT nullable, metadatos_escritura JSONB nullable, aprobada_por_artista BOOL default false, created_at) — `metadatos_escritura` es JSONB: estructura varía por tipo de entrega

  **Retiros**
  - `solicitudes_retiro` (id UUID, curador_id FK→usuarios, monto INT, estado ENUM(pendiente,aprobada,rechazada,pagada), metodo_pago JSONB, notas_admin nullable, created_at, updated_at) — `metodo_pago` es JSONB: estructura varía por método (CLABE, PayPal, Wise)

  **Infraestructura**
  - `bitacora_eventos` (id UUID, autor_id FK nullable, accion, entidad, entidad_id, detalle JSONB, correlation_id, created_at) — `detalle` es JSONB: estructura libre por tipo de evento
  - `ips_bloqueadas` (id, ip UK, motivo, blocked_until, created_at)
  - `tokens` (id UUID, token UK, tipo ENUM(registro,reset,confirmacion_email), usuario_id FK nullable, expires_at, consumed_at nullable, created_at)
  - `parametros_config` (id, clave UK, valor_cifrado TEXT, es_secreto BOOL, descripcion, updated_by FK nullable, updated_at)

- [x] **T4.** Generar migración inicial con `alembic revision --autogenerate -m "initial schema"`. Incluir seed de catálogos `idiomas` y `regiones` (ISO 639-1 / ISO 3166-1).
- [x] **T5.** Revisar migración: tipos correctos, índices, UKs, FKs con `ON DELETE` apropiado. UUIDs como PK en entidades principales. Verificar que todos los índices del bloque **Índices requeridos** estén presentes.
- [x] **T6.** Seed inicial (`alembic/versions/0002_seed_defaults.py`):
  - Perfil ID 1 "Admin" (protegido) + Perfil ID 2 "Artista" + Perfil ID 3 "Curador".
  - Géneros musicales base: Pop, Indie, Electrónica, Hip-hop, Rock, Regional Mexicano, Jazz, Clásica, R&B, Cumbia, Salsa, Metal, Reggaeton, Trap, Corridos, Folk, Soul, Funk, Ambient, House.
  - Parámetros config: `creditos_por_medio` (default: 1), `dias_limite_respuesta` (default: 6), `precio_credito_mxn` (default: 50), `minimo_palabras_resena` (default: 150), `porcentaje_comision` (default: 20), `max_intentos_login` (default: 5), `block_duration_hours` (default: 6).
- [x] **T7.** Aplicar migraciones (`alembic upgrade head`) y validar — tablas creadas, seeds aplicados.
- [x] **T8.** Documentar en `docs/db/schema.md`: diagrama ER (Mermaid), descripción de cada tabla, reglas de integridad referencial.
- [x] **T9.** Rollback probado: `alembic downgrade base` + `upgrade head` ciclo completo sin pérdida.

---

## Índices requeridos

Todos deben crearse en la migración inicial (T4/T5). Los índices parciales (`WHERE`) son exclusivos de PostgreSQL.

```sql
-- bitacora_eventos
CREATE INDEX idx_bitacora_autor     ON bitacora_eventos(autor_id, created_at DESC);
CREATE INDEX idx_bitacora_entidad   ON bitacora_eventos(entidad, entidad_id, created_at DESC);

-- campanas
CREATE INDEX idx_campanas_artista   ON campanas(artista_id, estado);
CREATE INDEX idx_campanas_estado    ON campanas(estado);

-- campana_medios
CREATE INDEX idx_campana_medios_curador  ON campana_medios(curador_id, estado);
CREATE INDEX idx_campana_medios_campana  ON campana_medios(campana_id);
CREATE INDEX idx_campana_medios_fecha    ON campana_medios(fecha_limite) WHERE estado = 'pendiente';

-- creditos_transacciones
CREATE INDEX idx_creditos_usuario   ON creditos_transacciones(usuario_id, created_at DESC);

-- tokens
CREATE INDEX idx_tokens_expires     ON tokens(expires_at) WHERE consumed_at IS NULL;

-- ips_bloqueadas
CREATE INDEX idx_ips_blocked_until  ON ips_bloqueadas(blocked_until);

-- solicitudes_curador
CREATE INDEX idx_sol_curador_usuario ON solicitudes_curador(usuario_id, estado);
```

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
| `src/models/sellos.py` | sellos_discograficos + sello_artistas |
| `src/models/solicitudes_curador.py` | |
| `src/models/curador_medios.py` | |
| `src/models/generos.py` | generos_musicales + usuario_generos + curador_medio_generos |
| `src/models/catalogos.py` | idiomas + regiones |
| `src/models/usuario_preferencias.py` | usuario_preferencias + usuario_preferencias_idiomas + usuario_preferencias_regiones |
| `src/models/usuario_redes.py` | |
| `src/models/creditos.py` | transacciones + wallets |
| `src/models/campanas.py` | |
| `src/models/campana_medios.py` | reemplaza campana_profesionales |
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
- `SELECT * FROM perfiles WHERE nombre='Curador'` retorna 1 fila.
- `SELECT COUNT(*) FROM generos_musicales` retorna 20.
- Insertar usuario con `perfil_id` inexistente → falla por FK.
- Insertar 2 usuarios con mismo correo → falla por UK.
- Insertar wallet con `saldo_creditos < 0` → falla (CHECK constraint).
- Un curador puede tener 3 medios distintos (playlist de Spotify, página de Facebook de cumbia, perfil de TikTok de reggaeton) → 3 filas en `curador_medios` con mismo `curador_id`.
- Una campaña puede enviarse a 2 medios distintos del mismo curador → 2 filas en `campana_medios`.
- Un artista puede pertenecer a un sello → `sello_artistas` tiene la fila; el sello puede lanzar campañas en nombre del artista (`campanas.sello_id` no nulo).

---

## Notas de diseño — decisiones clave

**Por qué `campana_medios` en lugar de `campana_profesionales`/`campana_curadores`:**
El artista elige el *medio específico* (el canal de TikTok de reggaeton del curador X), no al curador en abstracto. Esto permite que el curador con 5 medios reciba campañas en medios distintos de forma independiente, cada una con su propio estado, deadline y crédito retenido.

**Por qué `sello_artistas` como tabla puente:**
Un artista puede pertenecer a un sello (o a ninguno, es independiente). El sello puede tener managers que no son el artista. La tabla puente con `rol` permite este modelo sin romper la simplicidad de `usuarios`.

**Por qué `usuario_preferencias` separado de `usuarios`:**
Los datos de onboarding (idiomas, regiones, géneros, apertura musical) son opcionales y se llenan en pasos progresivos. Tenerlos en una tabla aparte evita NULL masivos en la tabla principal y facilita actualizar preferencias sin tocar el registro del usuario.

**Por qué catálogos `idiomas`/`regiones` en lugar de JSON:**
El matching artista↔curador filtra por idioma y región. Con JSON no hay índice posible; con tablas puente la query es un JOIN simple sobre PKs indexadas. Cambiar de JSON a catálogo después de producción implica migración de datos costosa — se define normalizado desde el inicio.

**Por qué `curador_medio_generos` en lugar de `generos_especializados JSON`:**
El catálogo `generos_musicales` ya existe. Duplicar géneros en JSON rompe integridad referencial (puedes escribir "Regueton" en un medio y "Reggaeton" en otro). La tabla puente garantiza unicidad de valores y permite la query "dame todos los medios especializados en Hip-hop" con índice.

**Por qué `detalle`/`metodo_pago`/`metadatos_escritura` permanecen como JSONB:**
Estos campos tienen estructura genuinamente variable: `detalle` en bitácora cambia por tipo de evento, `metodo_pago` varía por proveedor de pago, `metadatos_escritura` varía por tipo de entrega. No existe un schema fijo que normalizar. JSONB con GIN index es la herramienta correcta para datos semiestructurados inamovibles.

---

## Skill recomendado por tarea

- **T1, T2, T4, T5, T7, T9:** `dba-skill`.
- **T3:** `dba-skill` + `developer-skill`.
- **T6:** `dba-skill` (qué seedear según spec).
- **T8:** `document-skill`.

---

## PROGRESO

- [x] T1 — Inicializar Alembic
- [x] T2 — Configurar env async
- [x] T3 — Crear modelos (25 tablas: +curador_medio_generos, +idiomas, +regiones, +usuario_preferencias_idiomas, +usuario_preferencias_regiones)
- [x] T4 — Migración inicial
- [x] T5 — Revisar migración
- [x] T6 — Seed defaults
- [x] T7 — Aplicar y validar
- [x] T8 — schema.md con diagrama ER
- [x] T9 — Probar rollback

**Última sesión:** 2026-06-27 — T1 y T2 completadas. `alembic/env.py` reescrito como template
async (asyncpg), cableado a `DATABASE_URL` de settings y a `Base.metadata`. Creado
`src/models/base.py` (Base + mixins UUID PK / timestamps + naming_convention de constraints) y
`src/models/__init__.py` como punto único de registro de modelos. Validado con `alembic current`
(conecta a Postgres sin errores) y `ruff check` limpio.
**Próximo paso al reanudar:** Fase 02 COMPLETADA (9/9). Iniciar Fase 03 — Autenticación +
Onboarding 9 pasos + login + OTP + reset (modelo `claude-opus-4-7`, skill `security-skill`).
Depende de Fase 02 `[x]`.

Nota T8/T9: `docs/db/schema.md` creado (diagrama ER Mermaid, tablas por dominio, ENUMs, reglas
ON DELETE, índices). Ciclo de rollback validado: `upgrade → downgrade base → upgrade` limpio.
Bug corregido en el `downgrade` de 0001: faltaba soltar los 13 tipos ENUM nativos (PostgreSQL no
los borra con DROP TABLE) → se añadió un bucle `DROP TYPE IF EXISTS`, haciendo el ciclo idempotente.

Nota T5/T6/T7: migraciones aplicadas (`0001` → `0002`). Validado contra todos los criterios:
26 tablas (25 + alembic_version), 20 géneros, 8 idiomas (códigos íntegros: `es`/`en`… no truncados),
20 regiones, 7 parámetros, perfiles 1=Admin/2=Artista/3=Curador. Constraints FK/UK/CHECK rechazan
correctamente. Funcional OK: curador con 3 medios, sello↔artista, campaña a 2 medios del mismo curador.
Bug corregido en T7: `sa.CHAR` sin longitud en el `bulk_insert` de 0001 truncaba los códigos a 1 char
(`'es'`→`'e'`) → se cambió a `sa.String` (la columna física sigue siendo CHAR(2)).

Nota T4: `0001_initial_schema.py` (`--rev-id 0001`). Autogenerate capturó `created_at DESC` y los
`WHERE` parciales. Seed de catálogos vía `op.bulk_insert`.

Nota T3: 25 tablas en `src/models/`. ENUMs en `src/models/enums.py`, mixins en `base.py`,
engine async en `src/infra/db.py`.