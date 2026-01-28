from datetime import datetime, timedelta, timezone
from jose import jwt
import jose
from functools import wraps
from flask import request, jsonify
import os

SECRET_KEY = os.environ.get('SECRET_KEY') or 'super secret secrets'

def encode_token(user_id, role="user"):
    payload = {
        'exp': datetime.now(timezone.utc) + timedelta(days=0, hours=1),
        'iat': datetime.now(timezone.utc),
        'sub': str(user_id),
        'role': role
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def token_required(f):
    @wraps(f)
    def decoration(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split()[1]
        
        if not token:
            return jsonify({"error": "token missing from authorization headers"}), 401
        
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            request.logged_in_user_id = data['sub']
        except jose.exceptions.ExpiredSignatureError:
            return jsonify({'message':'token is expired'}), 403
        except jose.exceptions.JWTError:
            return jsonify({'message':'invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decoration

def admin_required(f):
    @wraps(f)
    def decoration(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split()[1]
        
        if not token:
            return jsonify({"error": "token missing from authorization headers"}), 401
        
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            request.logged_in_user_id = int(data['sub'])
            if data['role'].lower() != "admin":
                return jsonify({"message": "Admin permissions required."}), 403
        except jose.exceptions.ExpiredSignatureError:
            return jsonify({'message':'token is expired'}), 403
        except jose.exceptions.JWTError:
            return jsonify({'message':'invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decoration

def customer_token_required(f):
    @wraps(f)
    def decoration(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split()[1]
        
        if not token:
            return jsonify({"error": "token missing from authorization headers"}), 401
        
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            request.logged_in_customer_id = int(data['sub'])
            if data.get('role', '').lower() != "customer":
                return jsonify({"message": "Customer authentication required."}), 403
        except jose.exceptions.ExpiredSignatureError:
            return jsonify({'message':'token is expired'}), 403
        except jose.exceptions.JWTError:
            return jsonify({'message':'invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decoration

def mechanic_token_required(f):
    @wraps(f)
    def decoration(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split()[1]
        
        if not token:
            return jsonify({"error": "token missing from authorization headers"}), 401
        
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            request.logged_in_mechanic_id = int(data['sub'])
            if data.get('role', '').lower() != "mechanic":
                return jsonify({"message": "Mechanic authentication required."}), 403
        except jose.exceptions.ExpiredSignatureError:
            return jsonify({'message':'token is expired'}), 403
        except jose.exceptions.JWTError:
            return jsonify({'message':'invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decoration