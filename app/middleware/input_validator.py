from flask import request, jsonify
from typing import Dict, Any, Callable
import re
import ipaddress

class InputValidator:
    def __init__(self):
        self.validators = {}
    
    def add_validator(self, field: str, validator: Callable[[str], bool], error_message: str):
        if field not in self.validators:
            self.validators[field] = []
        self.validators[field].append({
            'validator': validator,
            'error_message': error_message
        })
    
    def validate(self, data: Dict[str, Any]) -> (bool, Dict[str, str]):
        errors = {}
        
        for field, validators in self.validators.items():
            if field not in data:
                errors[field] = 'Field is required'
                continue
            
            value = data[field]
            for validator in validators:
                if not validator['validator'](value):
                    if field not in errors:
                        errors[field] = []
                    errors[field].append(validator['error_message'])
        
        if errors:
            return False, errors
        return True, {}
    
    def validate_request(self, request_data: Dict[str, Any] = None) -> (bool, Dict[str, str]):
        if request_data is None:
            request_data = request.get_json() or {}
        return self.validate(request_data)
    
    def add_required_validator(self, field: str):
        self.add_validator(
            field,
            lambda x: x is not None and str(x).strip() != '',
            'Field is required'
        )
    
    def add_string_validator(self, field: str, min_length: int = 1, max_length: int = None):
        def validator(value):
            if not isinstance(value, str):
                return False
            if len(value) < min_length:
                return False
            if max_length and len(value) > max_length:
                return False
            return True
        
        error_message = f'Must be a string between {min_length}'
        if max_length:
            error_message += f' and {max_length} characters'
        else:
            error_message += ' or more characters'
        
        self.add_validator(field, validator, error_message)
    
    def add_email_validator(self, field: str):
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        def validator(value):
            if not isinstance(value, str):
                return False
            return re.match(email_regex, value) is not None
        
        self.add_validator(field, validator, 'Invalid email address')
    
    def add_password_validator(self, field: str, min_length: int = 8):
        def validator(value):
            if not isinstance(value, str):
                return False
            if len(value) < min_length:
                return False
            # Check for at least one uppercase letter
            if not any(c.isupper() for c in value):
                return False
            # Check for at least one lowercase letter
            if not any(c.islower() for c in value):
                return False
            # Check for at least one digit
            if not any(c.isdigit() for c in value):
                return False
            return True
        
        error_message = f'Password must be at least {min_length} characters long '
        error_message += 'and contain uppercase, lowercase, and digits'
        
        self.add_validator(field, validator, error_message)
    
    def add_ip_validator(self, field: str):
        def validator(value):
            if not isinstance(value, str):
                return False
            try:
                ipaddress.ip_address(value)
                return True
            except ValueError:
                return False
        
        self.add_validator(field, validator, 'Invalid IP address')
    
    def add_url_validator(self, field: str):
        url_regex = r'^(https?|ftp)://[^
.\"]*'
        
        def validator(value):
            if not isinstance(value, str):
                return False
            return re.match(url_regex, value) is not None
        
        self.add_validator(field, validator, 'Invalid URL')
    
    def add_json_validator(self, field: str):
        def validator(value):
            if not isinstance(value, str):
                return False
            try:
                json.loads(value)
                return True
            except ValueError:
                return False
        
        self.add_validator(field, validator, 'Invalid JSON')
    
    def add_number_validator(self, field: str, min_value: float = None, max_value: float = None):
        def validator(value):
            try:
                num = float(value)
                if min_value is not None and num < min_value:
                    return False
                if max_value is not None and num > max_value:
                    return False
                return True
            except (ValueError, TypeError):
                return False
        
        error_message = 'Must be a number'
        if min_value is not None and max_value is not None:
            error_message += f' between {min_value} and {max_value}'
        elif min_value is not None:
            error_message += f' >= {min_value}'
        elif max_value is not None:
            error_message += f' ≤ {max_value}'
        
        self.add_validator(field, validator, error_message)
    
    def add_choice_validator(self, field: str, choices: List[str]):
        def validator(value):
            return value in choices
        
        error_message = f'Must be one of: {", ".join(choices)}'
        
        self.add_validator(field, validator, error_message)
    
    def add_date_validator(self, field: str):
        date_regex = r'^\d{4}-\d{2}-\d{2}$'
        def validator(value):
            if not isinstance(value, str):
                return False
            if not re.match(date_regex, value):
                return False
            try:
                datetime.strptime(value, '%Y-%m-%d')
                return True
            except ValueError:
                return False
        
        self.add_validator(field, validator, 'Invalid date format (YYYY-MM-DD)')
    
    def add_datetime_validator(self, field: str):
        datetime_regex = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
        def validator(value):
            if not isinstance(value, str):
                return False
            if not re.match(datetime_regex, value):
                return False
            try:
                datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
                return True
            except ValueError:
                return False
        
        self.add_validator(field, validator, 'Invalid datetime format (YYYY-MM-DDTHH:MM:SSZ)')
    
    def add_custom_validator(self, field: str, validator_func: Callable[[Any], bool], error_message: str):
        self.add_validator(field, validator_func, error_message)
    
    def validate_all(self, data: Dict[str, Any]) -> (bool, Dict[str, str]):
        errors = {}
        
        for field, validators in self.validators.items():
            if field not in data:
                errors[field] = 'Field is required'
                continue
            
            value = data[field]
            field_errors = []
            
            for validator in validators:
                if not validator['validator'](value):
                    field_errors.append(validator['error_message'])
            
            if field_errors:
                errors[field] = field_errors
        
        if errors:
            return False, errors
        return True, {}
    
    def get_validation_errors(self) -> Dict[str, List[str]]:
        return {field: [v['error_message'] for v in validators] 
                for field, validators in self.validators.items()}

# Global input validator instance
input_validator = InputValidator()