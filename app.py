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
from datetime import datetime, timedelta, timezone
from collections import deque
from functools import wraps

import requests
import apprise
from flask import Flask, jsonify, request, send_from_directory, make_response
from flask_cors import CORS

# ---------------------------------------------------------------------------
# Boot-time config (from env)
# ---------------------------------------------------------------------------
CROWDSEC_URL       = os.getenv("CROWDSEC_URL", "http://crowdsec:8080")
CROWDSEC_API_KEY   = os.getenv("CROWDSEC_API_KEY", "")
APPRISE_URLS       = os.getenv("APPRISE_URLS", "")
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

AUTH_CREDENTIALS_ENABLED = bool(AUTH_USERNAME and AUTH_PASSWORD)
AUTH_AUTH0_ENABLED = bool(AUTH0_DOMAIN and AUTH0_CLIENT_ID)
AUTH_ENABLED = AUTH_CREDENTIALS_ENABLED or AUTH_AUTH0_ENABLED

AUTH_PASSWORD_FILE = "/app/.auth_password"

def load_runtime_password():
    if os.path.exists(AUTH_PASSWORD_FILE):
        try:
            with open(AUTH_PASSWORD_FILE, "r") as f:
                return f.read().strip()
        except:
            pass
    return AUTH_PASSWORD

def save_runtime_password(password):
    try:
        with open(AUTH_PASSWORD_FILE, "w") as f:
            f.write(password)
        os.chmod(AUTH_PASSWORD_FILE, 0o600)
        return True
    except Exception as e:
        log.error("Failed to save password: %s", e)
        return False

CURRENT_PASSWORD = load_runtime_password()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static")
CORS(app, supports_credentials=True)

# Session storage (simple in-memory, use Redis for production)
sessions = {}

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_session(username):
    token = secrets.token_urlsafe(32)
    sessions[token] = {
        "username": username,
        "created": time.time(),
        "expires": time.time() + 86400
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
    return session["username"]

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
    "alert_threshold":    int(os.getenv("ALERT_THRESHOLD", "5")),
    "ban_threshold":      int(os.getenv("BAN_THRESHOLD", "0")),
    "notify_cooldown":    int(os.getenv("NOTIFY_COOLDOWN", "3600")),
    "digest_interval":    int(os.getenv("DIGEST_INTERVAL", "0")),
    "apprise_urls":       os.getenv("APPRISE_URLS", ""),
}

# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------
state = {
    "decisions":           [],
    "alerts":              [],
    "metrics":             {},
    "last_poll":           None,
    "poll_errors":         0,
    "known_decision_ids":  set(),
    "known_alert_ids":     set(),
    "events":              deque(maxlen=500),
    "cooldowns":           {},
    "suppressed_count":    0,
    "sent_count":          0,
    "digest_buffer":       [],
    "last_digest_sent":    time.time(),
}

# ---------------------------------------------------------------------------
# Notification logic
# ---------------------------------------------------------------------------

def _get_apprise_urls():
    if APPRISE_API_URL:
        return []
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
def cs_headers():
    return {"X-Api-Key": CROWDSEC_API_KEY, "Accept": "application/json"}

def fetch_decisions():
    try:
        r = requests.get(f"{CROWDSEC_URL}/v1/decisions", headers=cs_headers(), timeout=10)
        if r.status_code == 200:
            return r.json() or []
        log.warning("GET /v1/decisions -> %s", r.status_code)
    except Exception as e:
        log.error("fetch_decisions: %s", e)
    return None

