import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import sys

# Chargement des variables d'environnement
load_dotenv()

def get_spotify_client():
    scope = "user-read-playback-state user-modify-playback-state playlist-read-private"
    return spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, open_browser=False))

def find_playlist(sp, name):
    results = sp.current_user_playlists()
    for item in results['items']:
        if name.lower() in item['name'].lower():
            return item
    return None

def start_impro_session(playlist_name="Impro"):
    sp = get_spotify_client()
    
    # 1. Trouver la playlist
    playlist = find_playlist(sp, playlist_name)
    if not playlist:
        print(f"❌ Playlist '{playlist_name}' non trouvée.")
        return

    print(f"🎵 Playlist trouvée : {playlist['name']}")

    # 2. Vérifier les devices actifs
    devices = sp.devices()['devices']
    active_device = next((d for d in devices if d['is_active']), None)
    
    # Préférence pour ASUSJAY si disponible pour le volume
    asus = next((d for d in devices if "ASUSJAY" in d['name'].upper()), None)
    if asus:
        active_device = asus

    if not active_device:
        if devices:
            active_device = devices[0]
            print(f"⚠️ Transfert sur : {active_device['name']}")
            sp.transfer_playback(device_id=active_device['id'], force_play=False)
        else:
            print("❌ Aucun device Spotify détecté.")
            return

    # 3. Lancer la lecture
    print(f"🚀 Lancement sur : {active_device['name']}")
    try:
        sp.start_playback(device_id=active_device['id'], context_uri=playlist['uri'])
        sp.shuffle(state=True, device_id=active_device['id'])
        print("✅ Lecture OK.")
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    # Lecture de l'argument s'il existe
    p_name = sys.argv[1] if len(sys.argv) > 1 else "Impro"
    start_impro_session(p_name)
