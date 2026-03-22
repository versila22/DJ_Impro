# Architecture & Vision du Projet DJ_Impro

Ce document est le "Post-Mortem" permanent et la boussole technique du projet DJ_Impro.

## 🏗️ L'État de l'Art (V1)
Actuellement, DJ_Impro repose sur une architecture simple et robuste :

- **Le Core (Contrôle UI / PWA) :** `impro_remote_server.py` (Flask) expose une interface web PWA sur le réseau local. Il agit comme le chef d'orchestre, sans connaître la complexité de l'audio.
- **Les Workers (Actionneurs) :** Des scripts Python isolés exécutent les ordres (Play, Stop, Fade).
  - `impro_launcher.py` : Connexion et lancement Spotify via Spotipy.
  - `spotify_stop.py`, `spotify_fadeout.py` : Gestion du volume (Fade In/Out).
- **Le Légal (SACEM Tracker) :** `sacem_logger.py` scrute le cache Spotify et génère un log CSV/JSON des morceaux diffusés.

### Sécurité et Contraintes
- **DRM & Streaming :** Nous passons par l'API Spotify, ce qui induit une latence réseau (1 à 2 secondes).
- **Quotas API :** Chaque instance locale doit utiliser son propre `.env` (Client ID/Secret Spotify) pour répartir la charge sur l'API Spotify et éviter les bannissements (Tokenomics).

## 🚀 La Vision (V2 et au-delà)
Le projet vise une transition d'un "outil manuel" vers un **Agent Autonome de Régie**.

### 1. La Modularisation "Core vs Plugins" (Axe Horizontal)
L'objectif est d'isoler la logique de l'interface et du routage (le Core) des exécuteurs métier (les Plugins).
- Si un régisseur professionnel veut utiliser **QLab** au lieu de Spotify, il écrira un `qlab_plugin.py` sans modifier le code réseau Flask.
- Gestion du **DMX** pour synchroniser lumière et son.

### 2. Le Pipeline IA & Évaluation (Axe Vertical)
Nous allons intégrer un système "Self-RAG" pour l'impro :
- **Ingestion :** Un set de données composé de vidéos YouTube d'improvisation fournies par la communauté.
- **Perception :** Transcription de l'audio (Whisper) localement (coût 0).
- **Décision :** Un modèle (LMM/LLM type Gemini ou local via ollama) lit le flux et génère des logs d'actions musicales (`{"action": "fade_in", "emotion": "tension"}`).
- **Self-Training :** Une boucle DSPy avec "Human-in-the-loop" pour optimiser les prompts en fonction du feedback du régisseur (ex: "Musique trop tôt").

Nous bâtissons un CI/CD audiovisuel où les geeks improvisateurs pourront uploader leurs vidéos pour entraîner le modèle.
