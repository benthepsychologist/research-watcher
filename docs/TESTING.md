# Research Watcher - Testing Guide

## Overview

Research Watcher uses a multi-layered testing approach:
- **Bash integration tests** - Quick infrastructure validation (Phase 0)
- **Pytest suite** - Comprehensive unit and integration tests (Phase 1+)
- **Manual testing** - UI and end-to-end workflows (Phase 3+)

---

## Phase 0 Testing (Infrastructure)

### Quick Test - Bash Script

The fastest way to validate Phase 0 infrastructure:

```bash
./scripts/test_phase0_infrastructure.sh
```

**Tests 36 components:**
- ✅ Cloud Run service (3 tests)
- ✅ Firestore database (3 tests)
- ✅ Pub/Sub infrastructure (4 tests)
- ✅ BigQuery infrastructure (4 tests)
- ✅ Service accounts & IAM (5 tests)
- ✅ Cloud Scheduler (5 tests)
- ✅ Local configuration (12 tests)

**Expected output:**
```
✅ ALL TESTS PASSED
Passed: 36
Failed: 0
Total:  36
```

### Pytest Integration Tests

More comprehensive Python-based tests:

```bash
# Install dependencies (requires virtual environment)
pip install -r requirements.txt

# Run Phase 0 integration tests
pytest tests/test_phase0_infrastructure.py -m integration -v

# Run only unit tests (local files)
pytest tests/test_phase0_infrastructure.py -m unit -v
```

**Test coverage:**
- 33 integration tests (require GCP)
- 6 unit tests (local only)

---

## Test Requirements

### For Bash Tests
- `gcloud` CLI authenticated
- `bq` CLI available
- `curl` installed
- Project `research-watcher` set as active

### For Pytest Tests
- Python 3.11+
- Virtual environment with dependencies
- `gcloud` CLI authenticated
- `requests` library installed

---

## Running Tests in Different Environments

### Local Development

```bash
# Set project
gcloud config set project research-watcher

# Run bash tests
./scripts/test_phase0_infrastructure.sh

# Run pytest (if venv available)
pytest -m integration
```

### CI/CD Pipeline

```yaml
# Example GitHub Actions
- name: Test Infrastructure
  run: |
    gcloud auth activate-service-account --key-file=${{ secrets.GCP_KEY }}
    gcloud config set project research-watcher
    ./scripts/test_phase0_infrastructure.sh
```

### Cloud Workstation

```bash
# Authenticate
gcloud auth login

# Run tests
./scripts/test_phase0_infrastructure.sh
```

---

## Test Markers (Pytest)

Use markers to run specific test categories:

```bash
# Unit tests only (fast, no GCP)
pytest -m unit

# Integration tests only (requires GCP)
pytest -m integration

# Slow tests only (>10s)
pytest -m slow

# All tests
pytest
```

---

## Troubleshooting

### Authentication Errors

```bash
# Check authentication
gcloud auth list

# Re-authenticate
gcloud auth login

# Verify project
gcloud config get-value project
```

### Permission Errors

```bash
# Verify your roles
gcloud projects get-iam-policy research-watcher \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:YOUR_EMAIL"

# You need at least Viewer role for testing
```

### Test Failures

1. **Cloud Run not responding**
   - Check service is deployed: `gcloud run services list`
   - Check logs: `gcloud run services logs rw-api --region=us-central1`

2. **Firestore tests fail**
   - Verify database exists: `gcloud firestore databases list`
   - Check location matches: should be `us-central1`

3. **Pub/Sub tests fail**
   - Verify topic exists: `gcloud pubsub topics list`
   - Check subscription: `gcloud pubsub subscriptions list`

4. **BigQuery tests fail**
   - Verify dataset: `bq ls`
   - Check table: `bq show research_wal.events`

5. **Service account tests fail**
   - List service accounts: `gcloud iam service-accounts list`
   - Check IAM policy: `gcloud projects get-iam-policy research-watcher`

---

## Test Development

### Adding New Tests

1. **Bash tests** - Edit `scripts/test_phase0_infrastructure.sh`
   ```bash
   test_new_feature() {
       section "TEST: New Feature"
       if some_command; then
           pass "Feature works"
       else
           fail "Feature broken"
       fi
   }
   ```

2. **Pytest tests** - Add to appropriate test file
   ```python
   @pytest.mark.integration
   def test_new_feature():
       """Test description"""
       result = call_api()
       assert result.status_code == 200
   ```

### Test Guidelines

1. **Independence** - Tests should not depend on each other
2. **Idempotency** - Tests should be repeatable
3. **Clean up** - Remove test data after tests
4. **Fast** - Keep unit tests under 1s each
5. **Clear** - Use descriptive names and assertions

---

## Phase-Specific Testing

### Phase 0 ✅ Complete
- Infrastructure validation
- Configuration verification
- Service account permissions
- **Status**: 36/36 bash tests passing, 33 pytest tests written

### Phase 1 🔄 In Progress
- API endpoint tests
- Authentication tests
- Blueprint routing tests
- **TODO**: Set up virtual environment for pytest

### Phase 2 ⏳ Planned
- Collector logic tests
- External API mocking
- Scoring algorithm tests
- Dual-write verification

### Phase 3 ⏳ Planned
- Frontend UI tests
- E2E user flows
- Firebase Auth integration
- Hosting deployment tests

---

## Continuous Testing Strategy

### Pre-Commit
```bash
# Run fast unit tests
pytest -m unit
```

### Pre-Deploy
```bash
# Run all integration tests
./scripts/test_phase0_infrastructure.sh
pytest -m integration
```

### Daily/Scheduled
```bash
# Full test suite to catch drift
pytest
./scripts/test_phase0_infrastructure.sh
```

---

## Test Metrics

### Current Coverage (Phase 0)
- Infrastructure: **100%** (all components tested)
- Configuration: **100%** (all files verified)
- Service accounts: **100%** (all roles checked)
- Overall: **36/36 tests passing**

### Target Coverage (v1.0)
- Unit tests: > 80%
- Integration tests: > 60%
- E2E tests: Critical paths covered

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [gcloud CLI Reference](https://cloud.google.com/sdk/gcloud/reference)
- [BigQuery CLI (bq)](https://cloud.google.com/bigquery/docs/bq-command-line-tool)
- [Test README](../tests/README.md)

---

**Last Updated**: 2025-11-06
**Phase**: 0.5 (Testing infrastructure added)
