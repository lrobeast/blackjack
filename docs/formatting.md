# Configuration de formatage pour le projet

Cette documentation explique comment activer `black` pour le projet et pour les futurs projets.

Pour ce projet

- Installez les dépendances de développement:

```bash
pip install -r dev-requirements.txt
```

- Le workspace contient `.vscode/settings.json` qui active `editor.formatOnSave` et définit `black` comme formateur.

Pour les futurs projets

- Copiez `.vscode/settings.json` et `pyproject.toml` dans le nouveau dépôt.
- Installez `black` dans l'environnement de développement (`pip install black`) ou utilisez `dev-requirements.txt`.

Configurer au niveau utilisateur (optionnel)

Ouvrez les Paramètres utilisateur VS Code et ajoutez ces clés JSON:

```json
{
  "editor.formatOnSave": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length", 88]
}
```
