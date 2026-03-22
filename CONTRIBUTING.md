# Contribuer à DJ_Impro

Merci de l'intérêt que vous portez à DJ_Impro ! Ce projet vise à devenir le standard de la régie improvisée, propulsé par la communauté et (bientôt) par l'IA.

## 🧠 Philosophie (L'Architecte Pragmatique)
- **Stabilité avant tout :** En spectacle, un bug = un blanc sur scène. Votre code doit être robuste.
- **Modularité :** Ne modifiez pas le "Core" (serveur Flask) pour ajouter une fonctionnalité métier très spécifique. Pensez "Plugin" (ex: QLab, DMX).
- **Tokenomics & Quotas :** Chaque troupe doit utiliser ses propres clés d'API (Spotify, etc.). Ne hardcodez jamais de tokens.

## 🛠 Environnement de Développement
1. Forkez le dépôt et clonez-le en local.
2. Créez un environnement virtuel : `python -m venv venv && source venv/bin/activate`
3. Installez les dépendances : `pip install -r requirements.txt`
4. Copiez `.env.example` en `.env` (si existant) et configurez vos clés.

## 🚀 Processus de Pull Request (PR)
1. Créez une branche explicite : `feature/nom-de-votre-fonctionnalite` ou `bugfix/nom-du-bug`.
2. Documentez votre code (Docstrings) et respectez PEP8.
3. Testez votre code en condition réelle (lancez le serveur localement).
4. Soumettez votre PR avec une description claire du problème résolu ou de la valeur ajoutée.
5. Un mainteneur fera la revue de code. Des ajustements pourront être demandés.

*Note : Les premières "Good First Issues" sont disponibles dans l'onglet Issues.*
