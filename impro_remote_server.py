import os
import sys
import subprocess
import socket
from flask import Flask, render_template_string, request, jsonify, send_file
from flask_cors import CORS
import qrcode
import json
import csv
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuration des scripts
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = sys.executable
LOG_FILE = os.path.join(SCRIPTS_DIR, "sacem_log.json")

def run_script(script_name, arg=None):
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    cmd = [VENV_PYTHON, script_path]
    if arg:
        cmd.append(arg)
    try:
        subprocess.Popen(cmd)
        return True
    except Exception as e:
        print(f"Erreur lancement {script_name}: {e}")
        return False

# HTML de l'interface mobile
HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Impro Remote + SACEM</title>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; background-color: #121212; color: white; margin: 0; padding: 20px; display: flex; flex-direction: column; height: 100vh; box-sizing: border-box; }
        h1 { color: #1DB954; text-align: center; font-size: 1.5rem; margin-bottom: 2rem; }
        .playlist-btn { background: #282828; border: none; border-radius: 15px; padding: 20px; margin-bottom: 15px; color: white; font-size: 1.1rem; font-weight: bold; width: 100%; display: flex; align-items: center; gap: 15px; cursor: pointer; }
        .playlist-btn:active { background: #333; transform: scale(0.98); }
        .icon { font-size: 1.5rem; }
        .footer-btns { margin-top: auto; display: flex; gap: 15px; padding-bottom: 20px; }
        .action-btn { flex: 1; color: white; border: none; border-radius: 12px; padding: 20px; font-weight: bold; font-size: 1rem; cursor: pointer; }
        .fade-btn { background: #f39c12; }
        .stop-btn { background: #e74c3c; }
        .sacem-btn { background: #3498db; margin-top: 10px; width: 100%; }
        #status { text-align: center; font-size: 0.8rem; color: #666; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>PA 🤖 Impro Remote</h1>
    
    <button class="playlist-btn" onclick="cmd('launch_impro')">
        <span class="icon">🎤</span> Lip Sync Seul
    </button>
    <button class="playlist-btn" onclick="cmd('launch_cabaret')">
        <span class="icon">🔞</span> Cabaret +16
    </button>
    <button class="playlist-btn" onclick="cmd('launch_match')">
        <span class="icon">🎈</span> Match +9
    </button>

    <div class="footer-btns" style="flex-wrap: wrap;">
        <button class="action-btn fade-btn" onclick="cmd('fade')">📉 FADE</button>
        <button class="action-btn stop-btn" onclick="cmd('stop')">🛑 STOP</button>
        <button class="action-btn sacem-btn" onclick="downloadSacem()">📑 Télécharger Fiche SACEM</button>
    </div>
    
    <div id="status">Prêt</div>

    <script>
        function cmd(action) {
            const status = document.getElementById('status');
            status.innerText = 'Envoi: ' + action + '...';
            fetch('/api/' + action)
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

        // Auto-log SACEM toutes les 10 secondes si la page est ouverte
        setInterval(() => {
            fetch('/api/log_sacem');
        }, 10000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_INTERFACE)

@app.route('/api/log_sacem')
def log_sacem():
    run_script("sacem_logger.py")
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
        writer.writerow(["Titre", "Artiste", "Durée de diffusion (secondes)", "Première diffusion", "Dernière diffusion"])
        for tid, info in data.items():
            first = datetime.fromtimestamp(info['first_seen']).strftime('%Y-%m-%d %H:%M:%S')
            last = datetime.fromtimestamp(info['last_seen']).strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow([info['title'], info['artist'], int(info['duration_sec']), first, last])
    
    return send_file(csv_path, as_attachment=True, download_name=f"sacem_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")

@app.route('/api/<action>')
def handle_action(action):
    if action == 'launch_impro':
        run_script("impro_launcher.py", "Lip Sync impro seul")
        return jsonify({"message": "Impro lancée"})
    elif action == 'launch_cabaret':
        run_script("impro_launcher.py", "Impro - Cabaret +16")
        return jsonify({"message": "Cabaret lancé"})
    elif action == 'launch_match':
        run_script("impro_launcher.py", "Impro - Match +9")
        return jsonify({"message": "Match lancé"})
    elif action == 'fade':
        run_script("spotify_fadeout.py")
        return jsonify({"message": "Fondu..."})
    elif action == 'stop':
        run_script("spotify_stop.py")
        return jsonify({"message": "Stop !"})
    return jsonify({"message": "Inconnu"}), 404

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
    print(f"🚀 Serveur SACEM Remote démarré sur http://{ip}:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
