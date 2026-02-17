"""
Authentication API Routes
backend/api/auth_routes.py
"""
from flask import Blueprint, request, jsonify
from backend.database import DatabaseService
from backend.database.models import User
from backend.utils import log
from backend.utils.auth import (
    create_access_token,
    get_current_user,
    require_auth
)
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    User signup endpoint
    
    Request body:
        {
            "username": "johndoe",
            "email": "john@example.com",
            "password": "secure_password",
            "full_name": "John Doe"
        }
    
    Returns:
        {
            "message": "User created successfully",
            "user": {...},
            "token": "jwt_token"
        }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'error': f'Missing required field: {field}'
                }), 400
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        full_name = data.get('full_name', '').strip()
        
        # Validate password length
        if len(password) < 6:
            return jsonify({
                'error': 'Password must be at least 6 characters long'
            }), 400
        
        with DatabaseService() as db:
            # Check if username already exists
            existing_user = db.db.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                if existing_user.username == username:
                    return jsonify({
                        'error': 'Username already exists'
                    }), 409
                else:
                    return jsonify({
                        'error': 'Email already registered'
                    }), 409
            
            # Create new user
            new_user = User(
                username=username,
                email=email,
                full_name=full_name,
                is_active=True,
                is_admin=False
            )
            
            # Hash password
            new_user.set_password(password)
            
            db.db.add(new_user)
            db.db.commit()
            db.db.refresh(new_user)
            
            # Create access token
            token = create_access_token(new_user.id, new_user.username)
            
            log.info(f"New user registered: {username}")
            
            return jsonify({
                'message': 'User created successfully',
                'user': new_user.to_dict(),
                'token': token
            }), 201
            
    except Exception as e:
        log.error(f"Error in signup: {str(e)}")
        return jsonify({
            'error': 'Registration failed',
            'message': str(e)
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint
    
    Request body:
        {
            "username": "johndoe",  // or email
            "password": "secure_password"
        }
    
    Returns:
        {
            "message": "Login successful",
            "user": {...},
            "token": "jwt_token"
        }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('username') or not data.get('password'):
            return jsonify({
                'error': 'Username and password are required'
            }), 400
        
        username_or_email = data['username'].strip()
        password = data['password']
        
        with DatabaseService() as db:
            # Find user by username or email
            user = db.db.query(User).filter(
                (User.username == username_or_email) | 
                (User.email == username_or_email.lower())
            ).first()
            
            if not user:
                return jsonify({
                    'error': 'Invalid username or password'
                }), 401
            
            # Check password
            if not user.check_password(password):
                return jsonify({
                    'error': 'Invalid username or password'
                }), 401
            
            # Check if user is active
            if not user.is_active:
                return jsonify({
                    'error': 'Account is inactive'
                }), 403
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.db.commit()
            
            # Create access token
            token = create_access_token(user.id, user.username)
            
            log.info(f"User logged in: {user.username}")
            
            return jsonify({
                'message': 'Login successful',
                'user': user.to_dict(),
                'token': token
            }), 200
            
    except Exception as e:
        log.error(f"Error in login: {str(e)}")
        return jsonify({
            'error': 'Login failed',
            'message': str(e)
        }), 500


@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_me():
    """
    Get current user profile
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        {
            "user": {...}
        }
    """
    try:
        user = get_current_user()
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        log.error(f"Error in get_me: {str(e)}")
        return jsonify({
            'error': 'Failed to get user profile',
            'message': str(e)
        }), 500


@auth_bp.route('/update-profile', methods=['PUT'])
@require_auth
def update_profile():
    """
    Update user profile
    
    Request body:
        {
            "full_name": "New Name",
            "email": "newemail@example.com"
        }
    
    Returns:
        {
            "message": "Profile updated",
            "user": {...}
        }
    """
    try:
        user = get_current_user()
        data = request.get_json()
        
        with DatabaseService() as db:
            # Get fresh user instance
            db_user = db.db.query(User).filter(User.id == user.id).first()
            
            # Update fields
            if 'full_name' in data:
                db_user.full_name = data['full_name'].strip()
            
            if 'email' in data:
                new_email = data['email'].strip().lower()
                # Check if email is already used by another user
                existing = db.db.query(User).filter(
                    User.email == new_email,
                    User.id != user.id
                ).first()
                
                if existing:
                    return jsonify({
                        'error': 'Email already in use'
                    }), 409
                
                db_user.email = new_email
            
            db.db.commit()
            db.db.refresh(db_user)
            
            log.info(f"User profile updated: {user.username}")
            
            return jsonify({
                'message': 'Profile updated successfully',
                'user': db_user.to_dict()
            }), 200
            
    except Exception as e:
        log.error(f"Error in update_profile: {str(e)}")
        return jsonify({
            'error': 'Failed to update profile',
            'message': str(e)
        }), 500


@auth_bp.route('/change-password', methods=['POST'])
@require_auth
def change_password():
    """
    Change user password
    
    Request body:
        {
            "current_password": "old_password",
            "new_password": "new_password"
        }
    
    Returns:
        {
            "message": "Password changed successfully"
        }
    """
    try:
        user = get_current_user()
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({
                'error': 'Current and new password are required'
            }), 400
        
        current_password = data['current_password']
        new_password = data['new_password']
        
        # Validate new password length
        if len(new_password) < 6:
            return jsonify({
                'error': 'New password must be at least 6 characters long'
            }), 400
        
        with DatabaseService() as db:
            # Get fresh user instance
            db_user = db.db.query(User).filter(User.id == user.id).first()
            
            # Verify current password
            if not db_user.check_password(current_password):
                return jsonify({
                    'error': 'Current password is incorrect'
                }), 401
            
            # Set new password
            db_user.set_password(new_password)
            db.db.commit()
            
            log.info(f"Password changed for user: {user.username}")
            
            return jsonify({
                'message': 'Password changed successfully'
            }), 200
            
    except Exception as e:
        log.error(f"Error in change_password: {str(e)}")
        return jsonify({
            'error': 'Failed to change password',
            'message': str(e)
        }), 500


@auth_bp.route('/verify-token', methods=['GET'])
def verify_token():
    """
    Verify if a token is valid
    
    Headers:
        Authorization: Bearer <token>
    
    Returns:
        {
            "valid": true,
            "user": {...}
        }
    """
    try:
        user = get_current_user()
        
        return jsonify({
            'valid': True,
            'user': user.to_dict()
        }), 200
        
    except Exception:
        return jsonify({
            'valid': False,
            'error': 'Invalid or expired token'
        }), 401