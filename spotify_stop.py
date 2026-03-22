import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

def stop_now():
    scope = "user-read-playback-state user-modify-playback-state"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, open_browser=False))
    
    playback = sp.current_playback()
    if playback and playback['is_playing']:
        print(f"🛑 Arrêt immédiat sur {playback['device']['name']}")
        sp.pause_playback(device_id=playback['device']['id'])
    else:
        print("⚠️ Rien n'est en cours de lecture.")

if __name__ == "__main__":
    stop_now()
