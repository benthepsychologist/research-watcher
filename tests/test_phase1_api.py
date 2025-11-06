"""
Phase 1 API Integration Tests

Tests the API skeleton endpoints deployed to Cloud Run.
These tests verify routing, authentication, and basic responses.
"""

import os
import pytest
import requests

# Test configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "research-watcher")
CLOUD_RUN_URL = "https://rw-api-491582996945.us-central1.run.app"


@pytest.mark.integration
class TestAPIHealth:
    """Test API health and availability"""

    def test_health_endpoint(self):
        """Health check should return 200 OK"""
        response = requests.get(f"{CLOUD_RUN_URL}/", timeout=10)
        assert response.status_code == 200

        data = response.json()
        assert data['status'] == 'healthy'
        assert data['service'] == 'research-watcher-api'
        assert 'version' in data


@pytest.mark.integration
class TestAuthentication:
    """Test authentication requirements"""

    def test_users_sync_requires_auth(self):
        """Users sync should return 401 without auth"""
        response = requests.post(f"{CLOUD_RUN_URL}/api/users/sync", timeout=10)
        assert response.status_code == 401

        data = response.json()
        assert data['error'] == 'unauthorized'
        assert 'Authorization' in data['message']

    def test_seeds_get_requires_auth(self):
        """Seeds GET should return 401 without auth"""
        response = requests.get(f"{CLOUD_RUN_URL}/api/seeds", timeout=10)
        assert response.status_code == 401

    def test_seeds_post_requires_auth(self):
        """Seeds POST should return 401 without auth"""
        response = requests.post(f"{CLOUD_RUN_URL}/api/seeds", json={'seeds': []}, timeout=10)
        assert response.status_code == 401

    def test_digest_requires_auth(self):
        """Digest endpoint should return 401 without auth"""
        response = requests.get(f"{CLOUD_RUN_URL}/api/digest/latest", timeout=10)
        assert response.status_code == 401

    def test_feedback_requires_auth(self):
        """Feedback endpoint should return 401 without auth"""
        response = requests.post(
            f"{CLOUD_RUN_URL}/api/feedback",
            json={'paperId': 'test', 'action': 'thumbs_up'},
            timeout=10
        )
        assert response.status_code == 401

    def test_invalid_token_format(self):
        """Invalid auth header format should return 401"""
        headers = {'Authorization': 'InvalidFormat'}
        response = requests.post(
            f"{CLOUD_RUN_URL}/api/users/sync",
            headers=headers,
            timeout=10
        )
        assert response.status_code == 401

        data = response.json()
        assert 'Bearer' in data['message']


@pytest.mark.integration
class TestCollectorEndpoints:
    """Test collector stub endpoints"""

    def test_collector_run_accessible(self):
        """Collector run endpoint should be accessible (OIDC check in Cloud Run)"""
        response = requests.post(f"{CLOUD_RUN_URL}/api/collect/run", timeout=10)
        assert response.status_code == 200

        data = response.json()
        assert data['status'] == 'stub'
        assert data['phase'] == 1

    def test_collector_queue_not_implemented(self):
        """Collector queue should return 501"""
        response = requests.post(f"{CLOUD_RUN_URL}/api/collect/queue", timeout=10)
        assert response.status_code == 501

        data = response.json()
        assert data['status'] == 'not_implemented'

    def test_collector_worker_not_implemented(self):
        """Collector worker should return 501"""
        response = requests.post(f"{CLOUD_RUN_URL}/api/collect/worker", timeout=10)
        assert response.status_code == 501

        data = response.json()
        assert data['status'] == 'not_implemented'


@pytest.mark.unit
class TestAPIStructure:
    """Test API structure and configuration"""

    def test_app_factory_exists(self):
        """App factory function should exist"""
        from app import create_app
        assert callable(create_app)

    def test_blueprints_registered(self):
        """All required blueprints should be registered"""
        from app import create_app
        app = create_app()

        # Check blueprint names
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        assert 'users' in blueprint_names
        assert 'seeds' in blueprint_names
        assert 'digest' in blueprint_names
        assert 'collector' in blueprint_names
        assert 'feedback' in blueprint_names

    def test_auth_decorator_exists(self):
        """Auth decorators should be importable"""
        from app.utils.auth import login_required, scheduler_auth_required
        assert callable(login_required)
        assert callable(scheduler_auth_required)
