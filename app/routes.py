# app/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
import face_recognition
import os
import json
import numpy as np
from .forms import RegisterForm
from .utils import load_users, save_user, find_user_by_encoding
import base64
from io import BytesIO
from PIL import Image

main = Blueprint('main', __name__)
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        face_image = form.face_image.data

        if face_image and allowed_file(face_image.filename):
            filename = secure_filename(face_image.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            face_image.save(file_path)

            # Process face image
            image = face_recognition.load_image_file(file_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                encoding = encodings[0].tolist()  # Convert numpy array to list for JSON serialization
            else:
                flash('No face detected in the image.', 'danger')
                os.remove(file_path)  # Remove the uploaded file if no face is detected
                return redirect(url_for('main.register'))

            # Save user data locally
            user = {
                'username': username,
                'face_encoding': encoding,
                'image_filename': filename
            }

            save_user(user)

            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('main.login'))
        else:
            flash('Invalid file type. Only jpg, jpeg, png, and gif are allowed.', 'danger')

    return render_template('register.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Expecting base64 image data from the frontend
        data_url = request.form.get('image')
        if not data_url:
            flash('No image data received.', 'danger')
            return redirect(url_for('main.login'))

        # Decode the base64 image
        header, encoded = data_url.split(',', 1)
        data = base64.b64decode(encoded)
        image = Image.open(BytesIO(data)).convert('RGB')
        image_np = np.array(image)

        # Process face image
        encodings = face_recognition.face_encodings(image_np)
        if encodings:
            encoding = encodings[0]
        else:
            flash('No face detected in the image.', 'danger')
            return redirect(url_for('main.login'))

        # Find user by encoding
        user = find_user_by_encoding(encoding)
        if user:
            session['username'] = user['username']
            flash(f'Welcome, {user["username"]}!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Face not recognized. Please register or try again.', 'danger')
            return redirect(url_for('main.login'))

    return render_template('login.html')

@main.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('main.login'))
    username = session['username']
    return render_template('dashboard.html', username=username)


@main.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
