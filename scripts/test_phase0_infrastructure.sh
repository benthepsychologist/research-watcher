#!/bin/bash
# Phase 0 Infrastructure Test Suite
# Tests all deployed GCP/Firebase infrastructure

# Don't exit on error - we want to run all tests
set +e

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-research-watcher}"
REGION="us-central1"
CLOUD_RUN_SERVICE="rw-api"
CLOUD_RUN_URL="https://rw-api-491582996945.us-central1.run.app"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((TESTS_FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
}

section() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
}

# Test functions
test_cloud_run() {
    section "TEST: Cloud Run Service"

    # Test service exists
    if gcloud run services describe $CLOUD_RUN_SERVICE --region=$REGION &>/dev/null; then
        pass "Cloud Run service '$CLOUD_RUN_SERVICE' exists"
    else
        fail "Cloud Run service '$CLOUD_RUN_SERVICE' not found"
        return
    fi

    # Test service responds
    if curl -sf $CLOUD_RUN_URL/ > /dev/null; then
        pass "Cloud Run service is responding"
    else
        fail "Cloud Run service not responding at $CLOUD_RUN_URL"
    fi

    # Test service returns expected content
    RESPONSE=$(curl -s $CLOUD_RUN_URL/)
    if [[ "$RESPONSE" == *"Hello"* ]]; then
        pass "Cloud Run service returns expected content"
    else
        fail "Cloud Run service returned unexpected content: $RESPONSE"
    fi
}

test_firestore() {
    section "TEST: Firestore Database"

    # Test database exists
    if gcloud firestore databases describe --database="(default)" &>/dev/null; then
        pass "Firestore database exists"
    else
        fail "Firestore database not found"
        return
    fi

    # Test database type
    DB_TYPE=$(gcloud firestore databases describe --database="(default)" --format="value(type)")
    if [[ "$DB_TYPE" == "FIRESTORE_NATIVE" ]]; then
        pass "Firestore database is in Native mode"
    else
        fail "Firestore database type is '$DB_TYPE', expected 'FIRESTORE_NATIVE'"
    fi

    # Test database location
    DB_LOCATION=$(gcloud firestore databases describe --database="(default)" --format="value(locationId)")
    if [[ "$DB_LOCATION" == "us-central1" ]]; then
        pass "Firestore database location is us-central1"
    else
        warn "Firestore database location is '$DB_LOCATION', expected 'us-central1'"
    fi
}

test_pubsub() {
    section "TEST: Pub/Sub Infrastructure"

    # Test topic exists
    if gcloud pubsub topics describe rw-wal &>/dev/null; then
        pass "Pub/Sub topic 'rw-wal' exists"
    else
        fail "Pub/Sub topic 'rw-wal' not found"
        return
    fi

    # Test subscription exists
    if gcloud pubsub subscriptions describe rw-wal-to-bq &>/dev/null; then
        pass "Pub/Sub subscription 'rw-wal-to-bq' exists"
    else
        fail "Pub/Sub subscription 'rw-wal-to-bq' not found"
        return
    fi

    # Test subscription is connected to BigQuery
    BQ_TABLE=$(gcloud pubsub subscriptions describe rw-wal-to-bq --format="value(bigqueryConfig.table)")
    if [[ "$BQ_TABLE" == "research-watcher:research_wal.events" ]]; then
        pass "Subscription is connected to BigQuery table"
    else
        fail "Subscription BigQuery table is '$BQ_TABLE', expected 'research-watcher:research_wal.events'"
    fi

    # Test message publishing
    TEST_MSG_ID=$(gcloud pubsub topics publish rw-wal --message='{"test":"phase0_test"}' --format="value(messageIds[0])")
    if [[ -n "$TEST_MSG_ID" ]]; then
        pass "Can publish messages to topic (messageId: $TEST_MSG_ID)"
    else
        fail "Failed to publish test message"
    fi
}

test_bigquery() {
    section "TEST: BigQuery Infrastructure"

    # Test dataset exists
    if bq show research-watcher:research_wal &>/dev/null; then
        pass "BigQuery dataset 'research_wal' exists"
    else
        fail "BigQuery dataset 'research_wal' not found"
        return
    fi

    # Test table exists
    if bq show research-watcher:research_wal.events &>/dev/null; then
        pass "BigQuery table 'events' exists"
    else
        fail "BigQuery table 'events' not found"
        return
    fi

    # Test table schema
    SCHEMA=$(bq show --format=prettyjson research-watcher:research_wal.events | grep -o '"name": "data"')
    if [[ -n "$SCHEMA" ]]; then
        pass "BigQuery table has 'data' field in schema"
    else
        fail "BigQuery table schema missing 'data' field"
    fi

    # Test partitioning
    PARTITION=$(bq show --format=prettyjson research-watcher:research_wal.events | grep -o '"field": "publish_time"')
    if [[ -n "$PARTITION" ]]; then
        pass "BigQuery table is partitioned by publish_time"
    else
        warn "BigQuery table partitioning not detected"
    fi
}

