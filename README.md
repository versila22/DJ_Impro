# PA 🤖 Régisseur IA (Anciennement DJ_Impro)

Le premier Régisseur IA Open Source pour le spectacle vivant et l'improvisation théâtrale.

## 🎯 La Vision
Passer d'une simple "télécommande web" à un Agent Autonome (LMM/Audio) capable de regarder, écouter une scène, et de déclencher la musique avec le bon timing et la bonne émotion.

Actuellement en **V1 (Outil de Régie Connecté par Plugins)**.
Prochaine étape **V2 (Évaluation par IA et pipeline vidéo)**.

## 🧩 Architecture par Plugins
Le cœur (Core) est ultra-léger (serveur Flask sans dépendance métier). Les actions sont gérées par des plugins dynamiques.
Consultez [BOUNTIES.md](BOUNTIES.md) pour voir les plugins les plus demandés par la communauté (QLab, Apple Music, DMX) et gagnez des points en les développant !

## 🚀 Installation Rapide
1. Cloner ce projet : `git clone https://github.com/versila22/DJ_Impro.git`
2. Installer les dépendances : `pip install -r requirements.txt`
3. Configurer vos clés de plugins (ex: Spotify API) dans `.env`.
4. Lancer le serveur localement : `python impro_remote_server.py`
Le terminal affichera l'URL `http://<VOTRE_IP_LOCALE>:5000`. Accédez-y depuis votre smartphone.
