---
description: Analiza los cambios y crea un commit bien documentado
agent: build
---

Cambios en stage:
!`git diff --staged`

Archivos modificados (sin stage):
!`git status --short`

Últimos commits (para mantener el mismo estilo):
!`git log --oneline -5`

Con esta información:
1. Si no hay nada en stage, dime qué archivos conviene agregar con `git add` y espera confirmación.
2. Redacta un mensaje de commit siguiendo Conventional Commits: `tipo(alcance): resumen corto en imperativo`.
3. Agrega un cuerpo que explique el *qué* y sobre todo el *por qué* del cambio (no repitas el diff línea por línea).
4. Si hay breaking changes o se relaciona con un issue, añade un footer (`BREAKING CHANGE:` o `Refs #123`).
5. Muéstrame el mensaje propuesto antes de ejecutar `git commit`. Solo ejecútalo si confirmo.