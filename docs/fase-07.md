# Fase 07 — Géneros musicales + Configuración de categorías

> **Estado:** `[ ]` pendiente · **Días estimados:** 2 · **Modelo:** `claude-sonnet-4-6`
> **Skills:** `developer-skill`, `frontend-skill`
> **Pre-requisitos:** Fase 05 `[x]`

---

## Contexto

Los géneros musicales y categorías de profesionales son catálogos de configuración que:
1. El **admin** gestiona (crear, editar, activar/desactivar).
2. Los **artistas** usan al crear campañas para clasificar su música.
3. Los **profesionales** usan para declarar su especialidad (qué tipos de música cubren).
4. El sistema usa para hacer el **match** entre campañas y profesionales relevantes.

Un género tiene sub-categorías (ej. "Urbano" → ["Trap", "Reggaeton", "Corridos tumbados"]).
Los profesionales pueden seleccionar múltiples categorías de múltiples géneros.

---

## Tareas

- [ ] **T1.** Endpoints admin géneros: `GET /admin/generos`, `POST`, `PATCH /:id` (nombre, activo). Bloqueo de eliminación si hay campañas con ese género.
- [ ] **T2.** Endpoints admin categorías: `GET /admin/generos/:genero_id/categorias`, `POST`, `PATCH /:id`. Bloqueo de eliminación si hay profesionales con esa categoría.
- [ ] **T3.** Endpoint público `GET /generos` (con sus categorías anidadas, solo activos). Para usar en formularios de registro de profesional y creación de campaña.
- [ ] **T4.** Endpoint `PUT /profesional/categorias`: el profesional en sesión actualiza sus categorías de interés (array de `categoria_id`). Validar que todas las categorías pertenecen a géneros activos.
- [ ] **T5.** Vista `(dashboard)/admin/generos/page.tsx`: tabla de géneros + acordeón de categorías con toggle de estado.
- [ ] **T6.** Componente reutilizable `GenerosCategoriasPicker.tsx`: selector multi-nivel para que el profesional elija sus especialidades. Se reutiliza en el formulario de aplicación (Fase 03) y en el perfil.
- [ ] **T7.** Sección en perfil profesional (`mi-perfil`) para ver y actualizar sus categorías seleccionadas (reutiliza componente T6).
- [ ] **T8.** Tests: géneros con campañas no se pueden eliminar; profesional con categorías inactivas no aparece en búsquedas.

---

## Archivos a crear

| Ruta | |
|------|-|
| `src/api/admin_generos.py` | |
| `src/api/generos_public.py` | |
| `src/api/profesional_categorias.py` | |
| `src/services/generos_service.py` | |
| `app/(dashboard)/admin/generos/page.tsx` | |
| `components/forms/GenerosCategoriasPicker.tsx` | |
| `tests/integration/test_generos.py` | |

---

## Tests / validaciones

- `DELETE /admin/generos/1` con campañas activas → 409.
- `PUT /profesional/categorias` con `categoria_id` de género inactivo → 422.
- `GET /generos` solo retorna géneros activos con sus categorías activas anidadas.
- Profesional sin categorías asignadas retorna lista vacía (no error).

---

## Skill recomendado por tarea

- **T1-T4:** `developer-skill`.
- **T5-T7:** `frontend-skill`.
- **T8:** `testing-skill`.

---

## PROGRESO

- [ ] T1 — Endpoints admin géneros
- [ ] T2 — Endpoints admin categorías
- [ ] T3 — GET /generos (público)
- [ ] T4 — PUT /profesional/categorias
- [ ] T5 — Vista admin géneros
- [ ] T6 — GenerosCategoriasPicker (componente)
- [ ] T7 — Sección en perfil profesional
- [ ] T8 — Tests

**Última sesión:** —
**Próximo paso al reanudar:** T1 — endpoints CRUD de géneros en `src/api/admin_generos.py` con guard `require_admin`.
