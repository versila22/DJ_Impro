from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    # Relations
    shows = db.relationship('Show', backref='owner', lazy=True)
    spotify_token = db.relationship('SpotifyToken', backref='user', uselist=False, cascade="all, delete-orphan")

class SpotifyToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    # Spotipy a besoin d'un dictionnaire avec access_token, refresh_token, expires_at. On stocke le JSON.
    token_info = db.Column(db.JSON, nullable=False) 

class Show(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False) # Ex: "Match contre Brest"
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(50), nullable=False, default='UPCOMING') # UPCOMING ou PAST
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # L'ordre des morceaux
    tracks = db.relationship('ShowTrack', backref='show', lazy=True, cascade="all, delete-orphan", order_by="ShowTrack.position")

class ShowTrack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    show_id = db.Column(db.Integer, db.ForeignKey('show.id'), nullable=False)
    spotify_uri = db.Column(db.String(200), nullable=True) # L'ID Spotify de la piste
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(100), nullable=True) # Ex: "Tension", "Amour" (pour l'IA par défaut)
    position = db.Column(db.Integer, nullable=False, default=0) # Pour gérer l'ordre dans la liste
