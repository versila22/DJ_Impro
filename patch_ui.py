import os

filepath = '/data/.openclaw/workspace/impro-remote/impro_remote_server.py'
with open(filepath, 'r') as f:
    code = f.read()

# 1. Remplacer les liens morts par les liens dynamiques vers les spectacles
code = code.replace('href="#" class="show-link"', 'href="/show/{{ show.id }}" class="show-link"')

# 2. Ajouter le template HTML pour la vue de détail
HTML_SHOW_DETAIL = '''
HTML_SHOW_DETAIL = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{{ show.title }} - Régisseur IA</title>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; background-color: #121212; color: white; margin: 0; padding: 20px; box-sizing: border-box; }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 20px; }
        .back-btn { color: #1DB954; text-decoration: none; font-weight: bold; }
        h1 { color: white; font-size: 1.5rem; margin: 0; }
        .status-badge { background: #333; padding: 5px 10px; border-radius: 10px; font-size: 0.8rem; }
        .track-list { list-style: none; padding: 0; }
        .track-item { background: #282828; padding: 15px; border-radius: 8px; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;}
        .track-info { display: flex; flex-direction: column; }
        .track-title { font-weight: bold; font-size: 1.1rem; }
        .track-artist { color: #888; font-size: 0.9rem; }
        .track-category { background: #1DB954; color: black; padding: 3px 8px; border-radius: 5px; font-size: 0.8rem; font-weight: bold; }
        .add-btn { background: #1DB954; color: white; border: none; padding: 15px; border-radius: 8px; width: 100%; font-size: 1.1rem; font-weight: bold; cursor: pointer; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="header">
        <a href="/dashboard" class="back-btn">← Retour</a>
        <span class="status-badge">{{ "Passé" if show.status == 'PAST' else "À venir" }}</span>
    </div>
    
    <h1>{{ show.title }}</h1>
    <p style="color: #888;">{{ show.date.strftime('%d/%m/%Y') }}</p>

    <ul class="track-list">
        {% for track in show.tracks %}
        <li class="track-item">
            <div class="track-info">
                <span class="track-title">{{ track.title }}</span>
                <span class="track-artist">{{ track.artist }}</span>
            </div>
            {% if track.category %}
            <span class="track-category">{{ track.category }}</span>
            {% endif %}
        </li>
        {% else %}
        <p style="color: #666; font-style: italic;">Aucune piste dans ce spectacle.</p>
        {% endfor %}
    </ul>

    {% if show.status == 'UPCOMING' %}
    <button class="add-btn" onclick="alert('Module de recherche Spotify (OAuth) en cours de construction !')">➕ Ajouter un titre (Spotify)</button>
    {% endif %}
</body>
</html>
"""
'''

code = code.replace('# --- ROUTES AUTHENTIFICATION ---', HTML_SHOW_DETAIL + '\n# --- ROUTES AUTHENTIFICATION ---')

# 3. Ajouter la route Flask
route_code = '''
@app.route('/show/<int:show_id>')
@login_required
def show_detail(show_id):
    show = Show.query.get_or_404(show_id)
    if show.user_id != current_user.id:
        flash("Accès refusé.")
        return redirect(url_for('dashboard'))
    return render_template_string(HTML_SHOW_DETAIL, show=show)
'''

code = code.replace('# --- ROUTES APPLICATION ---', '# --- ROUTES APPLICATION ---\n' + route_code)

with open(filepath, 'w') as f:
    f.write(code)

print("Patch UI appliqué avec succès.")
