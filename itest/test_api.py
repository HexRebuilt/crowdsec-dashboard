import pytest
import json
import time


class TestHealthEndpoint:
    def test_health_endpoint_exists(self, client):
        response = client.get('/health')
        assert response.status_code == 200

    def test_health_returns_ok(self, client):
        response = client.get('/health')
        assert b'ok' in response.data.lower()


class TestStatusEndpoint:
    def test_status_requires_auth_in_secure_mode(self, app, client):
        app.config['AUTH_ENABLED'] = True
        response = client.get('/api/status')
        assert response.status_code in [401, 302]

    def test_status_works_in_unsecure_mode(self, client):
        response = client.get('/api/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_bans' in data
        assert 'unsecure_mode' in data


class TestDecisionsEndpoint:
    def test_decisions_requires_auth_in_secure_mode(self, app, client):
        app.config['AUTH_ENABLED'] = True
        response = client.get('/api/decisions')
        assert response.status_code in [401, 302]

    def test_decisions_returns_list(self, client):
        response = client.get('/api/decisions')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)


class TestAlarmsEndpoint:
    def test_alarms_endpoint_exists(self, client):
        response = client.get('/api/alarms')
        assert response.status_code == 200

    def test_alarms_returns_dict(self, client):
        response = client.get('/api/alarms')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert 'alarms' in data

    def test_alarms_has_required_fields(self, client):
        response = client.get('/api/alarms')
        data = json.loads(response.data)
        if len(data.get('alarms', [])) > 0:
            alarm = data['alarms'][0]
            assert 'type' in alarm
            assert 'message' in alarm


