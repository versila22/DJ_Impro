import os
import sys
import subprocess
import socket
import importlib.util
from flask import Flask, render_template_string, request, jsonify, send_file, redirect, url_for, flash
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import json
import csv
from datetime import datetime
from spotify_oauth import get_auth_url, save_token_from_code, get_valid_token
import spotipy
from models import db, User, Show, ShowTrack, SpotifyToken
from flask_bcrypt import Bcrypt

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-key-for-dev-only') # À changer en prod

# Configuration DB
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(SCRIPTS_DIR, 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt = Bcrypt(app)

# Configuration Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Configuration existante
PLUGINS_DIR = os.path.join(SCRIPTS_DIR, "plugins")
LOG_FILE = os.path.join(SCRIPTS_DIR, "sacem_log.json")
VENV_PYTHON = sys.executable

plugins = {}

def load_plugins():
    global plugins
    plugins = {}
    if not os.path.exists(PLUGINS_DIR):
        return
    for filename in os.listdir(PLUGINS_DIR):
        if filename.endswith("_plugin.py"):
            name = filename[:-3]
            filepath = os.path.join(PLUGINS_DIR, filename)
            spec = importlib.util.spec_from_file_location(name, filepath)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "get_config") and hasattr(mod, "execute"):
                plugins[name] = {
                    "module": mod,
                    "config": mod.get_config()
                }

load_plugins()

