import re
from typing import Dict, Any
from werkzeug.security import generate_password_hash, check_password_hash

class PasswordPolicy:
    def __init__(self, min_length: int = 8, require_uppercase: bool = True,
                 require_lowercase: bool = True, require_digits: bool = True,
                 require_special: bool = True, max_age_days: int = 90,
                 prevent_reuse: int = 5):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special = require_special
        self.max_age_days = max_age_days
        self.prevent_reuse = prevent_reuse
        self.used_passwords = {}
    
    def validate_password(self, password: str, username: str = None) -> (bool, str):
        errors = []
        
        # Check minimum length
        if len(password) < self.min_length:
            errors.append(f'Password must be at least {self.min_length} characters long')
        
        # Check for uppercase letters
        if self.require_uppercase and not any(c.isupper() for c in password):
            errors.append('Password must contain at least one uppercase letter')
        
        # Check for lowercase letters
        if self.require_lowercase and not any(c.islower() for c in password):
            errors.append('Password must contain at least one lowercase letter')
        
        # Check for digits
        if self.require_digits and not any(c.isdigit() for c in password):
            errors.append('Password must contain at least one digit')
        
        # Check for special characters
        if self.require_special:
            special_chars = re.compile(r'[^a-zA-Z0-9]')
            if not special_chars.search(password):
                errors.append('Password must contain at least one special character')
        
        # Check for username in password
        if username and username in password:
            errors.append('Password cannot contain your username')
        
        # Check for common patterns
        common_patterns = [
            'password', '123456', 'qwerty', 'abc123', 'letmein',
            'monkey', 'dragon', 'master', 'sunshine', 'passw0rd'
        ]
        if password.lower() in common_patterns:
            errors.append('Password is too common')
        
        if errors:
            return False, '; '.join(errors)
        return True, 'Password is valid'
    
    def check_password_strength(self, password: str) -> int:
        strength = 0
        
        # Length bonus
        length = len(password)
        if length >= 8:
            strength += 1
        if length >= 12:
            strength += 1
        if length >= 16:
            strength += 1
        
        # Character variety bonus
        if any(c.isupper() for c in password):
            strength += 1
        if any(c.islower() for c in password):
            strength += 1
        if any(c.isdigit() for c in password):
            strength += 1
        if any(not c.isalnum() for c in password):
            strength += 1
        
        return min(strength, 5)
    
    def get_password_strength_message(self, password: str) -> str:
        strength = self.check_password_strength(password)
        
        messages = [
            'Very Weak',
            'Weak',
            'Fair',
            'Good',
            'Strong',
            'Very Strong'
        ]
        
        return messages[strength]
    
    def is_password_expired(self, created_at: str) -> bool:
        from datetime import datetime, timedelta
        
        if not created_at:
            return True
        
        try:
            created_date = datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%SZ')
            expiration_date = created_date + timedelta(days=self.max_age_days)
            return datetime.utcnow() > expiration_date
        except:
            return True
    
    def hash_password(self, password: str) -> str:
        return generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, hashed: str, password: str) -> bool:
        return check_password_hash(hashed, password)
    
    def track_password_usage(self, user_id: str, password_hash: str):
        if user_id not in self.used_passwords:
            self.used_passwords[user_id] = []
        
        self.used_passwords[user_id].append(password_hash)
        
        # Keep only the last N passwords
        if len(self.used_passwords[user_id]) > self.prevent_reuse:
            self.used_passwords[user_id] = self.used_passwords[user_id][-self.prevent_reuse:]
    
    def is_password_reused(self, user_id: str, password_hash: str) -> bool:
        if user_id not in self.used_passwords:
            return False
        
        return password_hash in self.used_passwords[user_id]
    
    def get_policy_details(self) -> Dict[str, Any]:
        return {
            'min_length': self.min_length,
            'require_uppercase': self.require_uppercase,
            'require_lowercase': self.require_lowercase,
            'require_digits': self.require_digits,
            'require_special': self.require_special,
            'max_age_days': self.max_age_days,
            'prevent_reuse': self.prevent_reuse
        }

# Global password policy instance
password_policy = PasswordPolicy()