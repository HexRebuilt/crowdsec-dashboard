#!/usr/bin/env python3
"""
CrowdSec Dashboard - Backend API
Reads from CrowdSec LAPI and sends notifications via Apprise.
Supports runtime-configurable thresholds, cooldowns, and digest mode.
Supports both embedded Apprise and external Apprise API.
Supports authentication via credentials or Auth0.
"""

import os
import json
import logging
import threading
import time
import hashlib
import secrets
import redis
from datetime import datetime, timedelta, timezone
from collections import deque
from functools import wraps

import requests
import apprise
from flask import Flask, jsonify, request, send_from_directory, make_response
from flask_cors import CORS

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_TIMEOUT = int(os.getenv("REDIS_TIMEOUT", "300"))

# Rate limiting configuration
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# Security configuration
CSRF_SECRET_KEY = os.getenv("CSRF_SECRET_KEY", secrets.token_hex(32))

# Audit logging configuration
AUDIT_LOG_ENABLED = os.getenv("AUDIT_LOG_ENABLED", "true").lower() == "true"
AUDIT_LOG_FILE = os.getenv("AUDIT_LOG_FILE", "/var/log/crowdsec-dashboard/audit.log")

# Boot-time config (from env)
CROWDSEC_URL       = os.getenv("CROWDSEC_URL", "http://crowdsec:8080")
CROWDSEC_API_KEY   = os.getenv("CROWDSEC_API_KEY", "")
CROWDSEC_LOGIN     = os.getenv("CROWDSEC_LOGIN", "")
CROWDSEC_PASSWORD  = os.getenv("CROWDSEC_PASSWORD", "")
APPRISE_URLS       = os.getenv("APPRISE_URLS", "")
APPRISE_CONFIG_URL = os.getenv("APPRISE_CONFIG_URL", "")
POLL_INTERVAL      = int(os.getenv("POLL_INTERVAL", "30"))
LOG_LEVEL          = os.getenv("LOG_LEVEL", "INFO")
UNSECURE           = os.getenv("UNSECURE", "false").lower() == "true"
APPRISE_API_URL    = os.getenv("APPRISE_API_URL", "")
APPRISE_API_KEY    = os.getenv("APPRISE_API_KEY", "")
APPRISE_CONFIG_KEY = os.getenv("APPRISE_CONFIG_KEY", "crowdsec-dashboard")

# Auth config
AUTH_USERNAME      = os.getenv("AUTH_USERNAME", "")
AUTH_PASSWORD      = os.getenv("AUTH_PASSWORD", "")
AUTH_SECRET_KEY    = os.getenv("AUTH_SECRET_KEY", secrets.token_hex(32))
AUTH0_DOMAIN       = os.getenv("AUTH0_DOMAIN", "")
AUTH0_CLIENT_ID    = os.getenv("AUTH0_CLIENT_ID", "")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "")

AUTH_PASSWORD_FILE = "/app/.auth_password"
DEFAULT_PASSWORDS = ["", "admin", "password", "changeme", "default", "secret", "123456", "admin123", "your_secure_password_here"]
APP_URL = os.getenv("APP_URL", "")

oidc_config = {}

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

def get_oidc_config():
    global oidc_config
    if oidc_config:
        return oidc_config
    
    if not AUTH0_DOMAIN:
        return None
    
    if AUTH0_DOMAIN.startswith('http://') or AUTH0_DOMAIN.startswith('https://'):
        discovery_url = AUTH0_DOMAIN
    else:
        if '/' in AUTH0_DOMAIN:
            base = AUTH0_DOMAIN
            discovery_url = f"https://{base}/.well-known/openid-configuration"
        else:
            discovery_url = f"https://{AUTH0_DOMAIN}/.well-known/openid-configuration"
    
    try:
        r = requests.get(discovery_url, timeout=10)
        if r.status_code == 200:
            oidc_config = r.json()
            log.info("OIDC discovery loaded: %s", oidc_config.get('issuer'))
            return oidc_config
    except Exception as e:
        log.error("Failed to fetch OIDC discovery: %s", e)
    return None

def generate_random_password(length=16):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(length))

def load_runtime_password():
    if os.path.exists(AUTH_PASSWORD_FILE):
        try:
            with open(AUTH_PASSWORD_FILE, "r") as f:
                return f.read().strip()
        except:
            pass
    return None

def save_runtime_password(password):
    try:
        with open(AUTH_PASSWORD_FILE, "w") as f:
            f.write(password)
        os.chmod(AUTH_PASSWORD_FILE, 0o600)
        return True
    except Exception as e:
        log.error("Failed to save password: %s", e)
        return False

def initialize_password():
    stored_password = load_runtime_password()
    if stored_password:
        return stored_password
    
    if AUTH_PASSWORD and AUTH_PASSWORD not in DEFAULT_PASSWORDS:
        return AUTH_PASSWORD
    
    random_password = generate_random_password()
    if save_runtime_password(random_password):
        log.info("=" * 60)
        log.info("GENERATED RANDOM PASSWORD (save this securely):")
        log.info("  Username: %s", AUTH_USERNAME or "admin")
        log.info("  Password: %s", random_password)
        log.info("=" * 60)
        return random_password
    
    return AUTH_PASSWORD

CURRENT_PASSWORD = initialize_password()

AUTH_CREDENTIALS_ENABLED = bool(AUTH_USERNAME and CURRENT_PASSWORD)
AUTH_AUTH0_ENABLED = bool(AUTH0_DOMAIN and AUTH0_CLIENT_ID)
AUTH_ENABLED = AUTH_CREDENTIALS_ENABLED or AUTH_AUTH0_ENABLED

app = Flask(__name__, static_folder="static")
CORS(app, supports_credentials=True)

# Session configuration
SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "1800"))
SESSION_MAX_AGE = int(os.getenv("SESSION_MAX_AGE", "86400"))

# Session storage
sessions = {}

def create_session(username):
    token = secrets.token_urlsafe(32)
    sessions[token] = {
        "username": username,
        "created": time.time(),
        "expires": time.time() + SESSION_MAX_AGE,
        "last_activity": time.time()
    }
    return token

def validate_session(token):
    if not token:
        return None
    session = sessions.get(token)
    if not session:
        return None
    if time.time() > session["expires"]:
        sessions.pop(token, None)
        return None
    if SESSION_TIMEOUT > 0:
        last_activity = session.get("last_activity", session["created"])
        if time.time() - last_activity > SESSION_TIMEOUT:
            sessions.pop(token, None)
            return None
        session["last_activity"] = time.time()
    return session["username"]

def cleanup_sessions():
    now = time.time()
    expired = [t for t, s in sessions.items() if now > s["expires"] or (SESSION_TIMEOUT > 0 and now - s.get("last_activity", s["created"]) > SESSION_TIMEOUT)]
    for t in expired:
        sessions.pop(t, None)

def session_cleanup_loop():
    while True:
        time.sleep(60)
        cleanup_sessions()

# Rate limiting middleware
class RateLimiter:
    def __init__(self):
        self.redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        self.request_count = 0
        self.window_start = time.time()
    
    def is_allowed(self, identifier):
        current_time = time.time()
        window_key = f"rate_limit:{identifier}:{int(current_time // RATE_LIMIT_WINDOW)}"
        
        try:
            count = self.redis.incr(window_key)
            if count == 1:
                self.redis.expire(window_key, RATE_LIMIT_WINDOW)
            
            if count > RATE_LIMIT_REQUESTS:
                return False
            return True
        except redis.RedisError as e:
            log.warning("Rate limiting Redis error: %s", e)
            return True
    
    def get_count(self, identifier):
        current_time = time.time()
        window_key = f"rate_limit:{identifier}:{int(current_time // RATE_LIMIT_WINDOW)}"
        try:
            return int(self.redis.get(window_key) or 0)
        except redis.RedisError:
            return 0

