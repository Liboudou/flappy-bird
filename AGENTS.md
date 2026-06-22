# AGENTS.md — règles de travail dans /workspace (hermes-sandbox)

Ce fichier est injecté automatiquement dans le contexte des agents (`--workdir`).

## Structure
- Un projet = un dossier `./<nom-projet>/`. N'écris jamais à la racine sauf ce fichier, README, .gitignore.
- `kb/` est la knowledge-base montée — **ne la modifie pas** depuis ici (c'est le rôle de `researcher`).

## Git
- Branche par ticket : `feat/<id>` ou `fix/<id>`. Pas de commit direct sur `main`.
- Commits petits et atomiques, messages clairs (Conventional Commits apprécié).
- Push sur la branche, puis laisse la chaîne Kanban dispatcher le `reviewer`.

## Qualité (gate CI local actif)
Un hook `pre_tool_call` lance les tests/lint **avant** `kanban_complete` et **bloque** si ça casse.
Pour que le gate soit utile sur un projet Python :
- mets un `pyproject.toml` + un dossier `tests/`,
- installe les deps dans un venv local `./<projet>/.venv` (le gate l'active automatiquement).
Un hook `post_tool_call` formate les fichiers modifiés (ruff/prettier/gofmt) après chaque édition.

## Définition de « terminé »
Code correct, testé (tests verts), lisible, commité et poussé. Sinon → `kanban_block` avec la question.
