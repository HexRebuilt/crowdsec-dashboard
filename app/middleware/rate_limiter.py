from flask import request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis
from typing import Callable

class RateLimiter:
    def __init__(self, app=None):
        self.redis_client = Redis(host='redis', port=6379, db=0)
        self.limiter = Limiter(
            key_func=get_remote_address,
            storage_uri='redis://redis:6379',
            storage_options={
                'redis_cls': Redis,
                'host': 'redis',
                'port': 6379,
                'db': 0
            }
        )
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        # Rate limits configuration
        self.limiter.init_app(app)
        
        # Default rate limits
        self.limiter.shared_limit("100/minute;10/second", "default")
        self.limiter.shared_limit("5/minute", "login")
        self.limiter.shared_limit("2/minute", "admin")
    
    def limit(self, limit: str, key_func=None, methods=None, error_message=None):
        def decorator(f):
            return self.limiter.limit(limit, key_func=key_func, methods=methods, error_message=error_message)(f)
        return decorator
    
    def get_rate_limit_headers(self, limit: str, remaining: int, reset: int):
        return {
            'X-RateLimit-Limit': limit,
            'X-RateLimit-Remaining': remaining,
            'X-RateLimit-Reset': reset
        }

# Global rate limiter instance
rate_limiter = RateLimiter()