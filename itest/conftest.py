import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def app():
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['UNSECURE'] = 'true'
    os.environ['CROWDSEC_URL'] = 'http://localhost:8080'
    os.environ['CROWDSEC_API_KEY'] = 'test_api_key'
    os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    
    from main import app as flask_app
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['AUTH_ENABLED'] = False  # Default to unsecure for tests
    
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