# Initialize rate limiter
rate_limiter = RateLimiter()

def rate_limit(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        client_ip = request.remote_addr
        user_agent = request.headers.get("User-Agent", "unknown")
        identifier = f"{client_ip}:{user_agent}"
        
        if not rate_limiter.is_allowed(identifier):
            log.warning("Rate limit exceeded for %s", client_ip)
            track_rate_limit_warning(client_ip, request.path)
            return jsonify({
                "error": "Rate limit exceeded",
                "retry_after": RATE_LIMIT_WINDOW
            }), 429
        
        response = f(*args, **kwargs)
        if isinstance(response, tuple) and len(response) == 3:
            resp, status, headers = response
            headers["X-RateLimit-Limit"] = str(RATE_LIMIT_REQUESTS)
            headers["X-RateLimit-Remaining"] = str(max(0, RATE_LIMIT_REQUESTS - rate_limiter.get_count(identifier)))
            headers["X-RateLimit-Reset"] = str(int((time.time() // RATE_LIMIT_WINDOW + 1) * RATE_LIMIT_WINDOW))
            return resp, status, headers
        elif hasattr(response, "headers"):
            response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_REQUESTS)
            response.headers["X-RateLimit-Remaining"] = str(max(0, RATE_LIMIT_REQUESTS - rate_limiter.get_count(identifier)))
            response.headers["X-RateLimit-Reset"] = str(int((time.time() // RATE_LIMIT_WINDOW + 1) * RATE_LIMIT_WINDOW))
        return response
    return decorated

# IP whitelist configuration
IP_WHITELIST_ENABLED = os.getenv("IP_WHITELIST_ENABLED", "false").lower() == "true"
IP_WHITELIST = os.getenv("IP_WHITELIST", "").split(",")
IP_WHITELIST = [ip.strip() for ip in IP_WHITELIST if ip.strip()]

# IP whitelist decorator
def ip_whitelist_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not IP_WHITELIST_ENABLED:
            return f(*args, **kwargs)
        
        client_ip = request.remote_addr
        if client_ip in IP_WHITELIST:
            return f(*args, **kwargs)
        
        log.warning("IP whitelist blocked access from %s", client_ip)
        return jsonify({"error": "Access denied", "message": "IP not in whitelist"}), 403
    return decorated

# Audit logging functions
def audit_log(username, action, details=None):
    if not AUDIT_LOG_ENABLED:
        return
    
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "username": username,
        "action": action,
        "details": details or {},
        "client_ip": request.remote_addr if "request" in globals() else "unknown",
        "user_agent": request.headers.get("User-Agent", "unknown") if "request" in globals() else "unknown"
    }
    
    try:
        with open(AUDIT_LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        log.error("Failed to write audit log: %s", e)

# Audit logging decorator
def audit_logged(action):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = get_token_from_request()
            username = validate_session(token) if token else "anonymous"
            result = f(*args, **kwargs)
            
            # Log successful actions
            if isinstance(result, tuple):
                status_code = result[1] if len(result) > 1 else 200
                if status_code < 400:
                    audit_log(username, action, {"status": status_code})
            elif hasattr(result, "status_code"):
                if result.status_code < 400:
                    audit_log(username, action, {"status": result.status_code})
            else:
                audit_log(username, action, {"status": 200})
            
            return result
        return decorated
    return decorator

def get_token_from_request():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return request.cookies.get("session_token")

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not AUTH_ENABLED:
            return f(*args, **kwargs)
        
        token = get_token_from_request()
        username = validate_session(token)
        
        if not username:
            return jsonify({"error": "Unauthorized", "authenticated": False}), 401
        return f(*args, **kwargs)
    return decorated

# ---------------------------------------------------------------------------
# Runtime config — editable via /api/config without restart
# ---------------------------------------------------------------------------
cfg = {
    "notify_on_ban":      os.getenv("NOTIFY_ON_BAN", "true").lower() == "true",
    "notify_on_alert":    os.getenv("NOTIFY_ON_ALERT", "true").lower() == "true",
    "alert_threshold":    int(os.getenv("ALERT_THRESHOLD", "10")),
    "ban_threshold":      int(os.getenv("BAN_THRESHOLD", "50")),
    "notify_cooldown":    int(os.getenv("NOTIFY_COOLDOWN", "3600")),
    "digest_interval":    int(os.getenv("DIGEST_INTERVAL", "0")),
    "apprise_urls":       os.getenv("APPRISE_URLS", ""),
}

# ---------------------------------------------------------------------------
# Alarm data structures
# ---------------------------------------------------------------------------
from enum import Enum

class AlarmSeverity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class AlarmStatus(Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

class Alarm:
    def __init__(self, alert_id, severity, ip, scenario, events_count, message, source):
        self.id = str(alert_id)
        self.severity = severity
        self.status = AlarmStatus.ACTIVE
        self.ip = ip
        self.scenario = scenario
        self.events_count = events_count
        self.message = message
        self.source = source
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.updated_at = self.created_at
        self.acknowledged_at = None
        self.acknowledged_by = None
        self.correlation_id = self._generate_correlation_id()

    def _generate_correlation_id(self):
        return hashlib.sha256(f"{self.ip}_{self.scenario}".encode()).hexdigest()

    def acknowledge(self, username):
        self.status = AlarmStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.now(timezone.utc).isoformat()
        self.acknowledged_by = username
        self.updated_at = self.acknowledged_at

    def resolve(self):
        self.status = AlarmStatus.RESOLVED
        self.updated_at = datetime.now(timezone.utc).isoformat()

# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------
state = {
    "decisions":           [],
    "alerts":              [],
    "alarms":              [],
    "metrics":             {},
    "last_poll":           None,
    "poll_errors":         0,
    "known_decision_ids":  set(),
    "known_alert_ids":     set(),
    "known_alarm_ids":     set(),
    "events":              deque(maxlen=500),
    "cooldowns":           {},
    "suppressed_count":    0,
    "sent_count":          0,
    "digest_buffer":       [],
    "last_digest_sent":    time.time(),
    "alarm_correlations":  {},
    "known_ips":           set(),
    "known_countries":     set(),
    "failed_logins":       {},
    "api_errors":          [],
    "whitelist_expiry":    {},
    "rate_limit_warnings": [],
}

STATEfulness_lookback_days = 30
FAILED_LOGIN_THRESHOLD = 5
FAILED_LOGIN_WINDOW = 600
API_ERROR_THRESHOLD = 2
WHITELIST_EXPIRY_DAYS = 7

# ---------------------------------------------------------------------------
# Alarm correlation and severity logic
# ---------------------------------------------------------------------------
def _determine_alarm_severity(alert):
    events_count = alert.get("events_count", 0)
    scenario = alert.get("scenario", "")
    
    if "fail2ban" in scenario.lower() or "ssh" in scenario.lower():
        if events_count >= 50:
            return AlarmSeverity.CRITICAL
        elif events_count >= 20:
            return AlarmSeverity.WARNING
        else:
            return AlarmSeverity.INFO
    elif "web" in scenario.lower() or "http" in scenario.lower():
        if events_count >= 100:
            return AlarmSeverity.CRITICAL
        elif events_count >= 50:
            return AlarmSeverity.WARNING
        else:
            return AlarmSeverity.INFO
    elif "portscan" in scenario.lower() or "recon" in scenario.lower():
        if events_count >= 10:
            return AlarmSeverity.CRITICAL
        elif events_count >= 5:
            return AlarmSeverity.WARNING
        else:
            return AlarmSeverity.INFO
    elif events_count >= 100:
        return AlarmSeverity.CRITICAL
    elif events_count >= 50:
        return AlarmSeverity.WARNING
    else:
        return AlarmSeverity.INFO

# ---------------------------------------------------------------------------
# Actionable Alarms - Only items requiring user action
# ---------------------------------------------------------------------------

class ActionableAlarmType:
    NEW_ATTACK_SOURCE = "new_attack_source"
    MANUAL_REVIEW = "manual_review"
    WHITELIST_EXPIRY = "whitelist_expiry"
    FAILED_LOGIN_PATTERN = "failed_login_pattern"
    API_CONNECTION_ERROR = "api_connection_error"
    GEO_ANOMALY = "geo_anomaly"
    RATE_LIMIT_WARNING = "rate_limit_warning"

def _check_new_attack_sources(decisions):
    new_ips = set()
    for d in decisions:
        ip = d.get("value")
        if ip and ip != "—" and ip not in state["known_ips"]:
            new_ips.add(ip)
    
    if new_ips:
        state["known_ips"].update(new_ips)
        return {
            "type": ActionableAlarmType.NEW_ATTACK_SOURCE,
            "severity": AlarmSeverity.WARNING,
            "count": len(new_ips),
            "ips": list(new_ips)[:10],
            "message": f"{len(new_ips)} new attack source(s) detected - never seen in {STATEfulness_lookback_days} days",
            "requires_action": True,
        }
    return None

def _check_manual_review_alerts(alerts):
    review_needed = []
    for a in alerts:
        scenario = a.get("scenario", "")
        events_count = a.get("events_count", 0)
        ip = (a.get("source") or {}).get("ip", "?")
        
        if events_count >= cfg["alert_threshold"] * 0.5 and events_count < cfg["alert_threshold"]:
            review_needed.append({
                "id": a.get("id"),
                "ip": ip,
                "scenario": scenario,
                "events": events_count,
            })
    
    if review_needed:
        return {
            "type": ActionableAlarmType.MANUAL_REVIEW,
            "severity": AlarmSeverity.INFO,
            "count": len(review_needed),
            "alerts": review_needed[:10],
            "message": f"{len(review_needed)} alert(s) need manual review - near threshold",
            "requires_action": True,
        }
    return None

def _check_failed_login_pattern():
    now = time.time()
    window_start = now - FAILED_LOGIN_WINDOW
    
    recent_failures = {
        ip: list(timestamps)
        for ip, timestamps in state["failed_logins"].items()
        if any(ts > window_start for ts in timestamps)
    }
    
    suspicious_ips = []
    for ip, timestamps in recent_failures.items():
        recent = [ts for ts in timestamps if ts > window_start]
        if len(recent) >= FAILED_LOGIN_THRESHOLD:
            suspicious_ips.append({"ip": ip, "attempts": len(recent), "window": f"{FAILED_LOGIN_WINDOW//60}min"})
    
    if suspicious_ips:
        return {
            "type": ActionableAlarmType.FAILED_LOGIN_PATTERN,
            "severity": AlarmSeverity.CRITICAL,
            "count": len(suspicious_ips),
            "ips": suspicious_ips,
            "message": f"{len(suspicious_ips)} IP(s) with {FAILED_LOGIN_THRESHOLD}+ failed logins in {FAILED_LOGIN_WINDOW//60} minutes",
            "requires_action": True,
        }
    return None

def _check_api_connection_errors():
    now = time.time()
    window_start = now - 300
    
    recent_errors = [e for e in state["api_errors"] if e.get("timestamp", 0) > window_start]
    
    if len(recent_errors) >= API_ERROR_THRESHOLD:
        return {
            "type": ActionableAlarmType.API_CONNECTION_ERROR,
            "severity": AlarmSeverity.CRITICAL,
            "count": len(recent_errors),
            "errors": recent_errors[-5:],
            "message": f"{len(recent_errors)} CrowdSec API connection failures detected - system may be unavailable",
            "requires_action": True,
        }
    return None

def _check_geo_anomalies(decisions):
    current_countries = set()
    for d in decisions:
        country = d.get("origin", "unknown")
        if country and country != "—":
            current_countries.add(country)
    
    new_countries = current_countries - state["known_countries"]
    
    if new_countries and state["known_countries"]:
        state["known_countries"].update(new_countries)
        return {
            "type": ActionableAlarmType.GEO_ANOMALY,
            "severity": AlarmSeverity.WARNING,
            "count": len(new_countries),
            "countries": list(new_countries),
            "message": f"Attacks from new country/region: {', '.join(new_countries)} (not seen in {STATEfulness_lookback_days} days)",
            "requires_action": True,
        }
    
    if not state["known_countries"] and current_countries:
        state["known_countries"] = current_countries
    
    return None

def _check_rate_limit_warnings():
    if state["rate_limit_warnings"]:
        warnings = state["rate_limit_warnings"][-10:]
        return {
            "type": ActionableAlarmType.RATE_LIMIT_WARNING,
            "severity": AlarmSeverity.WARNING,
            "count": len(warnings),
            "warnings": warnings,
            "message": f"Application rate limits triggered {len(warnings)} times - possible DoS attack",
            "requires_action": True,
        }
    return None

def _check_whitelist_expiry():
    expiring = []
    now = datetime.now(timezone.utc)
    expiry_threshold = now + timedelta(days=WHITELIST_EXPIRY_DAYS)
    
    for ip, expiry_info in state.get("whitelist_expiry", {}).items():
        if isinstance(expiry_info, dict):
            expiry_date = expiry_info.get("expires")
            if expiry_date:
                try:
                    if isinstance(expiry_date, str):
                        expiry_dt = datetime.fromisoformat(expiry_date.replace("Z", "+00:00"))
                    else:
                        expiry_dt = expiry_date
                    
                    if expiry_dt <= expiry_threshold:
                        expiring.append({
                            "ip": ip,
                            "expires": expiry_info.get("expires"),
                            "reason": expiry_info.get("reason", "manual"),
                        })
                except:
                    pass
    
    if expiring:
        return {
            "type": ActionableAlarmType.WHITELIST_EXPIRY,
            "severity": AlarmSeverity.WARNING,
            "count": len(expiring),
            "entries": expiring,
            "message": f"{len(expiring)} whitelist(s) expiring within {WHITELIST_EXPIRY_DAYS} days - renew to maintain protection",
            "requires_action": True,
        }
    return None

def _check_all_actionable_alarms():
    alarms = []
    
    new_attack = _check_new_attack_sources(state["decisions"])
    if new_attack:
        alarms.append(new_attack)
    
    manual_review = _check_manual_review_alerts(state["alerts"])
    if manual_review:
        alarms.append(manual_review)
    
    failed_login = _check_failed_login_pattern()
    if failed_login:
        alarms.append(failed_login)
    
    api_error = _check_api_connection_errors()
    if api_error:
        alarms.append(api_error)
    
    geo_anomaly = _check_geo_anomalies(state["decisions"])
    if geo_anomaly:
        alarms.append(geo_anomaly)
    
    rate_limit = _check_rate_limit_warnings()
    if rate_limit:
        alarms.append(rate_limit)
    
    whitelist_expiry = _check_whitelist_expiry()
    if whitelist_expiry:
        alarms.append(whitelist_expiry)
    
    return alarms

# Track failed login attempts
def track_failed_login(ip):
    now = time.time()
    if ip not in state["failed_logins"]:
        state["failed_logins"][ip] = []
    state["failed_logins"][ip].append(now)
    
    cutoff = now - (FAILED_LOGIN_WINDOW * 2)
    state["failed_logins"][ip] = [ts for ts in state["failed_logins"][ip] if ts > cutoff]

def track_api_error(error_type, message):
    now = time.time()
    state["api_errors"].append({
        "timestamp": now,
        "type": error_type,
        "message": message,
    })
    
    cutoff = now - 3600
    state["api_errors"] = [e for e in state["api_errors"] if e.get("timestamp", 0) > cutoff]

def track_rate_limit_warning(ip, path):
    now = time.time()
    state["rate_limit_warnings"].append({
        "timestamp": now,
        "ip": ip,
        "path": path,
    })
    
    cutoff = now - 3600
    state["rate_limit_warnings"] = [w for w in state["rate_limit_warnings"] if w.get("timestamp", 0) > cutoff]

def add_whitelist_entry(ip, expires=None, reason="manual"):
    state.setdefault("whitelist_expiry", {})[ip] = {
        "expires": expires,
        "reason": reason,
        "added": datetime.now(timezone.utc).isoformat(),
    }

def remove_whitelist_entry(ip):
    state.get("whitelist_expiry", {}).pop(ip, None)

# ---------------------------------------------------------------------------
# Notification logic
# ---------------------------------------------------------------------------

def _get_apprise_urls():
    if APPRISE_API_URL:
        return []
    if APPRISE_CONFIG_URL:
        try:
            r = requests.get(APPRISE_CONFIG_URL, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list):
                    return data
                if isinstance(data, dict) and "urls" in data:
                    return data["urls"]
                if isinstance(data, dict) and "url" in data:
                    return [data["url"]]
                if isinstance(data, dict):
                    urls = []
                    for key in ["urls", "notification_urls", "services"]:
                        if key in data and isinstance(data[key], list):
                            urls.extend(data[key])
                    return urls
        except Exception as e:
            log.error("Failed to fetch Apprise config URL: %s", e)
    urls_str = cfg["apprise_urls"] or APPRISE_URLS
    return [u.strip() for u in urls_str.split(",") if u.strip()]

def _apprise_api_headers():
    headers = {"Content-Type": "application/json"}
    if APPRISE_API_KEY:
        headers["Authorization"] = f"Bearer {APPRISE_API_KEY}"
    return headers

def _apprise_api_get_urls():
    if not APPRISE_API_URL:
        return []
    try:
        r = requests.get(
            f"{APPRISE_API_URL}/get/{APPRISE_CONFIG_KEY}",
            headers=_apprise_api_headers(),
            timeout=5,
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("urls"):
                return data["urls"]
    except Exception as e:
        log.debug("Apprise API get URLs error: %s", e)
    return []

def _apprise_api_set_urls(urls):
    if not APPRISE_API_URL:
        return False
    try:
        r = requests.post(
            f"{APPRISE_API_URL}/add/{APPRISE_CONFIG_KEY}",
            headers=_apprise_api_headers(),
            json={"urls": urls},
            timeout=5,
        )
        return r.status_code in (200, 201, 204)
    except Exception as e:
        log.error("Apprise API set URLs error: %s", e)
        return False

def _apprise_api_notify(title, body):
    if not APPRISE_API_URL:
        return False
    try:
        r = requests.post(
            f"{APPRISE_API_URL}/notify/{APPRISE_CONFIG_KEY}",
            headers=_apprise_api_headers(),
            json={"title": title, "body": body, "type": "info"},
            timeout=10,
        )
        ok = r.status_code == 200
        log.info("Apprise API notify '%s' -> %s", title, "ok" if ok else "FAIL")
        return ok
    except Exception as e:
        log.error("Apprise API notify error: %s", e)
        return False

def _send_now(title, body):
    if APPRISE_API_URL:
        ok = _apprise_api_notify(title, body)
        if ok:
            state["sent_count"] += 1
        return ok
    
    urls = _get_apprise_urls()
    if not urls:
        log.debug("No Apprise URLs configured, skipping.")
        return False
    ap = apprise.Apprise()
    for url in urls:
        ap.add(url)
    ok = ap.notify(title=title, body=body)
    log.info("Notification '%s' -> %s", title, "ok" if ok else "FAIL")
    state["sent_count"] += 1
    return ok

def send_notification(title, body, ip=None):
    now = time.time()
    if ip and cfg["notify_cooldown"] > 0:
        last = state["cooldowns"].get(ip, 0)
        if now - last < cfg["notify_cooldown"]:
            log.debug("Suppressed notification for %s (cooldown)", ip)
            state["suppressed_count"] += 1
            state["events"].appendleft({
                "time": datetime.now(timezone.utc).isoformat(),
                "type": "suppressed",
                "msg": f"Suppressed (cooldown {cfg['notify_cooldown']}s) for {ip}",
                "data": {},
            })
            return
        state["cooldowns"][ip] = now

    if cfg["digest_interval"] > 0:
        state["digest_buffer"].append((title, body))
        log.debug("Buffered for digest: %s", title)
        return

    _send_now(title, body)


def digest_loop():
    while True:
        time.sleep(5)
        interval = cfg["digest_interval"]
        if interval <= 0:
            continue
        now = time.time()
        if now - state["last_digest_sent"] < interval:
            continue
        buf = state["digest_buffer"][:]
        if not buf:
            state["last_digest_sent"] = now
            continue
        state["digest_buffer"].clear()
        state["last_digest_sent"] = now
        if len(buf) == 1:
            _send_now(buf[0][0], buf[0][1])
        else:
            lines = "\n\n".join(f"- {t}\n{b}" for t, b in buf)
            _send_now(f"CrowdSec Digest — {len(buf)} events", lines)
        log.info("Digest sent: %d notifications", len(buf))

# ---------------------------------------------------------------------------
# CrowdSec LAPI helpers
# ---------------------------------------------------------------------------
_crowdsec_token = None
_crowdsec_token_expires = 0

def cs_headers():
    return {"X-Api-Key": CROWDSEC_API_KEY, "Accept": "application/json"}

def cs_auth():
    global _crowdsec_token, _crowdsec_token_expires
    if CROWDSEC_LOGIN and CROWDSEC_PASSWORD:
        import time
        if not _crowdsec_token or time.time() >= _crowdsec_token_expires - 60:
            try:
                login_data = {
                    "machine_id": CROWDSEC_LOGIN,
                    "password": CROWDSEC_PASSWORD
                }
                r = requests.post(
                    f"{CROWDSEC_URL}/v1/watchers/login",
                    json=login_data,
                    headers={"Accept": "application/json"},
                    timeout=10
                )
                if r.status_code == 200:
                    data = r.json()
                    _crowdsec_token = data.get("token")
                    expire_str = data.get("expire", "")
                    if expire_str:
                        from datetime import datetime, timezone
                        try:
                            exp_dt = datetime.fromisoformat(expire_str.replace("Z", "+00:00"))
                            _crowdsec_token_expires = exp_dt.timestamp()
                        except:
                            _crowdsec_token_expires = time.time() + 3600
                    else:
                        _crowdsec_token_expires = time.time() + 3600
                else:
                    log.warning("CrowdSec login failed: %s", r.status_code)
            except Exception as e:
                log.error("CrowdSec login error: %s", e)
        
        if _crowdsec_token:
            return {"Authorization": f"Bearer {_crowdsec_token}"}
    return None

def _parse_duration_to_seconds(duration_str):
    if not duration_str:
        return 0
    try:
        duration_str = str(duration_str).strip()
        seconds = 0
        temp = ""
        for c in duration_str:
            if c.isdigit():
                temp += c
            elif c == 'h' and temp:
                seconds += int(temp) * 3600
                temp = ""
            elif c == 'm' and temp:
                seconds += int(temp) * 60
                temp = ""
            elif c == 's' and temp:
                seconds += int(temp)
                temp = ""
            elif c == 'd' and temp:
                seconds += int(temp) * 86400
                temp = ""
        if temp:
            seconds += int(temp)
        return seconds
    except (ValueError, AttributeError):
        return 0

def fetch_decisions():
    try:
        r = requests.get(f"{CROWDSEC_URL}/v1/decisions", headers=cs_headers(), timeout=10)
        if r.status_code == 200:
            decisions = r.json() or []
            transformed = []
            now = datetime.now(timezone.utc)
            for d in decisions:
                until_str = d.get("until")
                created_at = d.get("created_at") or d.get("start_at")
                duration_val = d.get("duration")
                if not created_at and duration_val:
                    try:
                        seconds = _parse_duration_to_seconds(duration_val)
                        if seconds > 0:
                            created_dt = now - timedelta(seconds=seconds)
                            created_at = created_dt.isoformat()
                    except:
                        pass
                if not created_at and until_str:
                    try:
                        until_dt = datetime.fromisoformat(until_str.replace("Z", "+00:00"))
                        if duration_val:
                            seconds = _parse_duration_to_seconds(duration_val)
                            if seconds > 0:
                                created_dt = until_dt - timedelta(seconds=seconds)
                                created_at = created_dt.isoformat()
                    except:
                        pass
                transformed.append({
                    "id": d.get("id"),
                    "ip": d.get("value", "—"),
                    "type": d.get("type", "ban"),
                    "scenario": d.get("scenario", "—"),
                    "origin": d.get("origin", "—"),
                    "duration": _format_duration(until_str) if until_str else _format_duration_from_now(duration_val, now),
                    "until": until_str,
                    "value": d.get("value"),
                    "created_at": created_at,
                })
            return transformed
        log.warning("GET /v1/decisions -> %s", r.status_code)
        track_api_error("decisions_http", f"HTTP {r.status_code}")
    except Exception as e:
        log.error("fetch_decisions: %s", e)
        track_api_error("decisions_exception", str(e))
    return None

def _format_duration(until_str):
    if not until_str:
        return "—"
    try:
        until = datetime.fromisoformat(until_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = until - now
        if diff.total_seconds() <= 0:
            return "expired"
        hours = int(diff.total_seconds() // 3600)
        minutes = int((diff.total_seconds() % 3600) // 60)
        if hours > 24:
            days = hours // 24
            return f"{days}d {hours % 24}h"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except Exception:
        return "—"

def _format_duration_from_now(duration_str, now):
    if not duration_str:
        return "—"
    try:
        seconds = _parse_duration_to_seconds(duration_str)
        if seconds <= 0:
            return "expired"
        diff = timedelta(seconds=seconds)
        hours = int(diff.total_seconds() // 3600)
        minutes = int((diff.total_seconds() % 3600) // 60)
        if hours > 24:
            days = hours // 24
            return f"{days}d {hours % 24}h"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except Exception:
        return "—"

def fetch_alerts(since_minutes=120):
    try:
        since = f"{since_minutes}m"
        headers = cs_headers()
        auth = cs_auth()
        if auth:
            headers.update(auth)
        r = requests.get(f"{CROWDSEC_URL}/v1/alerts", headers=headers, params={"since": since}, timeout=10)
        if r.status_code == 200:
            return r.json() or []
        log.warning("GET /v1/alerts -> %s", r.status_code)
        track_api_error("alerts_http", f"HTTP {r.status_code}")
    except Exception as e:
        log.error("fetch_alerts: %s", e)
        track_api_error("alerts_exception", str(e))
    return None

def fetch_metrics():
    try:
        r = requests.get(f"{CROWDSEC_URL}/metrics", timeout=10)
        if r.status_code == 200:
            metrics = {}
            for line in r.text.splitlines():
                if line.startswith("#") or not line.strip():
                    continue
                parts = line.split(" ")
                if len(parts) >= 2:
                    key = parts[0].split("{")[0]
                    try:
                        metrics[key] = float(parts[-1])
                    except ValueError:
                        pass
            return metrics
    except Exception as e:
        log.debug("fetch_metrics: %s", e)
    return {}

# ---------------------------------------------------------------------------
# Poll loop
# ---------------------------------------------------------------------------
def poll_loop():
    log.info("Poller started (interval=%ds)", POLL_INTERVAL)
    while True:
        try:
            _do_poll()
        except Exception as e:
            log.exception("Poll loop error: %s", e)
            state["poll_errors"] += 1
        time.sleep(POLL_INTERVAL)

def _do_poll():
    now_str = datetime.now(timezone.utc).isoformat()
    state["last_poll"] = now_str

    decisions = fetch_decisions()
    if decisions is not None:
        new_ids = {str(d.get("id", "")) for d in decisions}
        added   = new_ids - state["known_decision_ids"]
        removed = state["known_decision_ids"] - new_ids

        state["decisions"] = decisions
        state["known_decision_ids"] = new_ids

        for d in decisions:
            if str(d.get("id", "")) in added:
                ip       = d.get("value", "?")
                scenario = d.get("scenario", "?")
                dtype    = d.get("type", "?")
                origin   = d.get("origin", "?")
                msg = f"BAN {ip} [{dtype}] via {origin} - {scenario}"
                state["events"].appendleft({"time": now_str, "type": "ban", "msg": msg, "data": d})

                if cfg["notify_on_ban"]:
                    ban_thr = cfg["ban_threshold"]
                    event_count = _find_alert_count(ip, scenario)
                    if ban_thr > 0 and event_count < ban_thr:
                        log.debug("Ban notify suppressed: %s events < threshold %s", event_count, ban_thr)
                        state["suppressed_count"] += 1
                    else:
                        send_notification(
                            title=f"CrowdSec Ban: {ip}",
                            body=f"Scenario: {scenario}\nType: {dtype}\nOrigin: {origin}\nExpires: {d.get('until','?')}",
                            ip=ip,
                        )

        for rid in removed:
            state["events"].appendleft({
                "time": now_str, "type": "unban",
                "msg": f"UNBAN decision id={rid}", "data": {},
            })

    alerts = fetch_alerts(since_minutes=120)
    if alerts is not None:
        new_alert_ids = {str(a.get("id", "")) for a in alerts}
        added_alerts  = new_alert_ids - state["known_alert_ids"]

        for a in alerts:
            if str(a.get("id", "")) in added_alerts:
                scenario = a.get("scenario", "?")
                ip       = (a.get("source") or {}).get("ip", "?")
                count    = a.get("events_count", 0)
                msg = f"ALERT {ip} scenario={scenario} events={count}"
                state["events"].appendleft({"time": now_str, "type": "alert", "msg": msg, "data": a})

                if cfg["notify_on_alert"]:
                    thr = cfg["alert_threshold"]
                    if thr > 0 and count < thr:
                        log.debug("Alert suppressed: %s events < threshold %s", count, thr)
                        state["suppressed_count"] += 1
                    else:
                        send_notification(
                            title=f"CrowdSec Alert: {scenario}",
                            body=f"IP: {ip}\nEvents: {count}\nMessage: {a.get('message','')}",
                            ip=ip,
                        )

        state["known_alert_ids"] = new_alert_ids
        state["alerts"] = alerts[:100]

    state["metrics"] = fetch_metrics()
    _prune_cooldowns()

def _find_alert_count(ip, scenario):
    for a in state["alerts"]:
        a_ip = (a.get("source") or {}).get("ip", "")
        if a_ip == ip and a.get("scenario", "") == scenario:
            return a.get("events_count", 0)
    return 0

def _prune_cooldowns():
    cutoff = time.time() - cfg["notify_cooldown"] * 2
    state["cooldowns"] = {k: v for k, v in state["cooldowns"].items() if v > cutoff}

# ---------------------------------------------------------------------------
# Auth API
# ---------------------------------------------------------------------------
@app.route("/api/auth/status")
@rate_limit
@ip_whitelist_required
@audit_logged("auth_status")
def api_auth_status():
    oidc = get_oidc_config()
    return jsonify({
        "enabled": AUTH_ENABLED,
        "method": "auth0" if AUTH_AUTH0_ENABLED else "credentials" if AUTH_CREDENTIALS_ENABLED else None,
        "auth0_domain": AUTH0_DOMAIN if AUTH0_DOMAIN else None,
        "auth0_client_id": AUTH0_CLIENT_ID if AUTH0_CLIENT_ID else None,
        "auth0_authorize_url": oidc.get("authorization_endpoint") if oidc else None,
        "auth0_token_url": oidc.get("token_endpoint") if oidc else None,
        "app_url": APP_URL,
        "password_change_available": AUTH_CREDENTIALS_ENABLED and not AUTH_AUTH0_ENABLED,
    })

@app.route("/api/auth/config")
@rate_limit
@auth_required
@ip_whitelist_required
@audit_logged("auth_config")
def api_auth_config():
    return jsonify({
        "enabled": AUTH_ENABLED,
        "method": "auth0" if AUTH_AUTH0_ENABLED else "credentials" if AUTH_CREDENTIALS_ENABLED else None,
        "credentials": {
            "enabled": AUTH_CREDENTIALS_ENABLED,
            "username": AUTH_USERNAME if AUTH_CREDENTIALS_ENABLED else None,
            "password_set": bool(load_runtime_password()) if AUTH_CREDENTIALS_ENABLED else False,
        },
        "auth0": {
            "enabled": AUTH_AUTH0_ENABLED,
            "domain": AUTH0_DOMAIN if AUTH_AUTH0_ENABLED else None,
            "client_id": AUTH0_CLIENT_ID if AUTH_AUTH0_ENABLED else None,
        },
    })

@app.route("/api/auth/login", methods=["POST"])
@rate_limit
@ip_whitelist_required
@audit_logged("auth_login")
def api_auth_login():
    data = request.get_json(force=True, silent=True) or {}
    
    if AUTH0_DOMAIN and AUTH0_CLIENT_ID:
        access_token = data.get("access_token")
        if not access_token:
            return jsonify({"error": "Access token required"}), 400
        
        try:
            oidc = get_oidc_config()
            if oidc and oidc.get("userinfo_endpoint"):
                userinfo_url = oidc["userinfo_endpoint"]
            elif AUTH0_DOMAIN.startswith('http'):
                userinfo_url = AUTH0_DOMAIN.replace('.well-known/openid-configuration', 'userinfo')
            else:
                userinfo_url = f"https://{AUTH0_DOMAIN}/userinfo"
            
            userinfo = requests.get(
                userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10
            )
            if userinfo.status_code != 200:
                return jsonify({"error": "Invalid token"}), 401
            
            user_data = userinfo.json()
            username = user_data.get("email") or user_data.get("sub", "user")
            token = create_session(username)
            
            response = make_response(jsonify({"ok": True, "username": username}))
            response.set_cookie("session_token", token, httponly=True, samesite="Lax", max_age=86400)
            return response
        except Exception as e:
            log.error("Auth0 login error: %s", e)
            return jsonify({"error": "Auth0 error"}), 500
    
    if AUTH_CREDENTIALS_ENABLED:
        username = data.get("username", "")
        password = data.get("password", "")
        
        runtime_password = load_runtime_password()
        
        if username == AUTH_USERNAME and password == runtime_password:
            token = create_session(username)
            response = make_response(jsonify({"ok": True, "username": username}))
            response.set_cookie("session_token", token, httponly=True, samesite="Lax", max_age=86400)
            return response
        
        return jsonify({"error": "Invalid credentials"}), 401
    
    return jsonify({"error": "Auth not configured"}), 400

@app.route("/api/auth/callback", methods=["POST"])
@rate_limit
@ip_whitelist_required
@audit_logged("auth_callback")
def api_auth_callback():
    data = request.get_json(force=True, silent=True) or {}
    code = data.get("code")
    redirect_uri = data.get("redirect_uri")
    
    if not code:
        return jsonify({"error": "Authorization code required"}), 400
    
    oidc = get_oidc_config()
    if not oidc:
        return jsonify({"error": "OIDC not configured"}), 400
    
    token_url = oidc.get("token_endpoint")
    if not token_url:
        return jsonify({"error": "Token endpoint not found in OIDC config"}), 400
    
    try:
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": AUTH0_CLIENT_ID,
            "client_secret": AUTH0_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
        }
        
        token_resp = requests.post(token_url, data=token_data, timeout=10)
        if token_resp.status_code != 200:
            log.error("Token exchange failed: %s - %s", token_resp.status_code, token_resp.text)
            return jsonify({"error": "Token exchange failed"}), 401
        
        tokens = token_resp.json()
        access_token = tokens.get("access_token")
        if not access_token:
            return jsonify({"error": "No access token in response"}), 400
        
        userinfo_url = oidc.get("userinfo_endpoint")
        if not userinfo_url:
            return jsonify({"error": "Userinfo endpoint not found"}), 400
        
        userinfo = requests.get(
            userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        if userinfo.status_code != 200:
            return jsonify({"error": "Failed to fetch user info"}), 401
        
        user_data = userinfo.json()
        username = user_data.get("email") or user_data.get("sub", "user")
        token = create_session(username)
        
        response = make_response(jsonify({"ok": True, "username": username}))
        response.set_cookie("session_token", token, httponly=True, samesite="Lax", max_age=86400)
        return response
    except Exception as e:
        log.error("OAuth callback error: %s", e)
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/logout", methods=["POST"])
@rate_limit
@auth_required
@audit_logged("auth_logout")
def api_auth_logout():
    token = get_token_from_request()
    if token:
        sessions.pop(token, None)
    
    response = make_response(jsonify({"ok": True}))
    response.delete_cookie("session_token")
    return response

@app.route("/api/auth/check", methods=["GET"])
@rate_limit
@auth_required
@audit_logged("auth_check")
def api_auth_check():
    token = get_token_from_request()
    username = validate_session(token)
    return jsonify({"authenticated": True, "username": username})

@app.route("/api/auth/session", methods=["GET"])
@rate_limit
@auth_required
def api_auth_session():
    token = get_token_from_request()
    session = sessions.get(token)
    if not session:
        return jsonify({"error": "No active session"}), 404
    
    now = time.time()
    remaining = 0
    if SESSION_TIMEOUT > 0:
        last_activity = session.get("last_activity", session["created"])
        remaining = max(0, SESSION_TIMEOUT - (now - last_activity))
    
    return jsonify({
        "timeout": SESSION_TIMEOUT,
        "max_age": SESSION_MAX_AGE,
        "remaining_seconds": int(remaining),
        "created": session.get("created"),
        "last_activity": session.get("last_activity"),
    })

@app.route("/api/auth/session", methods=["POST"])
@rate_limit
@auth_required
def api_auth_session_extend():
    token = get_token_from_request()
    session = sessions.get(token)
    if not session:
        return jsonify({"error": "No active session"}), 404
    
    session["last_activity"] = time.time()
    session["expires"] = time.time() + SESSION_MAX_AGE
    return jsonify({"ok": True, "message": "Session extended"})

@app.route("/api/auth/password", methods=["POST"])
@rate_limit
@auth_required
@audit_logged("auth_password_change")
def api_auth_change_password():
    if not AUTH_CREDENTIALS_ENABLED or AUTH_AUTH0_ENABLED:
        return jsonify({"error": "Password change not available"}), 400
    
    token = get_token_from_request()
    username = validate_session(token)
    
    if not username:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json(force=True, silent=True) or {}
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")
    
    if not current_password or not new_password:
        return jsonify({"error": "Current and new password required"}), 400
    
    if len(new_password) < 8:
        return jsonify({"error": "New password must be at least 8 characters"}), 400
    
    runtime_password = load_runtime_password()
    
    if current_password != runtime_password:
        return jsonify({"error": "Current password is incorrect"}), 401
    
    if save_runtime_password(new_password):
        log.info("Password changed for user %s", username)
        return jsonify({"ok": True, "message": "Password changed successfully"})
    
    return jsonify({"error": "Failed to save new password"}), 500

# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------
@app.route("/api/status")
@rate_limit
@auth_required
@audit_logged("api_status")
def api_status():
    next_digest = None
    if cfg["digest_interval"] > 0:
        elapsed = time.time() - state["last_digest_sent"]
        next_digest = max(0, int(cfg["digest_interval"] - elapsed))
    
    apprise_mode = "api" if APPRISE_API_URL else ("config_url" if APPRISE_CONFIG_URL else "embedded")
    apprise_configured = False
    if APPRISE_API_URL:
        apprise_configured = bool(_apprise_api_get_urls())
    else:
        apprise_configured = bool(_get_apprise_urls())
    
    return jsonify({
        "last_poll":          state["last_poll"],
        "poll_errors":        state["poll_errors"],
        "poll_interval":      POLL_INTERVAL,
        "crowdsec_url":       CROWDSEC_URL,
        "apprise_mode":       apprise_mode,
        "apprise_api_url":    APPRISE_API_URL,
        "apprise_config_url": APPRISE_CONFIG_URL,
        "apprise_configured": apprise_configured,
        "unsecure_mode":      UNSECURE,
        "total_bans":         len(state["decisions"]),
        "sent_count":         state["sent_count"],
        "suppressed_count":   state["suppressed_count"],
        "digest_pending":     len(state["digest_buffer"]),
        "next_digest_in":     next_digest,
        "cooldowns_tracked":  len(state["cooldowns"]),
    })

@app.route("/api/statistics")
@rate_limit
@auth_required
@audit_logged("api_statistics")
def api_statistics():
    decisions = state["decisions"]
    events = list(state["events"])
    
    decisions_by_type = {}
    for d in decisions:
        t = d.get("type", "unknown")
        decisions_by_type[t] = decisions_by_type.get(t, 0) + 1
    
    decisions_by_scenario = {}
    for d in decisions:
        s = d.get("scenario", "unknown")
        decisions_by_scenario[s] = decisions_by_scenario.get(s, 0) + 1
    
    decisions_by_origin = {}
    for d in decisions:
        o = d.get("origin", "unknown")
        decisions_by_origin[o] = decisions_by_origin.get(o, 0) + 1
    
    events_by_type = {}
    for e in events:
        t = e.get("type", "unknown")
        events_by_type[t] = events_by_type.get(t, 0) + 1
    
    return jsonify({
        "decisions": {
            "total": len(decisions),
            "by_type": decisions_by_type,
            "by_scenario": decisions_by_scenario,
            "by_origin": decisions_by_origin,
        },
        "events": {
            "total": len(events),
            "by_type": events_by_type,
        },
        "timeline": {
            "decisions": [
                {"time": d.get("created_at"), "type": d.get("type"), "ip": d.get("value")}
                for d in decisions[:50]
            ],
        }
    })

@app.route("/api/config", methods=["GET"])
@rate_limit
@auth_required
def api_config_get():
    return jsonify(cfg)

@app.route("/api/config", methods=["PATCH"])
@rate_limit
@auth_required
def api_config_patch():
    data = request.get_json(force=True, silent=True) or {}
    allowed = {"notify_on_ban", "notify_on_alert", "alert_threshold",
               "ban_threshold", "notify_cooldown", "digest_interval", "apprise_urls"}
    updated = {}
    for key, val in data.items():
        if key not in allowed:
            continue
        if key in ("alert_threshold", "ban_threshold", "notify_cooldown", "digest_interval"):
            val = int(val)
        elif key in ("notify_on_ban", "notify_on_alert"):
            val = bool(val)
        cfg[key] = val
        updated[key] = val
    log.info("Config updated: %s", updated)
    return jsonify({"ok": True, "updated": updated, "config": cfg})

@app.route("/api/decisions")
@rate_limit
@auth_required
@audit_logged("api_decisions")
def api_decisions():
    q = request.args.get("q", "").lower()
    data = state["decisions"]
    if q:
        data = [d for d in data if q in json.dumps(d).lower()]
    return jsonify(data)

@app.route("/api/alarms")
@rate_limit
@auth_required
@audit_logged("api_alarms")
def api_alarms():
    severity_filter = request.args.get("severity", "").lower()
    alarm_type_filter = request.args.get("type", "").lower()
    actionable_only = request.args.get("actionable", "true").lower() == "true"
    
    alarms = _check_all_actionable_alarms()
    
    if actionable_only:
        alarms = [a for a in alarms if a.get("severity", "").value != "info"]
    
    if severity_filter:
        alarms = [a for a in alarms if a.get("severity", "").value == severity_filter]
    if alarm_type_filter:
        alarms = [a for a in alarms if a.get("type", "") == alarm_type_filter]
    
    return jsonify({
        "alarms": alarms,
        "total": len(alarms),
        "critical_count": len([a for a in alarms if a.get("severity", "").value == "critical"]),
        "warning_count": len([a for a in alarms if a.get("severity", "").value == "warning"]),
        "info_count": len([a for a in alarms if a.get("severity", "").value == "info"]),
    })

@app.route("/api/alarms/<alarm_type>/dismiss", methods=["POST"])
@rate_limit
@auth_required
@audit_logged("api_alarms_dismiss")
def api_alarms_dismiss(alarm_type):
    if alarm_type == ActionableAlarmType.RATE_LIMIT_WARNING:
        state["rate_limit_warnings"] = []
    return jsonify({"ok": True})

@app.route("/api/alarms/failed-logins", methods=["POST"])
@rate_limit
@auth_required
@audit_logged("api_failed_login_track")
def api_track_failed_login():
    data = request.get_json(force=True, silent=True) or {}
    ip = data.get("ip", request.remote_addr)
    track_failed_login(ip)
    return jsonify({"ok": True})

@app.route("/api/whitelist", methods=["GET"])
@rate_limit
@auth_required
@audit_logged("api_whitelist_get")
def api_whitelist_get():
    whitelist = state.get("whitelist_expiry", {})
    return jsonify(whitelist)

@app.route("/api/whitelist", methods=["POST"])
@rate_limit
@auth_required
@audit_logged("api_whitelist_add")
def api_whitelist_add():
    data = request.get_json(force=True, silent=True) or {}
    ip = data.get("ip")
    expires = data.get("expires")
    reason = data.get("reason", "manual")
    
    if not ip:
        return jsonify({"error": "IP required"}), 400
    
    add_whitelist_entry(ip, expires, reason)
    return jsonify({"ok": True})

@app.route("/api/whitelist/<path:ip>", methods=["DELETE"])
@rate_limit
@auth_required
@audit_logged("api_whitelist_remove")
def api_whitelist_remove(ip):
    remove_whitelist_entry(ip)
    return jsonify({"ok": True})

@app.route("/api/events")
@rate_limit
@auth_required
@audit_logged("api_events")
def api_events():
    limit = int(request.args.get("limit", 60))
    ftype = request.args.get("type", "")
    data  = list(state["events"])
    if ftype:
        data = [e for e in data if e.get("type") == ftype]
    return jsonify(data[:limit])

@app.route("/api/metrics")
@rate_limit
@auth_required
@audit_logged("api_metrics")
def api_metrics():
    return jsonify(state["metrics"])

@app.route("/api/test-notify", methods=["POST"])
@rate_limit
@auth_required
@audit_logged("api_test_notify")
def api_test_notify():
    _send_now("CrowdSec Dashboard - Test", "Test notification working!\nThresholds configured correctly.")
    return jsonify({"ok": True})

@app.route("/api/apprise/status")
@rate_limit
@auth_required
@audit_logged("api_apprise_status")
def api_apprise_status():
    if APPRISE_API_URL:
        try:
            r = requests.get(
                f"{APPRISE_API_URL}/status",
                headers=_apprise_api_headers(),
                timeout=5,
            )
            return jsonify({
                "mode": "api",
                "api_url": APPRISE_API_URL,
                "api_reachable": r.status_code == 200,
                "config_key": APPRISE_CONFIG_KEY,
                "urls_count": len(_apprise_api_get_urls()),
                "apprise_configured": True,
            })
        except Exception as e:
            return jsonify({
                "mode": "api",
                "api_url": APPRISE_API_URL,
                "api_reachable": False,
                "error": str(e),
                "apprise_configured": False,
            })
    else:
        urls = _get_apprise_urls()
        return jsonify({
            "mode": "embedded",
            "urls_count": len(urls),
            "urls": urls[:3] if urls else [],
            "apprise_configured": len(urls) > 0,
        })

@app.route("/api/apprise/urls", methods=["GET"])
@rate_limit
@auth_required
@audit_logged("api_apprise_urls_get")
def api_apprise_urls_get():
    if APPRISE_API_URL:
        urls = _apprise_api_get_urls()
        return jsonify({"mode": "api", "urls": urls, "config_key": APPRISE_CONFIG_KEY})
    else:
        urls = _get_apprise_urls()
        return jsonify({"mode": "embedded", "urls": urls})

@app.route("/api/apprise/urls", methods=["POST"])
@rate_limit
@auth_required
@audit_logged("api_apprise_urls_set")
def api_apprise_urls_set():
    data = request.get_json(force=True, silent=True) or {}
    urls = data.get("urls", [])
    if isinstance(urls, str):
        urls = [u.strip() for u in urls.split(",") if u.strip()]
    
    if APPRISE_API_URL:
        ok = _apprise_api_set_urls(urls)
        if ok:
            log.info("Apprise API URLs set: %s", urls)
            return jsonify({"ok": True, "mode": "api", "urls": urls})
        return jsonify({"ok": False, "error": "Failed to set URLs in Apprise API"}), 500
    else:
        cfg["apprise_urls"] = ",".join(urls)
        log.info("Embedded Apprise URLs set: %s", urls)
        return jsonify({"ok": True, "mode": "embedded", "urls": urls})

@app.route("/api/system/config", methods=["GET"])
@rate_limit
@auth_required
@audit_logged("api_system_config")
def api_system_config():
    return jsonify({
        "connections": {
            "crowdsec": {
                "url": CROWDSEC_URL,
                "api_key_set": bool(CROWDSEC_API_KEY),
            },
            "apprise": {
                "mode": "api" if APPRISE_API_URL else "embedded",
                "api_url": APPRISE_API_URL,
                "config_key": APPRISE_CONFIG_KEY,
                "urls_count": len(_apprise_api_get_urls()) if APPRISE_API_URL else len(_get_apprise_urls()),
            },
        },
        "settings": {
            "unsecure_mode": UNSECURE,
            "poll_interval": POLL_INTERVAL,
        },
    })

@app.route("/api/system/test", methods=["POST"])
@rate_limit
@auth_required
@audit_logged("api_system_test")
def api_system_test():
    results = {
        "crowdsec": {"status": "unknown", "latency_ms": None, "error": None},
        "apprise": {"status": "unknown", "latency_ms": None, "error": None},
    }
    
    start = time.time()
    try:
        r = requests.get(f"{CROWDSEC_URL}/health", timeout=5)
        results["crowdsec"]["latency_ms"] = int((time.time() - start) * 1000)
        results["crowdsec"]["status"] = "connected" if r.status_code == 200 else "error"
    except Exception as e:
        results["crowdsec"]["status"] = "error"
        results["crowdsec"]["error"] = str(e)
    
    if APPRISE_API_URL:
        start = time.time()
        try:
            r = requests.get(f"{APPRISE_API_URL}/status", headers=_apprise_api_headers(), timeout=5)
            results["apprise"]["latency_ms"] = int((time.time() - start) * 1000)
            results["apprise"]["status"] = "connected" if r.status_code == 200 else "error"
        except Exception as e:
            results["apprise"]["status"] = "error"
            results["apprise"]["error"] = str(e)
    else:
        results["apprise"]["status"] = "embedded"
    
    return jsonify(results)

@app.route("/health")
@rate_limit
@audit_logged("health_check")
def health_check():
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})

@app.route("/api/unban", methods=["DELETE"])
@rate_limit
@auth_required
@audit_logged("api_unban")
def api_unban():
    decision_id = request.args.get("id")
    if not decision_id:
        return jsonify({"error": "id required"}), 400
    try:
        r = requests.delete(
            f"{CROWDSEC_URL}/v1/decisions/{decision_id}",
            headers=cs_headers(), timeout=10,
        )
        if r.status_code in (200, 204):
            state["events"].appendleft({
                "time": datetime.now(timezone.utc).isoformat(),
                "type": "unban",
                "msg": f"Manual UNBAN id={decision_id}",
                "data": {},
            })
        return jsonify({"status": r.status_code, "ok": r.status_code in (200, 204)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/cooldowns", methods=["GET"])
@rate_limit
@auth_required
@audit_logged("api_cooldowns_get")
def api_cooldowns():
    now = time.time()
    result = []
    for ip, ts in state["cooldowns"].items():
        remaining = int(cfg["notify_cooldown"] - (now - ts))
        if remaining > 0:
            result.append({"ip": ip, "remaining_seconds": remaining})
    return jsonify(result)

@app.route("/api/cooldowns", methods=["DELETE"])
@rate_limit
@auth_required
@audit_logged("api_cooldowns_clear")
def api_clear_cooldowns():
    ip = request.args.get("ip")
    if ip:
        state["cooldowns"].pop(ip, None)
    else:
        state["cooldowns"].clear()
    return jsonify({"ok": True})

@app.route("/callback")
@rate_limit
def callback():
    return send_from_directory("static", "index.html")

@app.route("/")
@rate_limit
def index():
    return send_from_directory("static", "index.html")

@app.route("/<path:filename>")
@rate_limit
def serve_static(filename):
    response = send_from_directory("static", filename)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == "__main__":
    if not CROWDSEC_API_KEY:
        log.warning("CROWDSEC_API_KEY not set - API calls will fail.")
    if AUTH_AUTH0_ENABLED:
        log.info("Authentication enabled: Auth0 (password login disabled)")
    elif AUTH_CREDENTIALS_ENABLED:
        log.info("Authentication enabled: credentials (password change available)")
    threading.Thread(target=digest_loop, daemon=True).start()
    threading.Thread(target=poll_loop, daemon=True).start()
    threading.Thread(target=_do_poll, daemon=True).start()
    threading.Thread(target=session_cleanup_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=False)
