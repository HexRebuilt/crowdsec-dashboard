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
        app.config['UNSECURE'] = False
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
        app.config['UNSECURE'] = False
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

    def test_alarms_returns_list(self, client):
        response = client.get('/api/alarms')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_alarms_has_required_fields(self, client):
        response = client.get('/api/alarms')
        data = json.loads(response.data)
        if len(data) > 0:
            alarm = data[0]
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
        assert 'snapshots' in data


class TestAppriseEndpoints:
    def test_apprise_urls_endpoint_exists(self, client):
        response = client.get('/api/apprise/urls')
        assert response.status_code in [200, 500]

    def test_apprise_status_endpoint_exists(self, client):
        response = client.get('/api/apprise/status')
        assert response.status_code in [200, 500]
