import sys
import os
from flask import Flask
from models import db, User, Show, ShowTrack
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    jay = User.query.filter_by(username='Jay').first()
    if not jay:
        print("Erreur: Utilisateur Jay introuvable.")
        sys.exit(1)
    
    if Show.query.filter_by(user_id=jay.id).count() > 0:
        print("Données déjà présentes. Nettoyage pour réinitialisation...")
        ShowTrack.query.delete()
        Show.query.delete()
        db.session.commit()

    print("Injection des données de test...")
    
    # Spectacles passés
    s1 = Show(title="Match d'impro vs Rennes", date=datetime.utcnow() - timedelta(days=30), status='PAST', user_id=jay.id)
    s2 = Show(title="Cabaret d'Hiver", date=datetime.utcnow() - timedelta(days=60), status='PAST', user_id=jay.id)
    
    # Spectacles à venir
    s3 = Show(title="Tournoi des 3 Nations", date=datetime.utcnow() + timedelta(days=7), status='UPCOMING', user_id=jay.id)
    s4 = Show(title="Spectacle Concept 'La Boucle'", date=datetime.utcnow() + timedelta(days=14), status='UPCOMING', user_id=jay.id)

    db.session.add_all([s1, s2, s3, s4])
    db.session.commit()

    # Pistes pour le Tournoi
    t1 = ShowTrack(show_id=s3.id, title="Eye of the Tiger", artist="Survivor", category="Entrée Joueurs", position=1)
    t2 = ShowTrack(show_id=s3.id, title="Careless Whisper", artist="George Michael", category="Amour", position=2)
    t3 = ShowTrack(show_id=s3.id, title="Requiem for a Dream", artist="Clint Mansell", category="Tension", position=3)

    db.session.add_all([t1, t2, t3])
    db.session.commit()
    print("Succès: Base de données peuplée avec les données de test !")
