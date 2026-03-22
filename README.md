# Impro Remote + SACEM Tracker

Un outil de télécommande via interface web (PWA) pour la gestion de la musique et des playlists Spotify lors de spectacles d'improvisation, incluant un suivi de diffusion (log SACEM).

## Prérequis
- Python 3.8+
- Un compte Spotify (Premium recommandé pour le contrôle de lecture)
- Une application développeur Spotify (pour les tokens API)

## Installation

1. Cloner ou télécharger ce projet.
2. Installer les dépendances :
   ```bash
   pip install -r requirements.txt
   ```
3. Créer un fichier `.env` à la racine et y ajouter vos accès Spotify :
   ```env
   SPOTIPY_CLIENT_ID='votre_client_id'
   SPOTIPY_CLIENT_SECRET='votre_client_secret'
   SPOTIPY_REDIRECT_URI='http://localhost:8080'
   ```

## Lancement

Exécutez le serveur web local (depuis le dossier du projet) :
```bash
python impro_remote_server.py
```
Le terminal affichera l'URL `http://<VOTRE_IP_LOCALE>:5000`. Vous pouvez y accéder depuis n'importe quel appareil connecté au même réseau Wi-Fi (mobile, tablette) pour contrôler la musique.
