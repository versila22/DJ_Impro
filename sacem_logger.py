import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import time
import json

load_dotenv()

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sacem_log.json")
CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")

def get_spotify_client():
    scope = "playlist-read-private playlist-modify-private playlist-modify-public user-read-playback-state"
    auth_manager = SpotifyOAuth(
        scope=scope,
        open_browser=False, 
        cache_path=CACHE_PATH
    )
    # validate_token refresh automatiquement si expiré via le refresh_token du cache
    token_info = auth_manager.validate_token(auth_manager.get_cached_token())
    if not token_info:
        return None
    
    return spotipy.Spotify(auth=token_info['access_token'])

def log_current_track():
    sp = get_spotify_client()
    if not sp: 
        print("❌ Token invalide ou expiré.")
        return

    try:
        playback = sp.current_playback()
    except Exception as e:
        print(f"❌ Erreur playback: {e}")
        return
    
    if not playback or not playback['item'] or not playback['is_playing']:
        return

    track = playback['item']
    track_id = track['id']
    
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                history = json.load(f)
        except: history = {}
    else:
        history = {}

    now = time.time()
    
    if track_id in history:
        if now - history[track_id]['last_seen'] < 20: 
            history[track_id]['duration_sec'] += (now - history[track_id]['last_seen'])
        history[track_id]['last_seen'] = now
    else:
        history[track_id] = {
            "title": track['name'],
            "artist": track['artists'][0]['name'],
            "duration_sec": 0,
            "last_seen": now,
            "first_seen": now
        }

    with open(LOG_FILE, 'w') as f:
        json.dump(history, f, indent=4)
    print(f"✅ Loggé : {track['name']}")

if __name__ == "__main__":
    log_current_track()