# --- HTML TEMPLATES (Simplifiés pour le moment, on les externalisera plus tard) ---
HTML_LOGIN = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connexion - Régisseur IA</title>
    <style>
        body { font-family: system-ui; background-color: #121212; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: #282828; padding: 40px; border-radius: 15px; text-align: center; width: 300px; }
        input { width: 100%; padding: 10px; margin: 10px 0; border-radius: 5px; border: none; box-sizing: border-box; }
        button { background: #1DB954; color: white; border: none; padding: 10px 20px; border-radius: 20px; font-weight: bold; cursor: pointer; width: 100%; margin-top: 10px; }
        .error { color: #e74c3c; font-size: 0.9em; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2 style="color: #1DB954; margin-bottom: 20px;">Connexion</h2>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            {% for message in messages %}
              <div class="error">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Nom d'utilisateur" required>
            <input type="password" name="password" placeholder="Mot de passe" required>
            <button type="submit">Se connecter</button>
        </form>
    </div>
</body>
</html>
"""

HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>PA 🤖 Régisseur IA - Dashboard</title>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; background-color: #121212; color: white; margin: 0; padding: 20px; display: flex; flex-direction: column; min-height: 100vh; box-sizing: border-box; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #333; padding-bottom: 10px; }
        h1 { color: #1DB954; font-size: 1.5rem; margin: 0; }
        .logout-btn { background: transparent; color: #888; border: 1px solid #555; padding: 5px 10px; border-radius: 5px; text-decoration: none; font-size: 0.9rem; }
        h2 { font-size: 1.2rem; margin-top: 20px; border-bottom: 1px solid #333; padding-bottom: 5px; }
        .show-list { list-style: none; padding: 0; margin: 0; }
        .show-item { background: #282828; margin-bottom: 10px; padding: 15px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
        .show-link { color: white; text-decoration: none; font-weight: bold; flex-grow: 1; }
        .show-date { color: #888; font-size: 0.9em; margin-right: 15px; }
        .spotify-connect-btn { background: #1DB954; color: white; padding: 10px 20px; border-radius: 20px; text-decoration: none; font-weight: bold; display: inline-block; margin-bottom: 20px; text-align: center; }
        .new-show-form { display: flex; gap: 10px; margin-bottom: 20px; }
        .new-show-form input { flex-grow: 1; padding: 10px; border-radius: 5px; border: none; background: #333; color: white; }
        .new-show-form button { background: #1DB954; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer; font-weight: bold; }
        
        /* Styles de la télécommande existante */
        .playlist-btn { border: none; border-radius: 15px; padding: 20px; margin-bottom: 15px; color: white; font-size: 1.1rem; font-weight: bold; width: 100%; display: flex; align-items: center; gap: 15px; cursor: pointer; }
        .playlist-btn:active { transform: scale(0.98); }
        .footer-btns { margin-top: auto; display: flex; flex-wrap: wrap; gap: 15px; padding-bottom: 20px; padding-top: 20px;}
        .action-btn { flex: 1; color: white; border: none; border-radius: 12px; padding: 20px; font-weight: bold; font-size: 1rem; cursor: pointer; }
        .action-btn:active { transform: scale(0.98); }
        .sacem-btn { background: #3498db; margin-top: 10px; width: 100%; flex: none; }
        #status { text-align: center; font-size: 0.8rem; color: #666; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>PA 🤖 Régisseur IA</h1>
        <a href="/logout" class="logout-btn">Déconnexion ({{ current_user.username }})</a>
    </div>

    {% if not has_spotify_token %}
    <div style="background: #333; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center;">
        <p style="margin-top: 0;">Pour utiliser le régisseur, vous devez lier votre compte Spotify.</p>
        <a href="/login/spotify" class="spotify-connect-btn">🔗 Lier mon compte Spotify</a>
    </div>
    {% endif %}

    <h2>Spectacles À Venir</h2>
    <form class="new-show-form" method="POST" action="/create_show">
        <input type="text" name="title" placeholder="Titre du nouveau spectacle (ex: Match d'Impro)" required>
        <button type="submit">Créer</button>
    </form>
    
    <ul class="show-list">
        {% for show in upcoming_shows %}
        <li class="show-item">
            <a href="/show/{{ show.id }}" class="show-link">{{ show.title }}</a>
            <span class="show-date">{{ show.date.strftime('%Y-%m-%d') }}</span>
        </li>
        {% else %}
        <li style="color: #666; font-style: italic;">Aucun spectacle à venir.</li>
        {% endfor %}
    </ul>

    <h2>Spectacles Passés</h2>
    <ul class="show-list">
        {% for show in past_shows %}
        <li class="show-item">
            <a href="/show/{{ show.id }}" class="show-link">{{ show.title }}</a>
            <span class="show-date">{{ show.date.strftime('%Y-%m-%d') }}</span>
        </li>
        {% else %}
        <li style="color: #666; font-style: italic;">Aucun historique de spectacle.</li>
        {% endfor %}
    </ul>

    <h2 style="margin-top: 40px; color: #888;">Contrôle Manuel (Global)</h2>
    <div id="main-btns"></div>
    <div class="footer-btns" id="footer-btns">
        <button class="action-btn sacem-btn" onclick="downloadSacem()">📑 Télécharger Fiche SACEM</button>
    </div>
    <div id="status">Chargement des plugins...</div>

    <script>
        // Code JavaScript existant pour les plugins
        fetch('/api/config')
            .then(r => r.json())
            .then(data => {
                const main = document.getElementById('main-btns');
                const footer = document.getElementById('footer-btns');
                const sacemBtn = footer.querySelector('.sacem-btn');
                
                document.getElementById('status').innerText = 'Prêt';

                for (const [pluginName, pluginData] of Object.entries(data)) {
                    pluginData.buttons.forEach(b => {
                        const btn = document.createElement('button');
                        btn.innerHTML = b.label;
                        btn.style.background = b.color || '#282828';
                        btn.onclick = () => cmd(pluginName, b.id);
                        
                        if (b.is_footer) {
                            btn.className = 'action-btn';
                            footer.insertBefore(btn, sacemBtn);
                        } else {
                            btn.className = 'playlist-btn';
                            main.appendChild(btn);
                        }
                    });
                }
            })
            .catch(e => { document.getElementById('status').innerText = 'Erreur UI: ' + e; });

        function cmd(plugin, action) {
            const status = document.getElementById('status');
            status.innerText = 'Envoi...';
            fetch(`/api/execute/${plugin}/${action}`)
                .then(r => r.json())
                .then(data => {
                    status.innerText = data.message;
                    setTimeout(() => status.innerText = 'Prêt', 2000);
                })
                .catch(e => { status.innerText = 'Erreur !'; });
        }

        function downloadSacem() {
            window.location.href = '/api/download_sacem';
        }

        setInterval(() => {
            fetch('/api/log_sacem');
        }, 10000);
    </script>
</body>
</html>
"""


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
        <li class="track-item" style="cursor: pointer;" onclick="playTrack('{{ track.spotify_uri }}')">
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
</html>
"""

# --- ROUTES AUTHENTIFICATION ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect.")
            
    return render_template_string(HTML_LOGIN)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# --- ROUTES OAUTH SPOTIFY ---

@app.route('/login/spotify')
@login_required
def login_spotify():
    '''Redirige l'utilisateur vers la page de connexion de Spotify'''
    redirect_uri = url_for('callback_spotify', _external=True)
    auth_url = get_auth_url(redirect_uri)
    return redirect(auth_url)

@app.route('/callback')
@login_required
def callback_spotify():
    '''Route de retour après autorisation Spotify'''
    code = request.args.get('code')
    if code:
        redirect_uri = url_for('callback_spotify', _external=True)
        if save_token_from_code(code, redirect_uri):
            flash("Votre compte Spotify a été lié avec succès !")
        else:
            flash("Erreur lors de la liaison de votre compte Spotify.")
    else:
        flash("Autorisation refusée par Spotify.")
    return redirect(url_for('dashboard'))


# --- ROUTES APPLICATION ---

@app.route('/show/<int:show_id>')
@login_required
def show_detail(show_id):
    show = Show.query.get_or_404(show_id)
    if show.user_id != current_user.id:
        flash("Accès refusé.")
        return redirect(url_for('dashboard'))
    return render_template_string(HTML_SHOW_DETAIL, show=show)


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    upcoming_shows = Show.query.filter_by(user_id=current_user.id, status='UPCOMING').order_by(Show.date.asc()).all()
    past_shows = Show.query.filter_by(user_id=current_user.id, status='PAST').order_by(Show.date.desc()).all()
    
    # On vérifie si l'utilisateur a un token Spotify en base
    has_spotify_token = current_user.spotify_token is not None
    
    return render_template_string(HTML_DASHBOARD, 
                                  current_user=current_user,
                                  upcoming_shows=upcoming_shows,
                                  past_shows=past_shows,
                                  has_spotify_token=has_spotify_token)

@app.route('/create_show', methods=['POST'])
@login_required
def create_show():
    title = request.form.get('title')
    if title:
        new_show = Show(title=title, user_id=current_user.id)
        db.session.add(new_show)
        db.session.commit()
    return redirect(url_for('dashboard'))


# --- ROUTES EXISTANTES DE L'API REST ---

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


@app.route('/api/config')
def get_config():
    res = {}
    for k, v in plugins.items():
        res[k] = v['config']
    return jsonify(res)

@app.route('/api/execute/<plugin>/<action>')
def execute_action(plugin, action):
    # Idéalement, il faudra ajouter @login_required ici plus tard, 
    # mais on garde ouvert pour les tests locaux du MVP.
    if plugin in plugins:
        success = plugins[plugin]['module'].execute(action)
        if success:
            return jsonify({"message": "Action envoyée"})
        else:
            return jsonify({"message": "Erreur exécution"}), 500
    return jsonify({"message": "Plugin inconnu"}), 404

@app.route('/api/log_sacem')
def log_sacem():
    script_path = os.path.join(SCRIPTS_DIR, "sacem_logger.py")
    subprocess.Popen([VENV_PYTHON, script_path])
    return jsonify({"status": "logged"})

@app.route('/api/download_sacem')
def download_sacem():
    if not os.path.exists(LOG_FILE):
        return "Aucune donnée SACEM enregistrée.", 404
    
    with open(LOG_FILE, 'r') as f:
        data = json.load(f)
    
    csv_path = os.path.join(SCRIPTS_DIR, "fiche_sacem.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Titre", "Artiste", "Durée (sec)", "Première diffusion", "Dernière diffusion"])
        for tid, info in data.items():
            first = datetime.fromtimestamp(info['first_seen']).strftime('%Y-%m-%d %H:%M:%S')
            last = datetime.fromtimestamp(info['last_seen']).strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow([info['title'], info['artist'], int(info['duration_sec']), first, last])
    
    return send_file(csv_path, as_attachment=True, download_name=f"sacem_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == '__main__':
    ip = get_ip()
    port = 5000
    print(f"🚀 Serveur Régisseur IA démarré sur http://{ip}:{port}")
    # Flask-Login a besoin des contextes d'application
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=port, debug=False)
