# Plan — Git init + push GitHub dora-rag

**Source** : `t_9b94ae6b` · **Planner** : planner · **Date** : 2026-06-28

## Contexte

Le projet dora-rag est complet dans `/opt/data/workspace/dora-rag/` (Phase 1 terminée, package installable via hatchling).
Pas de `.git`, pas de remote GitHub. Le repo cible est `liboudou/dora-rag`.
Le token `GITHUB_TOKEN` est disponible dans l'environnement.

## Décomposition

| # | Tâche | Fichiers | Critère d'acceptation | Tests |
|---|-------|----------|----------------------|-------|
| 1 | Créer `.gitignore` adapté au projet Python | `/opt/data/workspace/dora-rag/.gitignore` | Le fichier contient les patterns pour: `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `dist/`, `*.egg-info/`, `.env`, `*.pdf` (data/). Vérification: `git status` ne montre aucun fichier indésirable staged. | `cat .gitignore \| grep -c venv` renvoie ≥1 |
| 2 | Initialiser le dépôt git et commit initial | `/opt/data/workspace/dora-rag/.git/` (créé) | `git log --oneline` affiche 1 commit sur branche `main` avec message clair. Tous les fichiers du projet sont trackés. | `git status` renvoie "nothing to commit, working tree clean" |
| 3 | Créer le repo GitHub `liboudou/dora-rag` via API REST | Repo GitHub créé | `curl -s -o /dev/null -w "%{http_code}" https://api.github.com/repos/liboudou/dora-rag` renvoie `200`. | La commande ci-dessus retourne 200 |
| 4 | Ajouter le remote origin et push vers GitHub | Remote configuré, push réussi | `git remote -v` affiche `origin` pointant vers `https://github.com/liboudou/dora-rag.git`. `git log --oneline origin/main` affiche le même commit que local. | `git push` s'exécute sans erreur |

## Ordre d'exécution

1. Tâche 1 — `.gitignore` (prérequis, évite de track les fichiers indésirables)
2. Tâche 2 — `git init` + commit (dépend de 1 : le .gitignore doit être en place avant le commit)
3. Tâche 3 — Création du repo GitHub via API (indépendante de 2, peut être en parallèle)
4. Tâche 4 — remote add + push (dépend de 2 et 3 : commit local + repo GitHub doit exister)

## Coût estimé

- **Fichiers modifiés** : 1 (.gitignore créé) + 1 (.git créé)
- **Taille** : faible
- **Complexité** : simple
- **Risque** : faible (GITHUB_TOKEN disponible, repo cible clairement défini)

## Notes pour le dev

- Le `.gitignore` doit couvrir: `.venv/`, `__pycache__/`, `*.pyc`, `*.pyo`, `.pytest_cache/`, `dist/`, `*.egg-info/`, `.env`, `data/*.pdf` (ou `*.pdf`), `import_test.py`, `test_import.py` (fichiers de test éphémères à la racine)
- La création du repo GitHub utilise l'API REST avec le token: `curl -X POST https://api.github.com/user/repos -H "Authorization: Bearer $GITHUB_TOKEN" -d '{"name":"dora-rag","auto_init":false}'`
- Le push doit utiliser `git push -u origin main` pour configurer l'upstream
- Branche: `main` (pas de branche feat/ fix/ car c'est l'init du repo)