def fetch_alerts(since_minutes=120):
    try:
        since = (datetime.now(timezone.utc) - timedelta(minutes=since_minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")
        r = requests.get(
            f"{CROWDSEC_URL}/v1/alerts",
            headers=cs_headers(),
            params={"since": since},
            timeout=10,
        )
        if r.status_code == 200:
            return r.json() or []
        log.warning("GET /v1/alerts -> %s", r.status_code)
    except Exception as e:
        log.error("fetch_alerts: %s", e)
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
def api_auth_status():
    return jsonify({
        "enabled": AUTH_ENABLED,
        "method": "auth0" if AUTH_AUTH0_ENABLED else "credentials" if AUTH_CREDENTIALS_ENABLED else None,
        "auth0_domain": AUTH0_DOMAIN if AUTH0_DOMAIN else None,
        "auth0_client_id": AUTH0_CLIENT_ID if AUTH0_CLIENT_ID else None,
        "password_change_available": AUTH_CREDENTIALS_ENABLED and not AUTH_AUTH0_ENABLED,
    })

@app.route("/api/auth/config")
@auth_required
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
def api_auth_login():
    data = request.get_json(force=True, silent=True) or {}
    
    # Auth0 login
    if AUTH0_DOMAIN and AUTH0_CLIENT_ID:
        access_token = data.get("access_token")
        if not access_token:
            return jsonify({"error": "Access token required"}), 400
        
        try:
            userinfo = requests.get(
                f"https://{AUTH0_DOMAIN}/userinfo",
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
    
    # Credentials login
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

@app.route("/api/auth/logout", methods=["POST"])
def api_auth_logout():
    token = get_token_from_request()
    if token:
        sessions.pop(token, None)
    
    response = make_response(jsonify({"ok": True}))
    response.delete_cookie("session_token")
    return response

@app.route("/api/auth/check", methods=["GET"])
@auth_required
def api_auth_check():
    token = get_token_from_request()
    username = validate_session(token)
    return jsonify({"authenticated": True, "username": username})

@app.route("/api/auth/password", methods=["POST"])
@auth_required
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
@auth_required
def api_status():
    next_digest = None
    if cfg["digest_interval"] > 0:
        elapsed = time.time() - state["last_digest_sent"]
        next_digest = max(0, int(cfg["digest_interval"] - elapsed))
    
    apprise_mode = "api" if APPRISE_API_URL else "embedded"
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
        "apprise_configured": apprise_configured,
        "unsecure_mode":      UNSECURE,
        "total_bans":         len(state["decisions"]),
        "total_alerts":       len(state["alerts"]),
        "sent_count":         state["sent_count"],
        "suppressed_count":   state["suppressed_count"],
        "digest_pending":     len(state["digest_buffer"]),
        "next_digest_in":     next_digest,
        "cooldowns_tracked":  len(state["cooldowns"]),
    })

@app.route("/api/statistics")
@auth_required
def api_statistics():
    period = request.args.get("period", "all")
    
    now = datetime.now(timezone.utc)
    if period == "day":
        cutoff = now - timedelta(days=1)
    elif period == "week":
        cutoff = now - timedelta(weeks=1)
    elif period == "month":
        cutoff = now - timedelta(days=30)
    else:
        cutoff = None
    
    decisions = state["decisions"]
    alerts = state["alerts"]
    events = list(state["events"])
    
    def filter_by_time(items, time_field="created_at"):
        if cutoff is None:
            return items
        filtered = []
        for item in items:
            ts = item.get(time_field) or item.get("start_at") or item.get("time")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if dt >= cutoff:
                        filtered.append(item)
                except:
                    filtered.append(item)
        return filtered
    
    filtered_decisions = filter_by_time(decisions, "created_at")
    filtered_alerts = filter_by_time(alerts, "start_at")
    filtered_events = filter_by_time(events, "time")
    
    decisions_by_type = {}
    for d in filtered_decisions:
        t = d.get("type", "unknown")
        decisions_by_type[t] = decisions_by_type.get(t, 0) + 1
    
    decisions_by_scenario = {}
    for d in filtered_decisions:
        s = d.get("scenario", "unknown")
        decisions_by_scenario[s] = decisions_by_scenario.get(s, 0) + 1
    
    decisions_by_origin = {}
    for d in filtered_decisions:
        o = d.get("origin", "unknown")
        decisions_by_origin[o] = decisions_by_origin.get(o, 0) + 1
    
    alerts_by_scenario = {}
    for a in filtered_alerts:
        s = a.get("scenario", "unknown")
        alerts_by_scenario[s] = alerts_by_scenario.get(s, 0) + 1
    
    events_by_type = {}
    for e in filtered_events:
        t = e.get("type", "unknown")
        events_by_type[t] = events_by_type.get(t, 0) + 1
    
    return jsonify({
        "period": period,
        "decisions": {
            "total": len(filtered_decisions),
            "by_type": decisions_by_type,
            "by_scenario": decisions_by_scenario,
            "by_origin": decisions_by_origin,
        },
        "alerts": {
            "total": len(filtered_alerts),
            "by_scenario": alerts_by_scenario,
        },
        "events": {
            "total": len(filtered_events),
            "by_type": events_by_type,
        },
        "timeline": {
            "decisions": [
                {"time": d.get("created_at"), "type": d.get("type"), "ip": d.get("value")}
                for d in filtered_decisions[:50]
            ],
            "alerts": [
                {"time": a.get("start_at"), "scenario": a.get("scenario"), "ip": (a.get("source") or {}).get("ip")}
                for a in filtered_alerts[:50]
            ],
        }
    })

@app.route("/api/config", methods=["GET"])
@auth_required
def api_config_get():
    return jsonify(cfg)

@app.route("/api/config", methods=["PATCH"])
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
@auth_required
def api_decisions():
    q = request.args.get("q", "").lower()
    data = state["decisions"]
    if q:
        data = [d for d in data if q in json.dumps(d).lower()]
    return jsonify(data)

@app.route("/api/alerts")
@auth_required
def api_alerts():
    q = request.args.get("q", "").lower()
    data = state["alerts"]
    if q:
        data = [a for a in data if q in json.dumps(a).lower()]
    return jsonify(data)

@app.route("/api/events")
@auth_required
def api_events():
    limit = int(request.args.get("limit", 60))
    ftype = request.args.get("type", "")
    data  = list(state["events"])
    if ftype:
        data = [e for e in data if e.get("type") == ftype]
    return jsonify(data[:limit])

@app.route("/api/metrics")
@auth_required
def api_metrics():
    return jsonify(state["metrics"])

@app.route("/api/test-notify", methods=["POST"])
@auth_required
def api_test_notify():
    _send_now("CrowdSec Dashboard - Test", "Test notification working!\nThresholds configured correctly.")
    return jsonify({"ok": True})

@app.route("/api/apprise/status")
@auth_required
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
            })
        except Exception as e:
            return jsonify({
                "mode": "api",
                "api_url": APPRISE_API_URL,
                "api_reachable": False,
                "error": str(e),
            })
    else:
        urls = _get_apprise_urls()
        return jsonify({
            "mode": "embedded",
            "urls_count": len(urls),
            "urls": urls[:3] if urls else [],
        })

