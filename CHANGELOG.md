# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Fixed
- **Critical auth bug**: Session cookies now use `path='/'` so authentication persists across all pages (alarms.html, dashboard.html, settings.html) after SSO callback or credential login
- **notify_cooldown=0 save bug**: Cooldown can now be set to 0 (immediate re-notification) instead of falling back to 3600
- **Settings UI race condition**: `initSettings()` now properly awaits `loadConfig()` before rendering
- **Audit logger NameError**: Added missing `from flask import request` import
- **Input validator syntax errors**: Fixed indentation in `add_date_validator` and `add_datetime_validator`

### Security
- **XSS prevention**: Escaped user-controlled data in `static/app.js` (IP addresses, scenario labels, URLs)
- **CSRF protection**: Applied `@csrf_protection.require_csrf` to all mutating API endpoints (POST/PATCH/DELETE)
- **Secure cookies**: Session cookies now set with `secure=True` in production (non-debug, non-testing environments)
- **Removed print() from audit logger**: Replaced with proper logging

### Changed
- **Renamed `app.py` → `main.py`**: Fixes Python module shadowing where `app.py` prevented the `app/` package from being imported
- **Module structure**: Added `__init__.py` files to `app/`, `app/middleware/`, and `app/security/` for proper package imports

### Infrastructure
- **CI image versioning**: Fixed YAML syntax error, now pushes `latest`, `sha-<8-char>`, and git tag versions to GHCR
- **Production hardening**: `UNSECURE=false` enforced in docker-compose.yml for production deployments
