from flask import request, session, jsonify
from flask_wtf.csrf import CSRFProtect, generate_csrf
from typing import Callable
from functools import wraps

class CSRFProtection:
    def __init__(self, app=None):
        self.csrf = CSRFProtect()
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        self.csrf.init_app(app)
        
        # Add CSRF token endpoint
        @app.route('/csrf-token', methods=['GET'])
        def get_csrf_token():
            return jsonify({
                'csrf_token': generate_csrf()
            })
    
    def validate_csrf(self, token=None):
        try:
            self.csrf._get_csrf_token()
            return True
        except Exception as e:
            return False
    
    def get_csrf_token(self):
        return generate_csrf()
    
    def require_csrf(self, f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.validate_csrf():
                return jsonify({
                    'error': 'CSRF token missing or invalid'
                }), 403
            return f(*args, **kwargs)
        return decorated_function

# Global CSRF protection instance
csrf_protection = CSRFProtection()