from datetime import timedelta
from flask import session, g
from flask_login import current_user
import time

class SessionTimeout:
    def __init__(self, app=None, timeout_seconds=1800):
        self.timeout = timedelta(seconds=timeout_seconds)
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        app.config['SESSION_TIMEOUT'] = self.timeout
        app.before_request(self.check_session_timeout)
        app.after_request(self.update_session_timeout)
    
    def check_session_timeout(self):
        if current_user.is_authenticated:
            now = time.time()
            last_activity = session.get('last_activity', now)
            
            if now - last_activity > self.timeout.total_seconds():
                # Session has timed out
                session.clear()
                return jsonify({
                    'error': 'Session timeout',
                    'message': 'Your session has expired due to inactivity'
                }), 401
            
            # Update last activity time
            session['last_activity'] = now
    
    def update_session_timeout(self, response):
        if current_user.is_authenticated:
            session.modified = True
            session['last_activity'] = time.time()
        return response
    
    def get_timeout_remaining(self):
        if current_user.is_authenticated:
            last_activity = session.get('last_activity', time.time())
            now = time.time()
            elapsed = now - last_activity
            remaining = max(0, self.timeout.total_seconds() - elapsed)
            return remaining
        return 0
    
    def extend_session(self):
        if current_user.is_authenticated:
            session['last_activity'] = time.time()

# Global session timeout instance
session_timeout = SessionTimeout()