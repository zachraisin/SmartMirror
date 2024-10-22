from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify
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
import requests  # Import requests for the weather API

main = Blueprint('main', __name__)
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')

# Key for swell forecast API
SurfFOR_API ="8e6bc43c-e89b-11ed-92e6-0242ac130002-8e6bc4a0-e89b-11ed-92e6-0242ac130002"

# Your OpenWeatherMap API key
API_KEY = 'f3337f70ad27b09a847fe7856d3ceaaf'

# retrieve swell of user input location
def swell(lat, lng, key):
    import arrow
    import requests

    # Get first hour of today
    start = arrow.now().floor('day')

    # Get last hour of today
    end = arrow.now().ceil('day')

    response = requests.get(
    'https://api.stormglass.io/v2/weather/point',
    params={
        'lat': lat,
        'lng': lng,
        'params': ','.join(['waveHeight', 'waterTemperature']),
        'start': start.to('UTC').timestamp(),  # Convert to UTC timestamp
        'end': end.to('UTC').timestamp()  # Convert to UTC timestamp
    },
    headers={
        'Authorization': key
    }
    )

    json_data= response.json()
        
    # Get the first entry in the dictionary
    first_entry = json_data['hours'][0]
    
    # Extract the waveHeight
    height_swell = first_entry['waveHeight']['sg']
    
    return height_swell

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
    
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    swell(latitude, longitude, SurfFOR_API)
    
    return render_template('dashboard.html', username=username)

# Route to fetch weather data based on user's geolocation
@main.route('/get_weather', methods=['POST'])
def get_weather():
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if latitude and longitude:
        # Fetch weather data using latitude and longitude
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={API_KEY}&units=metric"
        response = requests.get(weather_url)
        
        if response.status_code == 200:
            weather_data = response.json()
            # Extract relevant weather information
            weather = {
                'temperature': weather_data['main']['temp'],
                'description': weather_data['weather'][0]['description'].capitalize(),
                'city': weather_data['name']
            }
            return jsonify(success=True, temperature=weather['temperature'], description=weather['description'], city=weather['city'])
        else:
            return jsonify(success=False), 500
    else:
        return jsonify(success=False), 400

@main.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
