import pytest
import sys
import os
from app import create_app
from app.models import db

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))



@pytest.fixture(scope='function')
def app():
    # Create and configure a test application instance for each test
    _app = create_app('testing')
    _app.config['TESTING'] = True
    
    with _app.app_context():
        db.create_all()
        yield _app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    # Create a test client for the app
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    # Create a test CLI runner for the app
    return app.test_cli_runner()