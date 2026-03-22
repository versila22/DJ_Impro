import sys
import os
from flask import Flask
from models import db, User
from flask_bcrypt import Bcrypt

# Fake app_context to run SQLAlchemy outside of the main server
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt = Bcrypt(app)

def add_user(username, password):
    with app.app_context():
        db.create_all()
        if User.query.filter_by(username=username).first():
            print(f"Erreur : L'utilisateur '{username}' existe déjà dans la base.")
            return
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password_hash=hashed)
        db.session.add(new_user)
        db.session.commit()
        print(f"Succès : Utilisateur '{username}' créé avec succès dans users.db.")

if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == 'add-user':
        add_user(sys.argv[2], sys.argv[3])
    else:
        print("Usage: python manage_users.py add-user <username> <password>")
