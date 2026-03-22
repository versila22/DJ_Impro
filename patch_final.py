import os

# --- Patch spotify_oauth.py ---
oauth_path = '/data/.openclaw/workspace/impro-remote/spotify_oauth.py'
with open(oauth_path, 'r') as f:
    oauth_code = f.read()

# On supprime la variable globale REDIRECT_URI
oauth_code = oauth_code.replace("REDIRECT_URI = 'http://localhost:5000/callback'", "")
# On modifie la fonction pour qu'elle accepte l'URI en paramètre
oauth_code = oauth_code.replace("def get_spotify_oauth():", "def get_spotify_oauth(redirect_uri):")
oauth_code = oauth_code.replace("redirect_uri=REDIRECT_URI,", "redirect_uri=redirect_uri,")
# On propage le paramètre
oauth_code = oauth_code.replace("def get_auth_url():", "def get_auth_url(redirect_uri):")
oauth_code = oauth_code.replace("sp_oauth = get_spotify_oauth()", "sp_oauth = get_spotify_oauth(redirect_uri)")
oauth_code = oauth_code.replace("def save_token_from_code(code):", "def save_token_from_code(code, redirect_uri):")
oauth_code = oauth_code.replace("sp_oauth = get_spotify_oauth()", "sp_oauth = get_spotify_oauth(redirect_uri)", 1) # Remplacer qu'une fois
oauth_code = oauth_code.replace("def get_valid_token():", "def get_valid_token(redirect_uri='http://localhost:5000/callback'):")
oauth_code = oauth_code.replace("sp_oauth = get_spotify_oauth()", "sp_oauth = get_spotify_oauth(redirect_uri)", 1) # Remplacer qu'une fois

with open(oauth_path, 'w') as f:
    f.write(oauth_code)

print("Patch OAuth appliqué.")

# --- Patch impro_remote_server.py ---
server_path = '/data/.openclaw/workspace/impro-remote/impro_remote_server.py'
with open(server_path, 'r') as f:
    server_code = f.read()

# On modifie les appels pour passer l'URL dynamique
server_code = server_code.replace("auth_url = get_auth_url()", "redirect_uri = url_for('callback_spotify', _external=True)\\n    auth_url = get_auth_url(redirect_uri)")
server_code = server_code.replace("if save_token_from_code(code):", "redirect_uri = url_for('callback_spotify', _external=True)\\n        if save_token_from_code(code, redirect_uri):")
# On corrige l'import
server_code = server_code.replace("from spotify_oauth import get_valid_token, get_auth_url, save_token_from_code", "from spotify_oauth import get_auth_url, save_token_from_code, get_valid_token")

with open(server_path, 'w') as f:
    f.write(server_code)

print("Patch Serveur (OAuth dynamique) appliqué.")

