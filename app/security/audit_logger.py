import logging
from datetime import datetime
from typing import Dict, Any
import json
from flask import request

class AuditLogger:
    def __init__(self, log_file='audit.log'):
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        
        # Create file handler
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(handler)
    
    def log_event(self, user: str, action: str, details: Dict[str, Any] = None, severity: str = 'INFO'):
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'user': user,
            'action': action,
            'severity': severity,
            'details': details or {}
        }
        
        # Log to file
        self.logger.info(json.dumps(event))
        
        # Also log to console for debugging
        self.logger.info('AUDIT: %s', event)
    
    def log_login(self, user: str, success: bool, ip: str = None):
        self.log_event(
            user=user,
            action='login',
            details={
                'success': success,
                'ip': ip,
                'user_agent': request.headers.get('User-Agent', 'unknown') if 'request' in globals() else 'unknown'
            },
            severity='INFO' if success else 'WARNING'
        )
    
    def log_logout(self, user: str):
        self.log_event(
            user=user,
            action='logout',
            severity='INFO'
        )
    
    def log_admin_action(self, user: str, resource: str, action: str, details: Dict[str, Any] = None):
        self.log_event(
            user=user,
            action=f'admin_{action}',
            details={
                'resource': resource,
                'details': details
            },
            severity='INFO'
        )
    
    def log_security_event(self, user: str, event_type: str, details: Dict[str, Any] = None):
        self.log_event(
            user=user,
            action=f'security_{event_type}',
            details=details,
            severity='WARNING'
        )
    
    def log_api_access(self, user: str, endpoint: str, method: str, status_code: int):
        self.log_event(
            user=user,
            action='api_access',
            details={
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code
            },
            severity='INFO' if status_code < 400 else 'WARNING'
        )

# Global audit logger instance
audit_logger = AuditLogger()