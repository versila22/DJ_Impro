import os
import sys
import subprocess
import socket
import importlib.util
from flask import Flask, render_template_string, request, jsonify, send_file
from flask_cors import CORS
import json
import csv
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuration
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
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

HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>PA 🤖 Régisseur IA</title>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; background-color: #121212; color: white; margin: 0; padding: 20px; display: flex; flex-direction: column; height: 100vh; box-sizing: border-box; }
        h1 { color: #1DB954; text-align: center; font-size: 1.5rem; margin-bottom: 2rem; }
        .playlist-btn { border: none; border-radius: 15px; padding: 20px; margin-bottom: 15px; color: white; font-size: 1.1rem; font-weight: bold; width: 100%; display: flex; align-items: center; gap: 15px; cursor: pointer; }
        .playlist-btn:active { transform: scale(0.98); }
        .footer-btns { margin-top: auto; display: flex; flex-wrap: wrap; gap: 15px; padding-bottom: 20px; }
        .action-btn { flex: 1; color: white; border: none; border-radius: 12px; padding: 20px; font-weight: bold; font-size: 1rem; cursor: pointer; }
        .action-btn:active { transform: scale(0.98); }
        .sacem-btn { background: #3498db; margin-top: 10px; width: 100%; flex: none; }
        #status { text-align: center; font-size: 0.8rem; color: #666; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>PA 🤖 Régisseur IA</h1>
    <div id="main-btns"></div>
    <div class="footer-btns" id="footer-btns">
        <button class="action-btn sacem-btn" onclick="downloadSacem()">📑 Télécharger Fiche SACEM</button>
    </div>
    <div id="status">Chargement des plugins...</div>

    <script>
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

@app.route('/')
def index():
    return render_template_string(HTML_INTERFACE)

@app.route('/api/config')
def get_config():
    res = {}
    for k, v in plugins.items():
        res[k] = v['config']
    return jsonify(res)

@app.route('/api/execute/<plugin>/<action>')
def execute_action(plugin, action):
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
    app.run(host='0.0.0.0', port=port, debug=False)
