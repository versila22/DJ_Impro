import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import time

# Chargement des variables d'environnement
load_dotenv()

def get_spotify_client():
    scope = "user-read-playback-state user-modify-playback-state"
    return spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, open_browser=False))

def fade_out(duration_seconds=5, steps=10):
    sp = get_spotify_client()
    
    # Force le transfert sur ASUSJAY avant le fondu si besoin
    devices = sp.devices()['devices']
    target_device = next((d for d in devices if "ASUSJAY" in d['name'].upper()), None)
    
    if target_device:
        print(f"🔄 Transfert de la lecture vers {target_device['name']}...")
        sp.transfer_playback(device_id=target_device['id'], force_play=True)
        time.sleep(2) # Temps de stabilisation
    
    # 1. Récupérer l'état actuel
    playback = sp.current_playback()
    if not playback or not playback['is_playing']:
        print("⚠️ Aucune lecture en cours pour faire un fondu.")
        return

    start_volume = playback['device']['volume_percent']
    device_id = playback['device']['id']
    
    print(f"📉 Début du fondu sur {playback['device']['name']} (Volume: {start_volume}%)")
    
    # 2. Calculer le pas de réduction
    sleep_time = duration_seconds / steps
    volume_step = start_volume / steps
    
    current_volume = start_volume
    for i in range(steps):
        current_volume -= volume_step
        try:
            sp.volume(int(max(0, current_volume)), device_id=device_id)
            time.sleep(sleep_time)
        except Exception as e:
            print(f"❌ Erreur lors du fondu : {e}")
            break
            
    # 3. Mettre en pause à la fin
    sp.pause_playback(device_id=device_id)
    # 4. Remettre le volume à l'état initial (optionnel, pour la prochaine fois)
    sp.volume(start_volume, device_id=device_id)
    
    print("✅ Fondu terminé. Lecture en pause.")

if __name__ == "__main__":
    fade_out(duration_seconds=5)
