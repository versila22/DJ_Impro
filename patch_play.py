import os

filepath = '/data/.openclaw/workspace/impro-remote/impro_remote_server.py'
with open(filepath, 'r') as f:
    code = f.read()

# 1. Ajouter l'import
code = code.replace('from spotify_oauth import', 'from spotify_oauth import get_valid_token, get_auth_url, save_token_from_code\nimport spotipy\n')

# 2. Modifier le HTML_SHOW_DETAIL pour rendre les pistes cliquables (action JavaScript)
old_track_item = '<li class="track-item">'
new_track_item = '<li class="track-item" style="cursor: pointer;" onclick="playTrack(\'{{ track.spotify_uri }}\')">'
code = code.replace(old_track_item, new_track_item)

# 3. Ajouter le script JavaScript dans HTML_SHOW_DETAIL
script_js = """
    <script>
        function playTrack(uri) {
            if (!uri || uri === 'None') {
                alert("Aucun lien Spotify (URI) associé à ce titre.");
                return;
            }
            fetch('/api/play/' + uri)
                .then(r => r.json())
                .then(data => {
                    if(data.success) {
                        alert("▶️ Lecture de : " + data.message);
                    } else {
                        alert("Erreur: " + data.message);
                    }
                })
                .catch(e => { alert('Erreur réseau.'); });
        }
    </script>
</body>
"""
code = code.replace('</body>', script_js)

# 4. Ajouter la route Flask pour lire une piste via l'API Spotify
route_play = """
@app.route('/api/play/<path:uri>')
@login_required
def play_track(uri):
    '''Lance la lecture d'une piste spécifique sur le compte Spotify de l'utilisateur'''
    token = get_valid_token()
    if not token:
        return jsonify({"success": False, "message": "Compte Spotify non lié ou token expiré."}), 401
        
    try:
        sp = spotipy.Spotify(auth=token)
        # On lance la lecture (nécessite un appareil actif sur Spotify)
        sp.start_playback(uris=[uri])
        return jsonify({"success": True, "message": uri})
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 404:
             return jsonify({"success": False, "message": "Aucun appareil Spotify actif trouvé. Lancez Spotify sur votre téléphone ou PC."}), 404
        return jsonify({"success": False, "message": str(e)}), 500
    except Exception as e:
        return jsonify({"success": False, "message": "Erreur inattendue."}), 500
"""
code = code.replace('# --- ROUTES EXISTANTES DE L\'API REST ---', '# --- ROUTES EXISTANTES DE L\'API REST ---\n' + route_play)

with open(filepath, 'w') as f:
    f.write(code)

print("Patch Lecture Piste appliqué avec succès.")
