# Fase 11 — Panel de entregas (reels, links, HTML Blogger)

> **Estado:** `[ ]` pendiente · **Días estimados:** 3 · **Modelo:** `claude-sonnet-4-6`
> **Skills:** `developer-skill`, `frontend-skill`
> **Pre-requisitos:** Fase 10 `[x]`

---

## Contexto

El panel de entregas es donde cada tipo de profesional gestiona su workflow específico:
- **Blogger:** usa el editor de Fase 10, entrega HTML. Ve sus entregas pasadas y puede exportar de nuevo.
- **Playlister:** entrega un link a la playlist (Spotify, Apple Music, etc.) donde incluyó la canción.
- **Influencer:** entrega link a post (Instagram, TikTok, YouTube, etc.) donde publicó contenido.
- **Creador de reels:** entrega link al reel publicado + stats si los tiene.

El artista tiene un panel espejo donde ve todas las entregas recibidas por campaña, puede aprobar/solicitar cambios y dejar notas.

---

## Tareas

- [ ] **T1.** Endpoint `GET /profesional/entregas`: historial de entregas del profesional (paginado, filtrable por estado y tipo de campaña).
- [ ] **T2.** Endpoint `GET /artista/campanas/:id/entregas`: lista de entregas recibidas para una campaña específica, agrupadas por profesional.
- [ ] **T3.** Endpoint `POST /artista/campanas/:id/entregas/:entrega_id/solicitar-cambio`: body `{comentario}`. Solo si `aprobada_por_artista = false`. Notifica al profesional.
- [ ] **T4.** Endpoint `GET /profesional/entregas/:id/exportar-html`: retorna el `contenido_html` limpio de la entrega tipo blog, con Content-Type `text/html` para descarga directa.
- [ ] **T5.** Vista `(dashboard)/profesional/entregas/page.tsx`: historial con filtros, badge de estado, acciones (ver detalle, descargar HTML si es blog).
- [ ] **T6.** Vista `(dashboard)/artista/campanas/[id]/entregas/page.tsx`: todas las entregas de la campaña agrupadas. Para cada una: tipo, profesional, link o preview del contenido, botón aprobar/solicitar cambio.
- [ ] **T7.** Componente `EntregaViewer.tsx`: renderiza la entrega según tipo — blog (HTML sanitizado en iframe sandbox), playlist/influencer/reel (link clickeable con preview open-graph si disponible).
- [ ] **T8.** Componente `EntregaTimeline.tsx`: muestra el historial de acciones sobre una entrega (enviada → revisión solicitada → re-entregada → aprobada).
- [ ] **T9.** Tests: exportar HTML de entrega blog descarga archivo correcto; solicitar cambio cuando ya aprobada → 409.

---

## Archivos a crear

| Ruta | |
|------|-|
| `src/api/entregas.py` | |
| `src/services/entregas_service.py` | |
| `app/(dashboard)/profesional/entregas/page.tsx` | |
| `app/(dashboard)/artista/campanas/[id]/entregas/page.tsx` | |
| `components/entregas/EntregaViewer.tsx` | |
| `components/entregas/EntregaTimeline.tsx` | |
| `tests/integration/test_entregas.py` | |

---

## Tests / validaciones

- `GET /profesional/entregas` retorna solo entregas del profesional en sesión.
- `GET /artista/campanas/:id/entregas` retorna solo entregas de campañas del artista.
- `POST solicitar-cambio` en entrega ya aprobada → 409.
- HTML exportado no contiene `<script>` ni `onclick=`.

---

## PROGRESO

- [ ] T1 — GET /profesional/entregas
- [ ] T2 — GET /artista/campanas/:id/entregas
- [ ] T3 — POST solicitar-cambio
- [ ] T4 — GET exportar-html
- [ ] T5 — Vista profesional entregas
- [ ] T6 — Vista artista entregas por campaña
- [ ] T7 — EntregaViewer componente
- [ ] T8 — EntregaTimeline componente
- [ ] T9 — Tests

**Última sesión:** —
**Próximo paso al reanudar:** T1 — endpoint `GET /profesional/entregas` con guard `require_profesional_aprobado` y paginación.