test_service_accounts() {
    section "TEST: Service Accounts & IAM"

    # Test API service account exists
    if gcloud iam service-accounts describe rw-api@research-watcher.iam.gserviceaccount.com &>/dev/null; then
        pass "Service account 'rw-api' exists"
    else
        fail "Service account 'rw-api' not found"
    fi

    # Test scheduler service account exists
    if gcloud iam service-accounts describe scheduler-invoker@research-watcher.iam.gserviceaccount.com &>/dev/null; then
        pass "Service account 'scheduler-invoker' exists"
    else
        fail "Service account 'scheduler-invoker' not found"
    fi

    # Test API service account has datastore role
    ROLES=$(gcloud projects get-iam-policy $PROJECT_ID --flatten="bindings[].members" \
        --filter="bindings.members:serviceAccount:rw-api@research-watcher.iam.gserviceaccount.com" \
        --format="value(bindings.role)")

    if echo "$ROLES" | grep -q "roles/datastore.user"; then
        pass "Service account 'rw-api' has datastore.user role"
    else
        fail "Service account 'rw-api' missing datastore.user role"
    fi

    if echo "$ROLES" | grep -q "roles/pubsub.publisher"; then
        pass "Service account 'rw-api' has pubsub.publisher role"
    else
        fail "Service account 'rw-api' missing pubsub.publisher role"
    fi

    # Test scheduler can invoke Cloud Run
    INVOKER_POLICY=$(gcloud run services get-iam-policy $CLOUD_RUN_SERVICE --region=$REGION \
        --filter="bindings.members:serviceAccount:scheduler-invoker@research-watcher.iam.gserviceaccount.com" \
        --format="value(bindings.role)" 2>/dev/null || echo "")

    if echo "$INVOKER_POLICY" | grep -q "run.invoker"; then
        pass "Service account 'scheduler-invoker' can invoke Cloud Run"
    else
        fail "Service account 'scheduler-invoker' missing run.invoker permission"
    fi
}

test_cloud_scheduler() {
    section "TEST: Cloud Scheduler"

    # Test job exists
    if gcloud scheduler jobs describe collect-daily --location=$REGION &>/dev/null; then
        pass "Cloud Scheduler job 'collect-daily' exists"
    else
        fail "Cloud Scheduler job 'collect-daily' not found"
        return
    fi

    # Test schedule
    SCHEDULE=$(gcloud scheduler jobs describe collect-daily --location=$REGION --format="value(schedule)")
    if [[ "$SCHEDULE" == "0 9 * * *" ]]; then
        pass "Scheduler has correct cron schedule (0 9 * * *)"
    else
        fail "Scheduler schedule is '$SCHEDULE', expected '0 9 * * *'"
    fi

    # Test timezone
    TIMEZONE=$(gcloud scheduler jobs describe collect-daily --location=$REGION --format="value(timeZone)")
    if [[ "$TIMEZONE" == "America/Argentina/Buenos_Aires" ]]; then
        pass "Scheduler has correct timezone"
    else
        fail "Scheduler timezone is '$TIMEZONE', expected 'America/Argentina/Buenos_Aires'"
    fi

    # Test target URL
    TARGET_URL=$(gcloud scheduler jobs describe collect-daily --location=$REGION --format="value(httpTarget.uri)")
    if [[ "$TARGET_URL" == *"/api/collect/run" ]]; then
        pass "Scheduler targets correct endpoint (/api/collect/run)"
    else
        fail "Scheduler target URL is '$TARGET_URL'"
    fi

    # Test job is enabled
    STATE=$(gcloud scheduler jobs describe collect-daily --location=$REGION --format="value(state)")
    if [[ "$STATE" == "ENABLED" ]]; then
        pass "Scheduler job is enabled"
    else
        fail "Scheduler job state is '$STATE', expected 'ENABLED'"
    fi
}

test_local_files() {
    section "TEST: Local Configuration Files"

    cd "$(dirname "$0")/.." || exit 1

    # Test project structure
    for dir in app public scripts docs; do
        if [[ -d "$dir" ]]; then
            pass "Directory '$dir' exists"
        else
            fail "Directory '$dir' not found"
        fi
    done

    # Test configuration files
    for file in firebase.json firestore.rules Dockerfile .env.example .gitignore; do
        if [[ -f "$file" ]]; then
            pass "File '$file' exists"
        else
            fail "File '$file' not found"
        fi
    done

    # Test service account key (don't print path for security)
    if [[ -f "serviceAccountKey.json" ]]; then
        pass "Service account key file exists"
    else
        warn "Service account key file not found (may need to create)"
    fi

    # Test .env file
    if [[ -f ".env" ]]; then
        pass ".env file exists"

        # Check required variables
        if grep -q "GOOGLE_CLOUD_PROJECT" .env; then
            pass ".env contains GOOGLE_CLOUD_PROJECT"
        else
            fail ".env missing GOOGLE_CLOUD_PROJECT"
        fi
    else
        fail ".env file not found"
    fi
}

# Main execution
main() {
    echo "╔════════════════════════════════════════╗"
    echo "║  Phase 0 Infrastructure Test Suite    ║"
    echo "║  Research Watcher                      ║"
    echo "╚════════════════════════════════════════╝"
    echo ""
    echo "Project: $PROJECT_ID"
    echo "Region: $REGION"
    echo ""

    # Set project
    gcloud config set project $PROJECT_ID &>/dev/null

    # Run all tests
    test_cloud_run
    test_firestore
    test_pubsub
    test_bigquery
    test_service_accounts
    test_cloud_scheduler
    test_local_files

    # Summary
    echo ""
    echo "=========================================="
    echo "TEST SUMMARY"
    echo "=========================================="
    echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
    echo "Total:  $((TESTS_PASSED + TESTS_FAILED))"
    echo ""

    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
        echo ""
        exit 0
    else
        echo -e "${RED}❌ SOME TESTS FAILED${NC}"
        echo ""
        exit 1
    fi
}

# Run tests
main
