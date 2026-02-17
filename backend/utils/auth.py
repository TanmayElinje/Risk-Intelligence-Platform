"""
Authentication utilities - JWT token handling
backend/utils/auth.py
"""
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from backend.database import DatabaseService
from backend.database.models import User
from backend.utils import log

# Secret key for JWT (should be in .env in production)
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this-in-production')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def create_access_token(user_id: int, username: str) -> str:
    """
    Create JWT access token
    
    Args:
        user_id: User ID
        username: Username
        
    Returns:
        JWT token string
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': expire,
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_access_token(token: str) -> dict:
    """
    Decode and verify JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload dict
        
    Raises:
        jwt.ExpiredSignatureError: Token has expired
        jwt.InvalidTokenError: Token is invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")


def get_token_from_header() -> str:
    """
    Extract JWT token from Authorization header
    
    Returns:
        Token string or None
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return None
    
    # Expected format: "Bearer <token>"
    parts = auth_header.split()
    
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]


def get_current_user() -> User:
    """
    Get current authenticated user from JWT token
    
    Returns:
        User object
        
    Raises:
        Exception: If token is invalid or user not found
    """
    token = get_token_from_header()
    
    if not token:
        raise Exception("No authentication token provided")
    
    try:
        payload = decode_access_token(token)
        user_id = payload.get('user_id')
        
        if not user_id:
            raise Exception("Invalid token payload")
        
        # Get user from database
        with DatabaseService() as db:
            user = db.db.query(User).filter(User.id == user_id).first()
            
            if not user:
                raise Exception("User not found")
            
            if not user.is_active:
                raise Exception("User account is inactive")
            
            return user
            
    except Exception as e:
        raise Exception(f"Authentication failed: {str(e)}")


def require_auth(f):
    """
    Decorator to require authentication for API endpoints
    
    Usage:
        @app.route('/protected')
        @require_auth
        def protected_route():
            user = get_current_user()
            return jsonify({'user': user.username})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user = get_current_user()
            # Optionally pass user to the route function
            return f(*args, **kwargs)
        except Exception as e:
            log.warning(f"Authentication failed: {str(e)}")
            return jsonify({
                'error': 'Authentication required',
                'message': str(e)
            }), 401
    
    return decorated_function


def require_admin(f):
    """
    Decorator to require admin privileges
    
    Usage:
        @app.route('/admin-only')
        @require_admin
        def admin_route():
            return jsonify({'message': 'Admin access'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            user = get_current_user()
            
            if not user.is_admin:
                return jsonify({
                    'error': 'Admin access required',
                    'message': 'You do not have permission to access this resource'
                }), 403
            
            return f(*args, **kwargs)
        except Exception as e:
            log.warning(f"Authentication failed: {str(e)}")
            return jsonify({
                'error': 'Authentication required',
                'message': str(e)
            }), 401
    
    return decorated_function


def optional_auth(f):
    """
    Decorator for routes that work with or without authentication
    User will be None if not authenticated
    
    Usage:
        @app.route('/optional')
        @optional_auth
        def optional_route():
            try:
                user = get_current_user()
                return jsonify({'user': user.username})
            except:
                return jsonify({'user': 'guest'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Just proceed - route can call get_current_user() if needed
        return f(*args, **kwargs)
    
    return decorated_function