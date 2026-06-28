# SESION TEMPLATE — Resuena

> Estos dos prompts son los **rituales fijos** de cada sesión de trabajo.
> Funcionan idénticamente en **Claude Code** y **OpenCode**.
> Copia el bloque entre `===` y pégalo al inicio o final de cada sesión.

---

## A) PROMPT DE INICIO DE SESIÓN

```
=== INICIO DE SESIÓN — Resuena ===

Antes de hacer cualquier modificación de código, sigue estos pasos en orden:

1. Lee el archivo `CLAUDE.md` en la raíz del repo.
2. Lee `docs/PLAN.md` y revisa la tabla de fases.
3. Identifica la FASE ACTIVA: la primera marcada `[~]` (en progreso), o si no hay
   ninguna, la primera `[ ]` (pendiente) inmediatamente posterior a la última `[x]`
   completada.
4. Abre el archivo `docs/fase-XX.md` correspondiente a esa fase y lee:
   - La sección "Contexto".
   - La sección "PROGRESO" al final del archivo (estado real de tareas).
   - La línea "Próximo paso al reanudar".
5. Lee la sección "CHECKPOINT" al final de `docs/PLAN.md` (último avance global).
6. Responde al usuario en una sola línea con el siguiente formato exacto:

   "Fase XX — <título>  |  Progreso: N/M tareas  |  Próximo paso: <descripción>"

7. NO empieces a codificar. Espera confirmación explícita del usuario antes de
   tocar cualquier archivo. Si el usuario pide cambiar de fase, valida que las
   dependencias estén en `[x]` antes de aceptar.

Reglas durante la sesión:
- Consulta el skill recomendado para cada tarea (ver `docs/AGENTES.md`).
- Marca tareas como `[~]` en progreso al empezarlas y `[x]` al completarlas.
- No introduzcas tareas no listadas sin acordarlas con el usuario primero.
- Aplica las "Reglas no negociables" de `CLAUDE.md` en cada cambio.

=== FIN INSTRUCCIONES DE INICIO ===
```

---

## B) PROMPT DE CIERRE DE SESIÓN

```
=== CIERRE DE SESIÓN — Resuena ===

Ejecuta los siguientes pasos en orden estricto antes de terminar la sesión:

1. Identifica la fase trabajada en esta sesión. Abre `docs/fase-XX.md`.

2. Actualiza checkboxes:
   - Marca `[x]` las tareas que se completaron por completo.
   - Marca `[~]` la tarea que quedó parcialmente avanzada (si aplica).
   - Si surgieron sub-tareas no previstas y aceptadas con el usuario,
     agrégalas al checklist con `[ ]`.

3. Actualiza la sección PROGRESO de `docs/fase-XX.md`:
   - "Última sesión:" → fecha de hoy en formato YYYY-MM-DD.
   - "Próximo paso al reanudar:" → descripción concreta del siguiente paso,
     incluyendo número de tarea (ej. "T5 — implementar endpoint X en archivo Y").

4. Si la fase completó TODAS sus tareas:
   - En `docs/PLAN.md`, cambia `[ ]` o `[~]` de esa fila a `[x]`.
   - Cambia la siguiente fase (en orden de dependencias) de `[ ]` a `[~]`.

5. Actualiza la sección CHECKPOINT al final de `docs/PLAN.md`:
   - "Fecha último avance:" → fecha de hoy.
   - "Última fase tocada:" → "Fase XX — <título>".
   - "Último archivo modificado:" → ruta exacta del último archivo tocado.
   - "Próxima acción al reanudar:" → mismo texto que pusiste en el paso 3.
   - "Notas de handoff:" → solo si cambia de modelo/agente. Si no aplica: "ninguna".

6. Actualiza la línea de estado en `CLAUDE.md` (sección "Estado del proyecto")
   con la fase activa actual.

7. Verifica con `git status` qué archivos cambiaron en esta sesión.

8. Haz commit con este formato exacto:

   chore(fase-XX): <resumen breve de lo hecho> — checkpoint <YYYY-MM-DD>

   Donde:
   - XX es el número de la fase activa con cero a la izquierda (ej. 03).
   - <resumen breve> es máximo 10 palabras describiendo lo principal.
   - <YYYY-MM-DD> es la fecha de hoy.

9. NO hagas push automático. Pregunta al usuario si quiere pushear.

10. Imprime al usuario un resumen final de 3 líneas:
    - Lo que se completó hoy.
    - Próximo paso exacto al reanudar.
    - Recomendación de modelo para la próxima sesión (ver `docs/AGENTES.md`).

=== FIN INSTRUCCIONES DE CIERRE ===
```

---

## Compatibilidad cruzada

| Aspecto | Claude Code | OpenCode |
|---------|-------------|----------|
| Lectura de archivos | Tool Read | Tool Read (equivalente) |
| Edición de checkboxes | Tool Edit | Tool Edit (equivalente) |
| Commit | Bash → `git commit` | Bash → `git commit` |
| Convención de modelos | `claude-opus-4-7` / `claude-sonnet-4-6` | `o3-mini` / `gpt-4o` / `gpt-4o-mini` |
| Skills | `.claude/skills/` | `.opencode/skills/` |

---

## Notas de uso

- Si el usuario interrumpe a mitad de una tarea, marca `[~]` en lugar de `[x]`.
- Si descubres que una fase tiene un bloqueador no resuelto, **detén el trabajo** y reporta al usuario.
- Si una tarea cambia de alcance significativamente, edita la descripción en `docs/fase-XX.md`.
- **Nunca** marques `[x]` sin verificar el criterio de "done" descrito en la fase.