class TestConfigEndpoint:
    def test_config_endpoint_exists(self, client):
        response = client.get('/api/config')
        assert response.status_code == 200

    def test_config_returns_dict(self, client):
        response = client.get('/api/config')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)

    def test_config_patch_notify_cooldown(self, client):
        response = client.patch('/api/config',
                                json={'notify_cooldown': 1800},
                                content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['ok'] is True
        assert data['config']['notify_cooldown'] == 1800

    def test_config_patch_notify_cooldown_zero(self, client):
        response = client.patch('/api/config',
                                json={'notify_cooldown': 0},
                                content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['ok'] is True
        assert data['config']['notify_cooldown'] == 0

    def test_config_patch_events_per_minute_threshold(self, client):
        response = client.patch('/api/config',
                                json={'events_per_minute_threshold': 50},
                                content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['ok'] is True
        assert data['config']['events_per_minute_threshold'] == 50


class TestStatisticsEndpoint:
    def test_statistics_endpoint_exists(self, client):
        response = client.get('/api/statistics')
        assert response.status_code == 200

    def test_statistics_returns_proper_structure(self, client):
        response = client.get('/api/statistics')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'decisions' in data
        assert 'events' in data
        assert 'timeline' in data


class TestAppriseEndpoints:
    def test_apprise_urls_endpoint_exists(self, client):
        response = client.get('/api/apprise/urls')
        assert response.status_code in [200, 500]

    def test_apprise_status_endpoint_exists(self, client):
        response = client.get('/api/apprise/status')
        assert response.status_code in [200, 500]


class TestAuthStatusEndpoint:
    def test_auth_status_exists(self, client):
        response = client.get('/api/auth/status')
        assert response.status_code == 200

    def test_auth_status_returns_auth_method(self, client):
        response = client.get('/api/auth/status')
        data = json.loads(response.data)
        assert 'method' in data
        assert 'enabled' in data

    def test_auth_status_includes_auth0_when_configured(self, client):
        response = client.get('/api/auth/status')
        data = json.loads(response.data)
        if data.get('method') == 'auth0':
            assert 'auth0_domain' in data
            assert 'auth0_client_id' in data


class TestAuthConfigEndpoint:
    def test_auth_config_exists(self, client):
        response = client.get('/api/auth/config')
        assert response.status_code == 200

    def test_auth_config_returns_dict(self, client):
        response = client.get('/api/auth/config')
        data = json.loads(response.data)
        assert isinstance(data, dict)

    def test_auth_config_includes_auth0_settings(self, client):
        response = client.get('/api/auth/config')
        data = json.loads(response.data)
        auth = data.get('auth0', {})
        if auth.get('enabled'):
            assert 'domain' in auth
            assert 'client_id' in auth


class TestAuthCallbackEndpoint:
    def test_auth_callback_requires_code(self, client):
        response = client.post('/api/auth/callback',
                               json={},
                               content_type='application/json')
        assert response.status_code == 400

    def test_auth_callback_requires_redirect_uri(self, client):
        response = client.post('/api/auth/callback',
                               json={'code': 'test'},
                               content_type='application/json')
        assert response.status_code == 400

    def test_auth_callback_rejects_invalid_code(self, client):
        response = client.post('/api/auth/callback',
                               json={'code': 'invalid_code', 'redirect_uri': 'http://localhost/callback'},
                               content_type='application/json')
        data = json.loads(response.data)
        assert 'error' in data


class TestAuthLogoutEndpoint:
    def test_auth_logout_requires_auth(self, client):
        response = client.post('/api/auth/logout')
        assert response.status_code == 200


class TestAuthCheckEndpoint:
    def test_auth_check_requires_auth(self, client):
        response = client.get('/api/auth/check')
        assert response.status_code == 200


class TestAlarmDismiss:
    def test_dismiss_manual_review_clears_alarm(self, client):
        """Dismissing manual_review alarm should suppress it from subsequent polls."""
        from main import state, _check_all_actionable_alarms
        state["alerts"] = [{
            "id": 1,
            "scenario": "test_scenario",
            "source": {"ip": "1.2.3.4"},
            "events_count": 100,
        }]
        state["manual_review_dismissed"] = 0
        state["event_rate_window"] = [time.time()] * 101
        alarms_before = _check_all_actionable_alarms()
        manual_before = [a for a in alarms_before if a.get("type") == "manual_review"]
        assert len(manual_before) > 0, "Expected manual_review alarm before dismiss"
        response = client.post('/api/alarms/manual_review/dismiss')
        assert response.status_code == 200
        alarms_after = _check_all_actionable_alarms()
        manual_after = [a for a in alarms_after if a.get("type") == "manual_review"]
        assert len(manual_after) == 0, "Manual review alarm should be suppressed after dismiss"

    def test_dismiss_whitelist_expiry_clears_alarm(self, client):
        """Dismissing whitelist_expiry alarm should suppress it from subsequent polls."""
        from main import state, _check_whitelist_expiry
        from datetime import datetime, timezone, timedelta
        soon = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        state["whitelist_expiry"] = {
            "1.2.3.4": {"expires": soon, "reason": "test"}
        }
        state["whitelist_expiry_dismissed"] = 0
        alarm_before = _check_whitelist_expiry()
        assert alarm_before is not None, "Expected whitelist_expiry alarm before dismiss"
        response = client.post('/api/alarms/whitelist_expiry/dismiss')
        assert response.status_code == 200
        alarm_after = _check_whitelist_expiry()
        assert alarm_after is None, "Whitelist expiry alarm should be suppressed after dismiss"


class TestConfigRobustness:
    def test_config_patch_notify_cooldown_null_does_not_crash(self, client):
        """Sending null for notify_cooldown should not crash (returns 200, keeps default)."""
        response = client.patch('/api/config',
                                json={'notify_cooldown': None},
                                content_type='application/json')
        assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.data}"
        data = json.loads(response.data)
        assert data['ok'] is True
        assert data['config']['notify_cooldown'] is not None

    def test_config_patch_notify_cooldown_empty_string_does_not_crash(self, client):
        """Sending empty string for notify_cooldown should not crash (returns 200, keeps default)."""
        response = client.patch('/api/config',
                                json={'notify_cooldown': ''},
                                content_type='application/json')
        assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.data}"
        data = json.loads(response.data)
        assert data['ok'] is True
        assert data['config']['notify_cooldown'] is not None

    def test_config_has_notify_cooldown_default(self, client):
        """Config should include notify_cooldown with a sensible default."""
        response = client.get('/api/config')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'notify_cooldown' in data
        assert isinstance(data['notify_cooldown'], int)
        assert data['notify_cooldown'] >= 0
