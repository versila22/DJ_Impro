import os

filepath = '/data/.openclaw/workspace/impro-remote/impro_remote_server.py'
with open(filepath, 'r') as f:
    code = f.read()

# 1. Ajouter l'import
code = code.replace('from models import', 'from spotify_oauth import get_auth_url, save_token_from_code\nfrom models import')

# 2. Remplacer le bouton "Lier mon compte Spotify" dans le Dashboard
old_spotify_btn = '<a href="#" class="spotify-connect-btn">🔗 Lier mon compte Spotify</a>'
new_spotify_btn = '<a href="/login/spotify" class="spotify-connect-btn">🔗 Lier mon compte Spotify</a>'
code = code.replace(old_spotify_btn, new_spotify_btn)

# 3. Ajouter les routes d'authentification Spotify
routes_oauth = """
# --- ROUTES OAUTH SPOTIFY ---

@app.route('/login/spotify')
@login_required
def login_spotify():
    '''Redirige l'utilisateur vers la page de connexion de Spotify'''
    auth_url = get_auth_url()
    return redirect(auth_url)

@app.route('/callback')
@login_required
def callback_spotify():
    '''Route de retour après autorisation Spotify'''
    code = request.args.get('code')
    if code:
        if save_token_from_code(code):
            flash("Votre compte Spotify a été lié avec succès !")
        else:
            flash("Erreur lors de la liaison de votre compte Spotify.")
    else:
        flash("Autorisation refusée par Spotify.")
    return redirect(url_for('dashboard'))

"""
code = code.replace('# --- ROUTES APPLICATION ---', routes_oauth + '\n# --- ROUTES APPLICATION ---')

with open(filepath, 'w') as f:
    f.write(code)

print("Patch Serveur (OAuth) appliqué avec succès.")
