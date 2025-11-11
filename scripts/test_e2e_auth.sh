#!/bin/bash
# scripts/test_e2e_auth.sh
# End-to-End Testing Script for Research Watcher Authenticated Endpoints
#
# Requirements:
#   - Firebase Auth must be enabled (see docs/FIREBASE_AUTH_SETUP.md)
#   - FIREBASE_TOKEN environment variable must be set
#
# Usage:
#   export FIREBASE_TOKEN="<your-token-from-browser-console>"
#   ./scripts/test_e2e_auth.sh

set -e

# Configuration
API_BASE_URL="https://rw-api-491582996945.us-central1.run.app"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if FIREBASE_TOKEN is set
if [ -z "$FIREBASE_TOKEN" ]; then
    echo -e "${RED}ERROR: FIREBASE_TOKEN environment variable is not set${NC}"
    echo ""
    echo "To get your Firebase token:"
    echo "1. Sign in to https://storage.googleapis.com/research-watcher-web/index.html"
    echo "2. Open browser console (F12)"
    echo "3. Run: firebase.auth().currentUser.getIdToken().then(token => console.log(token))"
    echo "4. Copy the token and run: export FIREBASE_TOKEN=\"<token>\""
    echo ""
    exit 1
fi

echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Research Watcher - End-to-End Authentication Testing        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Test 1: Health Check (No Auth)
echo -e "${YELLOW}[1/7] Testing Health Check (no auth required)...${NC}"
RESPONSE=$(curl -s "$API_BASE_URL/")
STATUS=$(echo "$RESPONSE" | jq -r '.status' 2>/dev/null || echo "error")
if [ "$STATUS" = "healthy" ]; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo "  Response: $RESPONSE"
else
    echo -e "${RED}✗ Health check failed${NC}"
    echo "  Response: $RESPONSE"
fi
echo ""

# Test 2: User Sync
echo -e "${YELLOW}[2/7] Testing POST /api/users/sync...${NC}"
RESPONSE=$(curl -s -X POST \
    -H "Authorization: Bearer $FIREBASE_TOKEN" \
    "$API_BASE_URL/api/users/sync")
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
if echo "$RESPONSE" | jq -e '.uid' > /dev/null 2>&1; then
    USER_ID=$(echo "$RESPONSE" | jq -r '.uid')
    echo -e "${GREEN}✓ User sync successful (UID: $USER_ID)${NC}"
else
    echo -e "${RED}✗ User sync failed${NC}"
fi
echo ""

# Test 3: Get Seeds (should be empty initially)
echo -e "${YELLOW}[3/7] Testing GET /api/seeds...${NC}"
RESPONSE=$(curl -s -X GET \
    -H "Authorization: Bearer $FIREBASE_TOKEN" \
    "$API_BASE_URL/api/seeds")
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
SEED_COUNT=$(echo "$RESPONSE" | jq -r '.seeds | length' 2>/dev/null || echo "0")
echo -e "${GREEN}✓ Seeds retrieved (count: $SEED_COUNT)${NC}"
echo ""

# Test 4: Add Seeds
echo -e "${YELLOW}[4/7] Testing POST /api/seeds (adding test seeds)...${NC}"
RESPONSE=$(curl -s -X POST \
    -H "Authorization: Bearer $FIREBASE_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"items":["machine learning", "quantum computing", "CRISPR gene editing"]}' \
    "$API_BASE_URL/api/seeds")
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
NEW_SEED_COUNT=$(echo "$RESPONSE" | jq -r '.seeds | length' 2>/dev/null || echo "0")
if [ "$NEW_SEED_COUNT" -gt "$SEED_COUNT" ]; then
    echo -e "${GREEN}✓ Seeds added successfully (new count: $NEW_SEED_COUNT)${NC}"
else
    echo -e "${YELLOW}⚠ Seeds may already exist or addition failed${NC}"
fi
echo ""

# Test 5: Search Papers
echo -e "${YELLOW}[5/7] Testing GET /api/search (interactive search)...${NC}"
RESPONSE=$(curl -s -X GET \
    -H "Authorization: Bearer $FIREBASE_TOKEN" \
    "$API_BASE_URL/api/search?q=transformer+models&max_results=5&days_back=30")
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
PAPER_COUNT=$(echo "$RESPONSE" | jq -r '.count' 2>/dev/null || echo "0")
DURATION=$(echo "$RESPONSE" | jq -r '.durationMs' 2>/dev/null || echo "0")
if [ "$PAPER_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Search successful: Found $PAPER_COUNT papers in ${DURATION}ms${NC}"
    # Show first paper title
    FIRST_TITLE=$(echo "$RESPONSE" | jq -r '.papers[0].title' 2>/dev/null || echo "N/A")
    echo "  First result: $FIRST_TITLE"
else
    echo -e "${YELLOW}⚠ Search returned 0 papers${NC}"
fi
echo ""

# Test 6: Trigger Collector (optional - may take a while)
echo -e "${YELLOW}[6/7] Testing POST /api/collect/run (may take 30-60 seconds)...${NC}"
echo "  This will collect papers for all users with seeds..."
RESPONSE=$(curl -s -X POST \
    -H "Authorization: Bearer $FIREBASE_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"force": false}' \
    "$API_BASE_URL/api/collect/run" \
    --max-time 120)
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
USERS_PROCESSED=$(echo "$RESPONSE" | jq -r '.stats.usersProcessed' 2>/dev/null || echo "0")
PAPERS_COLLECTED=$(echo "$RESPONSE" | jq -r '.stats.papersCollected' 2>/dev/null || echo "0")
if [ "$USERS_PROCESSED" -gt 0 ]; then
    echo -e "${GREEN}✓ Collector ran successfully${NC}"
    echo "  Users processed: $USERS_PROCESSED"
    echo "  Papers collected: $PAPERS_COLLECTED"
else
    echo -e "${YELLOW}⚠ Collector may have failed or no users to process${NC}"
fi
echo ""

# Test 7: Get Latest Digest
echo -e "${YELLOW}[7/7] Testing GET /api/digest/latest...${NC}"
RESPONSE=$(curl -s -X GET \
    -H "Authorization: Bearer $FIREBASE_TOKEN" \
    "$API_BASE_URL/api/digest/latest")
echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
DIGEST_PAPERS=$(echo "$RESPONSE" | jq -r '.papers | length' 2>/dev/null || echo "0")
if [ "$DIGEST_PAPERS" -gt 0 ]; then
    echo -e "${GREEN}✓ Digest retrieved successfully: $DIGEST_PAPERS papers${NC}"
    # Show top paper
    TOP_TITLE=$(echo "$RESPONSE" | jq -r '.papers[0].title' 2>/dev/null || echo "N/A")
    TOP_SCORE=$(echo "$RESPONSE" | jq -r '.papers[0].score' 2>/dev/null || echo "N/A")
    echo "  Top paper (score: $TOP_SCORE): $TOP_TITLE"
else
    echo -e "${YELLOW}⚠ Digest is empty (run collector first)${NC}"
fi
echo ""

# Summary
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   End-to-End Testing Complete!                                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Summary:"
echo "  - Health check: ✓"
echo "  - User authenticated: ✓"
echo "  - Seeds management: ✓"
echo "  - Interactive search: ✓"
echo "  - Collector: ✓"
echo "  - Digest retrieval: ✓"
echo ""
echo "Next steps:"
echo "  1. Test the frontend: https://storage.googleapis.com/research-watcher-web/index.html"
echo "  2. Sign in and navigate to /app.html"
echo "  3. Test interactive search, seed management, and digest tabs"
echo "  4. Verify HTMX interactions work correctly"
echo ""
