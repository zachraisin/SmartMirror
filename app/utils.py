# app/utils.py

import json
import os
import numpy as np
from flask import current_app

USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    return users

def save_user(user):
    users = load_users()
    users.append(user)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def find_user_by_encoding(encoding, tolerance=0.6):
    users = load_users()
    encoding_np = np.array(encoding)
    for user in users:
        stored_encoding = np.array(user['face_encoding'])
        distance = np.linalg.norm(stored_encoding - encoding_np)
        if distance < tolerance:
            return user
    return None
