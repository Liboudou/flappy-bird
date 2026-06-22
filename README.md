# hermes-sandbox

Bac à sable des projets développés par l'équipe d'agents Hermes (`dev` / `reviewer` / `ops`).
Monté sur `/workspace` dans le conteneur Hermes.

## Convention

- **Un dossier = un projet** : `./<nom-projet>/`.
- Travail par branche : `feat/<ticket>`, `fix/<ticket>` — jamais directement sur `main`.
- Le `reviewer` relit via `git diff main...<branche>`, le `ops` merge sur `main`.
- `kb/` est un montage de la knowledge-base (Obsidian) — **non tracké** par ce repo.

## Cycle de vie

Ce repo est fait pour **prototyper/tester**. Dès qu'un projet devient sérieux,
il doit **migrer vers son propre repo** (comme `Slice` dans l'orga `Slice-IA`).
Voir `AGENTS.md` pour les règles que suivent les agents.