@app.route("/api/apprise/urls", methods=["GET"])
@auth_required
def api_apprise_urls_get():
    if APPRISE_API_URL:
        urls = _apprise_api_get_urls()
        return jsonify({"mode": "api", "urls": urls, "config_key": APPRISE_CONFIG_KEY})
    else:
        urls = _get_apprise_urls()
        return jsonify({"mode": "embedded", "urls": urls})

@app.route("/api/apprise/urls", methods=["POST"])
@auth_required
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
@auth_required
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
@auth_required
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
def health_check():
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()})

@app.route("/api/unban", methods=["DELETE"])
@auth_required
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
@auth_required
def api_cooldowns():
    now = time.time()
    result = []
    for ip, ts in state["cooldowns"].items():
        remaining = int(cfg["notify_cooldown"] - (now - ts))
        if remaining > 0:
            result.append({"ip": ip, "remaining_seconds": remaining})
    return jsonify(result)

@app.route("/api/cooldowns", methods=["DELETE"])
@auth_required
def api_clear_cooldowns():
    ip = request.args.get("ip")
    if ip:
        state["cooldowns"].pop(ip, None)
    else:
        state["cooldowns"].clear()
    return jsonify({"ok": True})

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)

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
    app.run(host="0.0.0.0", port=5000, debug=False)
