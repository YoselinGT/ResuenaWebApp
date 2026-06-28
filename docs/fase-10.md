# Fase 10 — Editor de contenido para bloggers (anti-IA)

> **Estado:** `[ ]` pendiente · **Días estimados:** 4 · **Modelo:** `claude-opus-4-7`
> **Skills:** `developer-skill`, `frontend-skill`
> **Pre-requisitos:** Fase 09 `[x]`

---

## Contexto

Esta es la funcionalidad más diferenciadora de Resuena: garantizar que las reseñas de los bloggers son **escritas por humanos**, no generadas por IA. Esto protege la credibilidad editorial de la plataforma.

El editor captura **metadatos de escritura** que luego se analizan para producir una `puntuacion_autenticidad` (0-100). Una puntuación baja puede derivar en bandera de revisión o rechazo automático.

Métricas capturadas en tiempo real:
- Tiempo total de escritura (ms activos, excluyendo tiempo idle >30s).
- Distribución de velocidad de tecleo (teclas por minuto en ventanas de 30s).
- Razón de borrados / total de teclas (indica escritura orgánica vs pegar-y-corregir).
- Detección de paste events (clipboard) — penaliza fuerte.
- Detección de dictado por voz (eventos de input con `inputType='insertReplacementText'`).
- Varianza en patrones de escritura (un humano tiene varianza natural).

Reglas de negocio:
- Mínimo de palabras configurable (`minimo_palabras_resena`, default 150).
- Corrector ortográfico integrado (basado en `nspell` o API del browser).
- Exportación en HTML listo para Blogger (conserva h2, p, img tags, limpia scripts).
- El blogger no puede copiar-pegar texto externo (paste de texto bloqueado; paste de imagen permitido).
- El blogger no puede usar dictado de voz.
- La reseña anterior del mismo blogger se compara para detectar reutilización (similaridad de texto >80% → bandera).

---

## Tareas

- [ ] **T1.** Componente `BloggerEditor` (`components/editor/BloggerEditor.tsx`): editor rich-text custom (usar `Tiptap` o similar). Bloquea `paste` de texto. Bloquea dictado de voz (detecta `insertReplacementText`). Muestra contador de palabras en tiempo real.
- [ ] **T2.** Hook `useEscrituraTracker` (`hooks/useEscrituraTracker.ts`): captura en memoria los metadatos de escritura: timestamps de cada keydown, velocidades por ventana, conteo de backspace, intentos de paste, eventos de dictado. Serializa a JSON al momento de envío.
- [ ] **T3.** Corrector ortográfico integrado: subrayado en rojo de palabras incorrectas. Usar `typo.js` o `nspell` con diccionario es-MX.
- [ ] **T4.** Exportación HTML: botón "Copiar para Blogger" que serializa el contenido del editor a HTML limpio (sin clases de Tiptap, sin scripts, compatible con Blogger).
- [ ] **T5.** Backend — Servicio `autenticidad_service.py`: recibe `metadatos_escritura` JSON y calcula `puntuacion_autenticidad` (0-100).
  - Algoritmo: penaliza pastes (−30/evento), penaliza dictado (−40), penaliza velocidad >300 WPM sostenida (−20), penaliza varianza baja (−15), bonifica tiempo total proporcional a palabras.
  - Umbral de alerta: <50 → bandera automática para revisión admin.
  - Umbral de bloqueo: <20 → entrega rechazada automáticamente.
- [ ] **T6.** Backend — Comparador de reseñas (`src/services/similaridad_service.py`): dado el texto de la reseña y el `profesional_id`, busca las últimas 5 entregas de ese profesional y calcula similaridad (cosine similarity sobre TF-IDF o Jaccard simple). Si >80% → bandera `contenido_repetido`.
- [ ] **T7.** Actualizar `POST /profesional/campanas/:id/entregar` (Fase 09): si `tipo == 'blog'`, recibe también `metadatos_escritura`. Llama a `autenticidad_service` y `similaridad_service`. Guarda `puntuacion_autenticidad` y `metadatos_escritura` en `entregas_contenido`. Si puntuación <20 → rechaza automáticamente con mensaje claro. Si <50 → entrega guardada pero marcada para revisión.
- [ ] **T8.** Vista admin `(dashboard)/admin/entregas-revision/page.tsx`: lista de entregas con puntuación <50, mostrando el texto, la puntuación y los metadatos clave (pastes, tiempo, WPM promedio). Botón para aprobar manualmente o rechazar.
- [ ] **T9.** Endpoint `GET /admin/entregas/:id/metadatos`: retorna el JSON completo de `metadatos_escritura` para inspección del admin.
- [ ] **T10.** Tests: paste de texto bloqueado en editor; dictado detectado y registrado; puntuación calculada correctamente para escenarios simulados; reseña idéntica a anterior → bandera `contenido_repetido`.

---

## Archivos a crear

| Ruta | |
|------|-|
| `components/editor/BloggerEditor.tsx` | |
| `components/editor/WordCounter.tsx` | |
| `components/editor/SpellChecker.tsx` | |
| `hooks/useEscrituraTracker.ts` | |
| `lib/html-exporter.ts` | limpiador HTML para Blogger |
| `src/services/autenticidad_service.py` | |
| `src/services/similaridad_service.py` | |
| `src/api/admin_entregas.py` | |
| `app/(dashboard)/admin/entregas-revision/page.tsx` | |
| `tests/unit/test_autenticidad_service.py` | |
| `tests/unit/test_similaridad_service.py` | |
| `tests/integration/test_entrega_blog.py` | |

---

## Tests / validaciones

- Editor: keydown con `ctrlKey + 'v'` → evento cancelado, `pasteCount` incrementa en tracker.
- `inputType = 'insertReplacementText'` → `voiceCount` incrementa, texto bloqueado.
- `autenticidad_service` con 0 pastes, 400 palabras, 60 min escritura → puntuación ≥70.
- `autenticidad_service` con 3 pastes → puntuación ≤40.
- `similaridad_service` con texto idéntico → bandera `contenido_repetido = true`.
- `POST /entregar` con tipo=blog y puntuación calculada <20 → 422 con código `calidad_insuficiente`.
- Exportar HTML → no contiene atributos `class=`, ni scripts, ni iframes.

---

## Skill recomendado por tarea

- **T1-T4:** `frontend-skill` (editor Tiptap, hooks, DOM events).
- **T5, T6:** `developer-skill` + algoritmos (scoring, TF-IDF/Jaccard).
- **T7:** `developer-skill` (integración backend).
- **T8, T9:** `developer-skill` + `frontend-skill`.
- **T10:** `testing-skill`.

---

## PROGRESO

- [ ] T1 — BloggerEditor (Tiptap + bloqueos)
- [ ] T2 — useEscrituraTracker hook
- [ ] T3 — Corrector ortográfico
- [ ] T4 — Exportación HTML Blogger
- [ ] T5 — autenticidad_service (scoring)
- [ ] T6 — similaridad_service
- [ ] T7 — Integrar en POST /entregar
- [ ] T8 — Vista admin entregas en revisión
- [ ] T9 — GET /admin/entregas/:id/metadatos
- [ ] T10 — Tests

**Última sesión:** —
**Próximo paso al reanudar:** T1 — componente `BloggerEditor.tsx` con Tiptap, bloqueo de paste de texto (`event.preventDefault()` en `paste`), bloqueo de dictado (listener `input` filtrando `insertReplacementText`), contador de palabras en tiempo real.
