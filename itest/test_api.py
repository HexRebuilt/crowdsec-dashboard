import pytest
import json


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
