"""
Phase 0 Infrastructure Integration Tests

Tests all deployed GCP/Firebase infrastructure components.
These are integration tests that require actual GCP resources to be deployed.

Run with: pytest tests/test_phase0_infrastructure.py -m integration
"""

import os
import subprocess
import pytest
import requests
from pathlib import Path

# Test configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "research-watcher")
REGION = "us-central1"
CLOUD_RUN_URL = "https://rw-api-491582996945.us-central1.run.app"


def gcloud_command(cmd: list) -> tuple[bool, str]:
    """Execute gcloud command and return success status and output"""
    try:
        result = subprocess.run(
            ["gcloud"] + cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)


@pytest.mark.integration
class TestCloudRun:
    """Test Cloud Run service deployment"""

    def test_service_exists(self):
        """Cloud Run service should exist"""
        success, _ = gcloud_command([
            "run", "services", "describe", "rw-api",
            "--region", REGION,
            "--format", "value(name)"
        ])
        assert success, "Cloud Run service 'rw-api' should exist"

    def test_service_responds(self):
        """Cloud Run service should respond to HTTP requests"""
        response = requests.get(CLOUD_RUN_URL, timeout=10)
        assert response.status_code == 200, "Service should return 200 OK"

    def test_service_content(self):
        """Cloud Run service should return expected content"""
        response = requests.get(CLOUD_RUN_URL, timeout=10)
        assert "Hello" in response.text, "Service should return greeting"


@pytest.mark.integration
class TestFirestore:
    """Test Firestore database configuration"""

    def test_database_exists(self):
        """Firestore database should exist"""
        success, _ = gcloud_command([
            "firestore", "databases", "describe",
            "--database", "(default)",
            "--format", "value(name)"
        ])
        assert success, "Firestore database should exist"

    def test_database_type(self):
        """Firestore should be in Native mode"""
        success, output = gcloud_command([
            "firestore", "databases", "describe",
            "--database", "(default)",
            "--format", "value(type)"
        ])
        assert success and output == "FIRESTORE_NATIVE", \
            "Database should be FIRESTORE_NATIVE"

    def test_database_location(self):
        """Firestore should be in us-central1"""
        success, output = gcloud_command([
            "firestore", "databases", "describe",
            "--database", "(default)",
            "--format", "value(locationId)"
        ])
        assert success and output == "us-central1", \
            "Database location should be us-central1"


@pytest.mark.integration
class TestPubSub:
    """Test Pub/Sub infrastructure"""

    def test_topic_exists(self):
        """Pub/Sub topic rw-wal should exist"""
        success, _ = gcloud_command([
            "pubsub", "topics", "describe", "rw-wal",
            "--format", "value(name)"
        ])
        assert success, "Topic 'rw-wal' should exist"

    def test_subscription_exists(self):
        """Pub/Sub subscription rw-wal-to-bq should exist"""
        success, _ = gcloud_command([
            "pubsub", "subscriptions", "describe", "rw-wal-to-bq",
            "--format", "value(name)"
        ])
        assert success, "Subscription 'rw-wal-to-bq' should exist"

    def test_subscription_bigquery_config(self):
        """Subscription should be connected to BigQuery"""
        success, output = gcloud_command([
            "pubsub", "subscriptions", "describe", "rw-wal-to-bq",
            "--format", "value(bigqueryConfig.table)"
        ])
        expected = f"{PROJECT_ID}:research_wal.events"
        assert success and output == expected, \
            f"Subscription should write to {expected}"

    def test_can_publish_message(self):
        """Should be able to publish messages to topic"""
        success, output = gcloud_command([
            "pubsub", "topics", "publish", "rw-wal",
            "--message", '{"test":"pytest"}',
            "--format", "value(messageIds[0])"
        ])
        assert success and output, "Should be able to publish message"


@pytest.mark.integration
class TestBigQuery:
    """Test BigQuery infrastructure"""

    def test_dataset_exists(self):
        """BigQuery dataset research_wal should exist"""
        cmd = [
            "bq", "show",
            f"{PROJECT_ID}:research_wal"
        ]
        success, _ = gcloud_command(cmd)
        assert success, "Dataset 'research_wal' should exist"

    def test_events_table_exists(self):
        """BigQuery events table should exist"""
        cmd = [
            "bq", "show",
            f"{PROJECT_ID}:research_wal.events"
        ]
        success, _ = gcloud_command(cmd)
        assert success, "Table 'research_wal.events' should exist"

    def test_table_has_data_field(self):
        """Events table should have data field"""
        cmd = [
            "bq", "show", "--format=prettyjson",
            f"{PROJECT_ID}:research_wal.events"
        ]
        success, output = gcloud_command(cmd)
        assert success and '"name": "data"' in output, \
            "Table should have 'data' field"

    def test_table_partitioning(self):
        """Events table should be partitioned by publish_time"""
        cmd = [
            "bq", "show", "--format=prettyjson",
            f"{PROJECT_ID}:research_wal.events"
        ]
        success, output = gcloud_command(cmd)
        assert success and '"field": "publish_time"' in output, \
            "Table should be partitioned by 'publish_time'"


