# app/__init__.py

from flask import Flask
from flask_session import Session  # To handle server-side sessions
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a secure secret key
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')  # Absolute path to uploads
    app.config['SESSION_TYPE'] = 'filesystem'  # Use server-side sessions

    # Ensure the upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Initialize session
    Session(app)

    # Register blueprints
    from .routes import main
    app.register_blueprint(main)

    return app
