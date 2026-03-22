import os
import subprocess
import sys

# Pointeur vers la racine du projet
SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_PYTHON = sys.executable

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

def get_config():
    """Retourne la configuration UI du plugin."""
    return {
        "name": "Spotify Actionneur",
        "buttons": [
            {"id": "launch_impro", "label": "🎤 Lip Sync Seul", "color": "#282828", "is_footer": False},
            {"id": "launch_cabaret", "label": "🔞 Cabaret +16", "color": "#282828", "is_footer": False},
            {"id": "launch_match", "label": "🎈 Match +9", "color": "#282828", "is_footer": False},
            {"id": "fade", "label": "📉 FADE", "color": "#f39c12", "is_footer": True},
            {"id": "stop", "label": "🛑 STOP", "color": "#e74c3c", "is_footer": True}
        ]
    }

def execute(action):
    """Exécute l'action demandée."""
    if action == 'launch_impro': return run_script("impro_launcher.py", "Lip Sync impro seul")
    elif action == 'launch_cabaret': return run_script("impro_launcher.py", "Impro - Cabaret +16")
    elif action == 'launch_match': return run_script("impro_launcher.py", "Impro - Match +9")
    elif action == 'fade': return run_script("spotify_fadeout.py")
    elif action == 'stop': return run_script("spotify_stop.py")
    return False
