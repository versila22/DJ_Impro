import os
import time
from spotipy.oauth2 import SpotifyOAuth
from models import db, SpotifyToken
from flask_login import current_user

# --- CONFIGURATION SPOTIFY ---
# Doit correspondre à l'URL de redirection configurée sur le Dashboard Spotify Dev
 
SCOPE = "user-read-playback-state user-modify-playback-state playlist-read-private"

def get_spotify_oauth(redirect_uri):
    """Crée l'objet SpotifyOAuth avec les clés du .env"""
    return SpotifyOAuth(
        client_id=os.environ.get("SPOTIPY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=redirect_uri,
        scope=SCOPE,
        open_browser=False,
        cache_handler=None # On gère le cache nous-mêmes via la BDD
    )

def get_auth_url(redirect_uri):
    """Génère l'URL de connexion Spotify pour l'utilisateur"""
    sp_oauth = get_spotify_oauth(redirect_uri)
    return sp_oauth.get_authorize_url()

def save_token_from_code(code, redirect_uri):
    """Échange le code de Spotify contre un token et le sauvegarde en BDD"""
    sp_oauth = get_spotify_oauth(redirect_uri)
    try:
        token_info = sp_oauth.get_access_token(code, as_dict=True)
        
        # Sauvegarde en BDD
        existing_token = SpotifyToken.query.filter_by(user_id=current_user.id).first()
        if existing_token:
            existing_token.token_info = token_info
        else:
            new_token = SpotifyToken(user_id=current_user.id, token_info=token_info)
            db.session.add(new_token)
            
        db.session.commit()
        return True
    except Exception as e:
        print(f"Erreur OAuth Spotify: {e}")
        return False

def get_valid_token(redirect_uri='http://localhost:5000/callback'):
    """Récupère le token de l'utilisateur, le rafraîchit si besoin"""
    if not current_user.is_authenticated:
        return None
        
    token_obj = SpotifyToken.query.filter_by(user_id=current_user.id).first()
    if not token_obj:
        return None
        
    token_info = token_obj.token_info
    sp_oauth = get_spotify_oauth(redirect_uri)
    
    # Vérifie si le token a expiré (avec une marge de 60s)
    now = int(time.time())
    is_expired = token_info.get('expires_at') - now < 60
    
    if is_expired:
        print("Rafraîchissement du token Spotify...")
        try:
            token_info = sp_oauth.refresh_access_token(token_info.get('refresh_token'))
            token_obj.token_info = token_info
            db.session.commit()
        except Exception as e:
            print(f"Erreur rafraîchissement token: {e}")
            # Token invalide, on le supprime
            db.session.delete(token_obj)
            db.session.commit()
            return None
            
    return token_info.get('access_token')
