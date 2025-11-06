# Research Watcher Tests

## Test Structure

- `test_phase0_infrastructure.py` - Integration tests for Phase 0 GCP/Firebase infrastructure
- Future: `test_phase1_api.py`, `test_phase2_collector.py`, etc.

## Running Tests

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

### Run Specific Test Suites

```bash
# Run only unit tests (fast, no external dependencies)
pytest -m unit

# Run only integration tests (requires GCP infrastructure)
pytest -m integration

# Run specific test file
pytest tests/test_phase0_infrastructure.py

# Run specific test class
pytest tests/test_phase0_infrastructure.py::TestCloudRun

# Run specific test
pytest tests/test_phase0_infrastructure.py::TestCloudRun::test_service_exists
```

### Bash Test Script

For quick infrastructure validation without pytest:

```bash
# Run comprehensive bash-based tests
./scripts/test_phase0_infrastructure.sh
```

This script tests:
- Cloud Run service
- Firestore database
- Pub/Sub topic and subscription
- BigQuery dataset and table
- Service accounts and IAM
- Cloud Scheduler job
- Local configuration files

## Test Markers

- `@pytest.mark.unit` - Fast unit tests, no external dependencies
- `@pytest.mark.integration` - Integration tests requiring GCP resources
- `@pytest.mark.slow` - Tests that take >10s to complete

## Writing Tests

### Unit Tests
- Should be fast (< 1s each)
- No external dependencies (mock everything)
- Test individual functions/classes

### Integration Tests
- Test actual GCP/Firebase infrastructure
- Require deployed resources
- Run less frequently (CI/CD, before deployment)

### Example

```python
import pytest

@pytest.mark.unit
def test_something_fast():
    assert 1 + 1 == 2

@pytest.mark.integration
def test_gcp_resource():
    # Test actual GCP resource
    pass
```

## Continuous Integration

Integration tests should run:
- Before deploying to production
- After infrastructure changes
- Daily (to catch configuration drift)

Unit tests should run:
- On every commit
- On every pull request

## Test Reports

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Generate terminal coverage report
pytest --cov=app --cov-report=term-missing
```

## Troubleshooting

### Authentication Issues

```bash
# Verify gcloud authentication
gcloud auth list

# Verify project is set
gcloud config get-value project

# Re-authenticate if needed
gcloud auth login
```

### Permission Issues

```bash
# Check service account permissions
gcloud projects get-iam-policy research-watcher

# Verify you have necessary roles
gcloud projects get-iam-policy research-watcher \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:YOUR_EMAIL"
```

### Timeout Issues

If tests timeout:
- Check your internet connection
- Verify GCP services are healthy
- Increase timeout in pytest.ini

## Phase-Specific Tests

### Phase 0 (Bootstrap & Environment)
✅ Complete - 36 bash tests, 33 pytest tests

Validates:
- GCP infrastructure deployment
- Firebase configuration
- Service accounts and IAM
- Local development setup

### Phase 1 (Backend Core)
Coming soon - API endpoint tests

### Phase 2 (Collector + Dual-Write)
Coming soon - Collector logic tests

### Phase 3 (Frontend)
Coming soon - Frontend UI tests