@pytest.mark.integration
class TestServiceAccounts:
    """Test service accounts and IAM"""

    def test_api_service_account_exists(self):
        """rw-api service account should exist"""
        success, _ = gcloud_command([
            "iam", "service-accounts", "describe",
            f"rw-api@{PROJECT_ID}.iam.gserviceaccount.com",
            "--format", "value(email)"
        ])
        assert success, "Service account 'rw-api' should exist"

    def test_scheduler_service_account_exists(self):
        """scheduler-invoker service account should exist"""
        success, _ = gcloud_command([
            "iam", "service-accounts", "describe",
            f"scheduler-invoker@{PROJECT_ID}.iam.gserviceaccount.com",
            "--format", "value(email)"
        ])
        assert success, "Service account 'scheduler-invoker' should exist"

    def test_api_has_datastore_role(self):
        """rw-api should have datastore.user role"""
        success, output = gcloud_command([
            "projects", "get-iam-policy", PROJECT_ID,
            "--flatten", "bindings[].members",
            "--filter", f"bindings.members:serviceAccount:rw-api@{PROJECT_ID}.iam.gserviceaccount.com",
            "--format", "value(bindings.role)"
        ])
        assert success and "roles/datastore.user" in output, \
            "Service account should have datastore.user role"

    def test_api_has_pubsub_role(self):
        """rw-api should have pubsub.publisher role"""
        success, output = gcloud_command([
            "projects", "get-iam-policy", PROJECT_ID,
            "--flatten", "bindings[].members",
            "--filter", f"bindings.members:serviceAccount:rw-api@{PROJECT_ID}.iam.gserviceaccount.com",
            "--format", "value(bindings.role)"
        ])
        assert success and "roles/pubsub.publisher" in output, \
            "Service account should have pubsub.publisher role"

    def test_scheduler_can_invoke_cloud_run(self):
        """scheduler-invoker should be able to invoke Cloud Run"""
        success, output = gcloud_command([
            "run", "services", "get-iam-policy", "rw-api",
            "--region", REGION,
            "--filter", f"bindings.members:serviceAccount:scheduler-invoker@{PROJECT_ID}.iam.gserviceaccount.com",
            "--format", "value(bindings.role)"
        ])
        assert success and "run.invoker" in output, \
            "Scheduler should have run.invoker permission"


@pytest.mark.integration
class TestCloudScheduler:
    """Test Cloud Scheduler configuration"""

    def test_job_exists(self):
        """Scheduler job collect-daily should exist"""
        success, _ = gcloud_command([
            "scheduler", "jobs", "describe", "collect-daily",
            "--location", REGION,
            "--format", "value(name)"
        ])
        assert success, "Scheduler job 'collect-daily' should exist"

    def test_schedule(self):
        """Job should have correct cron schedule"""
        success, output = gcloud_command([
            "scheduler", "jobs", "describe", "collect-daily",
            "--location", REGION,
            "--format", "value(schedule)"
        ])
        assert success and output == "0 9 * * *", \
            "Schedule should be '0 9 * * *'"

    def test_timezone(self):
        """Job should use Buenos Aires timezone"""
        success, output = gcloud_command([
            "scheduler", "jobs", "describe", "collect-daily",
            "--location", REGION,
            "--format", "value(timeZone)"
        ])
        assert success and output == "America/Argentina/Buenos_Aires", \
            "Timezone should be America/Argentina/Buenos_Aires"

    def test_target_endpoint(self):
        """Job should target /api/collect/run"""
        success, output = gcloud_command([
            "scheduler", "jobs", "describe", "collect-daily",
            "--location", REGION,
            "--format", "value(httpTarget.uri)"
        ])
        assert success and "/api/collect/run" in output, \
            "Should target /api/collect/run endpoint"

    def test_job_enabled(self):
        """Job should be enabled"""
        success, output = gcloud_command([
            "scheduler", "jobs", "describe", "collect-daily",
            "--location", REGION,
            "--format", "value(state)"
        ])
        assert success and output == "ENABLED", \
            "Job should be ENABLED"


@pytest.mark.unit
class TestLocalConfiguration:
    """Test local configuration files and structure"""

    def test_directories_exist(self):
        """Required directories should exist"""
        for dir_name in ["app", "public", "scripts", "docs"]:
            assert Path(dir_name).is_dir(), f"Directory '{dir_name}' should exist"

    def test_config_files_exist(self):
        """Required configuration files should exist"""
        files = [
            "firebase.json",
            "firestore.rules",
            "Dockerfile",
            ".env.example",
            ".gitignore"
        ]
        for file_name in files:
            assert Path(file_name).is_file(), f"File '{file_name}' should exist"

    def test_service_account_key_exists(self):
        """Service account key should exist"""
        assert Path("serviceAccountKey.json").is_file(), \
            "serviceAccountKey.json should exist"

    def test_env_file_exists(self):
        """.env file should exist"""
        assert Path(".env").is_file(), ".env file should exist"

    def test_env_has_project_id(self):
        """.env should contain GOOGLE_CLOUD_PROJECT"""
        env_content = Path(".env").read_text()
        assert "GOOGLE_CLOUD_PROJECT" in env_content, \
            ".env should contain GOOGLE_CLOUD_PROJECT"

    def test_gitignore_protects_secrets(self):
        """.gitignore should protect secrets"""
        gitignore = Path(".gitignore").read_text()
        assert ".env" in gitignore, ".gitignore should include .env"
        assert "serviceAccountKey.json" in gitignore, \
            ".gitignore should include serviceAccountKey.json"
