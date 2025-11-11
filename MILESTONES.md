# Research Watcher - Development Milestones

**Project**: Research Watcher v0
**Based on**: AIP 1.1 & Spec 1.0
**Status**: 🟢 Phase 3 Complete
**Current Phase**: Phase 3 → Phase 4 (Infra Upgrade Spec)
**Last Updated**: 2025-11-11

---

## Milestone Overview

| Phase | Milestone | Status | Completed |
|-------|-----------|--------|-----------|
| 0 | Bootstrap & Environment | ✅ | 2025-11-06 |
| 1 | Backend Core (API Skeleton) | ✅ | 2025-11-06 |
| 2 | Collector + Dual-Write | ✅ | 2025-11-08 |
| 3 | Frontend & User Flow | ✅ | 2025-11-11 |
| 4 | Event Ledger & Consumer Stub | ⏳ | - |
| 5 | v1 Fan-Out Readiness | ⏳ | - |
| 6 | Agentic Extensions (Optional) | ⏳ | - |

**Legend**: ✅ Complete | 🔄 In Progress | ⏳ Pending | ⏭️ Skipped

---

## Phase 0: Bootstrap & Environment ✅

**Status**: COMPLETE (2025-11-06)
**Goal**: Stand up base Firebase + GCP project scaffolding

### Tasks
- [x] Create Firebase Project
  - [x] Enable Firestore (Native Mode)
  - [x] Enable Firebase Auth (deferred to Phase 3 - not required for Phase 0)
- [x] Enable GCP APIs
  - [x] Cloud Run API
  - [x] Cloud Pub/Sub API
  - [x] BigQuery API
  - [x] Cloud Scheduler API
  - [x] Cloud IAM API
  - [x] Firestore API
- [x] Create GCP Resources
  - [x] Pub/Sub Topic: `rw-wal`
  - [x] BigQuery Dataset: `research_wal`
  - [x] BigQuery Table: `events` (partitioned by `publish_time`)
  - [x] Configure Pub/Sub → BigQuery sink with subscription `rw-wal-to-bq`
- [x] Create project structure
  - [x] `app/` directory with `__init__.py`
  - [x] `app/api/` for blueprints
  - [x] `app/services/` for external API clients
  - [x] `app/utils/` for shared utilities
  - [x] `public/` for static frontend files
  - [x] `tests/` for test files
  - [x] `scripts/` for automation scripts
  - [x] `docs/` for documentation
- [x] Configure environment
  - [x] Create `.env.example` template
  - [x] Create `.env` file
  - [x] Add `.env` to `.gitignore`
  - [x] Document required environment variables
- [x] Create Firebase Hosting configuration
  - [x] `firebase.json` with rewrite rules
  - [x] `firestore.rules` security rules
  - [x] `firestore.indexes.json` for indexes
  - [x] Deploy hosting stub (deferred to Phase 3 - requires Firebase CLI)
- [x] Create Service Accounts
  - [x] Create `rw-api` service account for Cloud Run
  - [x] Create `scheduler-invoker` service account for Cloud Scheduler
  - [x] Grant Cloud Run Invoker role to scheduler
  - [x] Grant Firestore, Pub/Sub, Cloud Tasks roles to rw-api
  - [x] Create service account key for local development
- [x] Create Dockerfile for Cloud Run
- [x] Deploy initial Cloud Run service
- [x] Create Cloud Scheduler job `collect-daily`
- [x] Create comprehensive test suite (Phase 0.5)
  - [x] Bash integration tests (36 tests)
  - [x] Pytest suite (39 tests: 33 integration, 6 unit)
  - [x] Testing documentation

### Deliverables
- ✅ Firebase project configured
- ✅ GCP infrastructure online
- ✅ Cloud Run placeholder deploys
- ✅ Firebase Hosting rewrite verified
- ✅ Git tag: `v0-bootstrap`

### Dependencies
- GCP Project with billing enabled
- Firebase CLI installed
- gcloud CLI configured

---

## Phase 1: Backend Core (API Skeleton) ✅

**Status**: COMPLETE (2025-11-06)
**Goal**: Deploy Flask API on Cloud Run with auth, routing, and blueprints

### Tasks
- [x] Refactor `main.py` to use App Factory pattern
- [x] Initialize Firebase Admin SDK in `app/__init__.py`
- [x] Create JWT validator (`app/utils/auth.py`)
  - [x] Implement `@login_required` decorator
  - [x] Implement `@scheduler_auth_required` decorator
  - [x] Verify Firebase ID tokens
  - [x] Extract `uid` from token
- [x] Create Flask Blueprints
  - [x] `app/api/users.py` - User profile management
  - [x] `app/api/seeds.py` - Research seeds CRUD
  - [x] `app/api/digest.py` - Digest retrieval
  - [x] `app/api/collector.py` - Collection trigger endpoints (stubs)
  - [x] `app/api/feedback.py` - User feedback tracking
- [x] Implement `/api/users/sync` endpoint
  - [x] Idempotent user profile creation
  - [x] Set default quota and tier
  - [x] Also implemented `/api/users/profile` GET endpoint
- [x] Update `requirements.txt`
  - [x] Already had `firebase-admin`
  - [x] Already had all required dependencies
  - [x] All versions pinned
- [x] `.env.example` already exists with all required vars
- [x] Dockerfile already configured for production
- [x] Deploy to Cloud Run
  - [x] Configure environment variables
  - [x] Test with unauthenticated request (401 ✅)
  - [x] Test with valid Firebase token (deferred to Phase 3 UI)
- [x] Create Phase 1 integration tests (16 tests in test_phase1_api.py)

### Deliverables
- ✅ Functional secured API endpoints
- ✅ Auth and Firestore connection working
- ✅ All blueprints registered
- ✅ Cloud Run service deployed and accessible
- ✅ Git tag: `v0-api-skeleton`

### Validation
```bash
# Should fail (401)
curl https://rw-api-xxxxx.run.app/api/users/sync

# Should succeed (200)
curl -H "Authorization: Bearer <FIREBASE_TOKEN>" \
  https://rw-api-xxxxx.run.app/api/users/sync
```

---

## Phase 2: Collector + Dual-Write (WAL Emission) ✅

**Status**: COMPLETE (2025-11-08)
**Goal**: Implement daily collector pipeline with Firestore writes + Pub/Sub publish

### Tasks
- [x] Build external API clients (`app/services/`)
  - [x] `openalex.py` - OpenAlex API wrapper with polite pool
  - [x] `semantic_scholar.py` - Semantic Scholar API wrapper (optional API key)
  - [x] `arxiv_client.py` - arXiv API wrapper with XML parsing
  - [x] Error handling and null-safety
  - [x] Note: Crossref deferred - using OpenAlex + S2 + arXiv for semantic intelligence
- [x] Create paper deduplication logic (`app/services/collector.py`)
  - [x] Normalize DOIs, arXiv IDs
  - [x] Generate stable paper IDs (doi: / arxiv: / hash: prefixes)
  - [x] Merge metadata from multiple sources (max citations, merge provenance)
- [x] Create scoring algorithm (`app/services/collector.py`)
  - [x] Factor: citation count (log scale, max 30 points)
  - [x] Factor: venue prestige (Nature/Science/Cell/PNAS)
  - [x] Factor: recency (current year = 25 points)
  - [x] Factor: open access availability (15 points)
  - [x] Factor: abstract presence (10 points)
  - [x] Total: 0-100 score range
- [x] Implement `/api/collect/run` endpoint
  - [x] Verify OIDC token from Cloud Scheduler SA
  - [x] Fetch all users with seeds
  - [x] For each user:
    - [x] Fetch papers matching seeds from all APIs
    - [x] Deduplicate and score
    - [x] Upsert to `papers/` collection (sanitize IDs, replace / with _)
    - [x] Create/update `digests/{uid}_latest` document
    - [x] Publish WAL event to Pub/Sub
  - [x] Log runId, counts, errors
  - [x] Note: Quota enforcement deferred to Phase 3
- [x] Create WAL event builder
  - [x] Follow canonical schema (v1)
  - [x] Include provenance flags
  - [x] Timestamp in ISO8601
- [x] Implement `/api/seeds` endpoints (from Phase 1)
  - [x] GET: Retrieve user seeds
  - [x] POST: Update seeds
  - [x] Note: Quota validation deferred to Phase 3
- [x] Implement `/api/digest/latest` endpoint
  - [x] Retrieve latest digest for user
  - [x] Expand paper details from `papers/` collection
  - [x] Sort by score descending
- [x] Implement `/api/feedback` endpoint (from Phase 1)
  - [x] Record user actions (save, mute, click)
  - [x] Write to `events/{uid}/` collection
- [x] Cloud Scheduler job (already exists from Phase 0)
  - [x] Schedule: `0 9 * * *` (09:00 daily)
  - [x] Timezone: `America/Argentina/Buenos_Aires`
  - [x] Target: `/api/collect/run`
  - [x] Auth: OIDC with service account
- [x] Verify BigQuery sink
  - [x] Confirmed WAL events arrive in `research_wal.events`
  - [x] Verified partition by date
  - [x] Tested queries successfully

### Testing
- [x] Created `scripts/test_api_clients.py` - comprehensive API client tests
  - [x] OpenAlex normalization (fixed null authorship handling)
  - [x] Semantic Scholar search
  - [x] arXiv search
  - [x] Deduplication logic
  - [x] Scoring algorithm
  - [x] All 5 tests passing
- [x] Created `scripts/create_test_user.py` - Firebase Admin SDK test user creation
  - [x] Test user: `test-user-phase2`
  - [x] 3 test seeds: LLMs, quantum computing, CRISPR
- [x] End-to-end acceptance test
  - [x] Triggered collector via curl
  - [x] Verified 1 user, 49 papers, 1 digest, 0 errors
  - [x] Confirmed WAL event in BigQuery with correct schema

### Deliverables
- ✅ End-to-end collector run working
- ✅ Firestore contains papers and digests
- ✅ Pub/Sub events land in BigQuery
- ✅ Cloud Scheduler job already configured
- ✅ All user endpoints functional
- ✅ Git tag: `v0-collector-dual-write`

### Validation
```bash
# Trigger collector manually (tested successfully)
curl -X POST https://rw-api-491582996945.us-central1.run.app/api/collect/run

# Check BigQuery (confirmed working)
bq query --project_id=research-watcher-491582996945 \
  "SELECT type, uid, ts FROM research_wal.events WHERE type = 'digest.created' LIMIT 1"

# Result: 1 user processed, 49 papers collected, 1 digest created
```

### Key Decisions
- **API Sources**: Using OpenAlex + Semantic Scholar + arXiv (dropped Crossref)
  - Semantic Scholar provides crucial semantic intelligence (embeddings, influence metrics)
  - Using own S2 API key during limited alpha
  - Plan: Switch to user-provided keys when scaling beyond alpha
- **Commercial Licensing**:
  - OpenAlex: ✅ Free for commercial use
  - arXiv: ✅ Free for commercial use
  - Semantic Scholar: Using own API key during beta, will require user-provided keys or partnership for production
- **Document ID Sanitization**: Replace `/` with `_` in paper IDs for Firestore compatibility
- **Digest Storage**: Using composite document IDs `{uid}_latest` instead of subcollections

---

## Phase 3: Frontend & User Flow + Firebase Hosting ✅

**Status**: COMPLETE (2025-11-11)
**Goal**: Interactive web UI with sign-in, seed management, digest view, real-time search, and professional Firebase Hosting

### Tasks
- [x] Create landing page (`public/index.html`)
  - [x] Project description
  - [x] Firebase Auth integration (Google Sign-In)
  - [x] Auto-redirect to app after authentication
  - [x] Links to About and Privacy pages
- [x] Create authenticated app page (`public/app.html`)
  - [x] HTMX-powered SPA with Firebase Auth
  - [x] Tailwind CSS styling
  - [x] Tab-based navigation: Digest | Search | Seeds | Saved
  - [x] Token-based API authentication
- [x] Create about page (`public/about.html`)
  - [x] Project description and mission
  - [x] Technology stack overview
  - [x] Contact information
- [x] Create privacy policy page (`public/privacy.html`)
  - [x] Data collection policy
  - [x] User rights and consent
  - [x] Third-party services disclosure
- [x] Implement Firebase Auth flow
  - [x] Google sign-in popup
  - [x] Session persistence via `onAuthStateChanged`
  - [x] Auto-redirect after login to `app.html`
  - [x] Token stored in `localStorage`
  - [x] Call `/api/users/sync` on authentication
  - [x] Sign-out page (`public/signout.html`)
- [x] Implement seed management UI
  - [x] Add/remove research topic keywords
  - [x] Quota display (seeds limit, runs per day)
  - [x] Real-time seed count tracking
  - [x] Example seeds for guidance
  - [x] Backend validation enforced
- [x] Implement digest viewer
  - [x] Fetch from `/api/digest/latest` on page load
  - [x] Render paper cards with:
    - [x] Title, authors, venue, year
    - [x] Abstract (truncated to 300 chars)
    - [x] Score badge with color coding
    - [x] Open Access indicator
    - [x] Provenance badges (OpenAlex/S2/arXiv)
    - [x] Clickable links to paper sources
    - [x] Save button on each card
  - [x] Sort by score descending
  - [x] Show "no digest yet" empty state
- [x] Implement interactive search
  - [x] Real-time search endpoint (`/api/search`)
  - [x] Search form with query input
  - [x] Configurable filters: days back, max results
  - [x] Loading state during search
  - [x] Results rendered as paper cards
  - [x] Client-side rate limiting (1 req/sec for S2 compliance)
- [x] Implement saved papers functionality
  - [x] Backend API endpoints (GET/POST/DELETE `/api/saved`)
  - [x] Save button on digest and search paper cards
  - [x] Saved papers tab with reading list
  - [x] Remove button on saved papers
  - [x] Firestore subcollection storage
- [x] Configure CORS in Flask
  - [x] Allow Cloud Storage domain
  - [x] Allow Firebase Hosting domains
  - [x] Allow localhost for development
  - [x] Credentials support for auth headers
- [x] Deploy frontend
  - [x] Migrated from Cloud Storage to Firebase Hosting
  - [x] Firebase CLI installed (v14.24.2)
  - [x] Service account granted Firebase Develop Admin role
  - [x] Deployed to https://research-watcher.web.app
  - [x] Cloud Run API rewrites configured in firebase.json
  - [x] All pages deployed (index.html, app.html, signout.html)
- [x] Add quota UI display
  - [x] Account tier display
  - [x] Seeds usage (X / Y format)
  - [x] Runs per day limit
  - [x] Visual quota card in Seeds tab
- [x] Setup Firebase Hosting with custom domain
  - [x] Deployed to Firebase Hosting
  - [x] Default URL working: https://research-watcher.web.app
  - [x] Custom domain configured: app.researchwatcher.org
  - [x] DNS records added (A records + TXT verification)
  - [x] Waiting for SSL certificate provisioning (1-24 hours)

### Deliverables
- ✅ Usable public web app with modern UI
- ✅ Firebase Auth flow working (Google Sign-In)
- ✅ Functional backend integration (all endpoints working)
- ✅ Responsive design (Tailwind CSS, mobile-friendly)
- ✅ Interactive search feature (real-time paper discovery)
- ✅ Saved papers reading list
- ✅ Quota limits displayed
- ✅ Firebase Hosting deployment with Cloud Run backend proxy
- ✅ Custom domain configured (app.researchwatcher.org)
- ✅ Git tag: `v0-frontend`

### Validation
- [x] Can sign in with Google
- [x] Can add/update/remove seeds
- [x] Can view daily digest
- [x] Can search papers in real-time
- [x] Can save papers to reading list
- [x] Can remove saved papers
- [x] Quota limits displayed correctly
- [x] All tabs functional
- [x] API authentication working
- [x] Token audience mismatch resolved

### Key Decisions
- **Frontend Hosting**: Migrated to Firebase Hosting with custom domain
  - Service account authentication (Firebase Develop Admin role)
  - Automatic Cloud Run backend proxy via rewrites
  - Custom domain: app.researchwatcher.org (researchwatcher.org purchased)
- **UI Framework**: HTMX + Tailwind CSS (minimal JS, fast, responsive)
- **Search Feature**: Added interactive search alongside daily digest (expanded from original plan)
- **Saved Papers**: Implemented as Firestore subcollection instead of feedback-only approach
- **Quota Display**: Shows limits even though high for testing (supports future tier management)
- **Auth Method**: Google Sign-In only (email/password deferred for simplicity)

### Documentation Created
- [x] `docs/E2E_TESTING_CHECKLIST.md` - Comprehensive testing guide
- [x] `docs/FIREBASE_AUTH_SETUP.md` - Firebase Auth configuration steps
- [x] `docs/QUICK_START_GUIDE.md` - Quick start for new developers
- [x] `scripts/test_e2e_auth.sh` - Automated API testing script

### Bugs Fixed
- [x] Firebase API key validation
- [x] Token audience mismatch (`research-watcher` vs `research-watcher-491582996945`)
- [x] URL redirect losing bucket path in Cloud Storage
- [x] Seeds API field name mismatch (`items` vs `seeds`)
- [x] Browser cache issues with old JavaScript

---

## Phase 4: Event Ledger & Consumer Stub

**Goal**: Verify WAL integrity and prepare for event-sourced flip

### Tasks
- [ ] Define canonical event schema (v1)
  - [ ] Document in `docs/event-schema.md`
  - [ ] Match BigQuery table schema
  - [ ] Add validation helpers
- [ ] Create sample consumer endpoint (`/_wal/push`)
  - [ ] Verify OIDC token (Pub/Sub service account)
  - [ ] Parse WAL event
  - [ ] Idempotent upsert to Firestore
  - [ ] Log processing status
- [ ] Create test Pub/Sub subscription
  - [ ] Push to consumer endpoint
  - [ ] Verify idempotency
  - [ ] Test error handling
- [ ] Write BigQuery validation queries
  - [ ] Count events by type
  - [ ] Check for gaps in runIds
  - [ ] Verify provenance flags
  - [ ] Export sample for testing
- [ ] Create replay script (`scripts/replay_from_bq.py`)
  - [ ] Read events from BigQuery
  - [ ] Rebuild Firestore state
  - [ ] Support date range filters
  - [ ] Dry-run mode
  - [ ] Progress reporting
- [ ] Test replay on separate Firestore instance
  - [ ] Export events for last 7 days
  - [ ] Clear test Firestore
  - [ ] Replay events
  - [ ] Compare with production state
- [ ] Document WAL schema and consumer pattern
  - [ ] Add to `docs/event-sourcing.md`
  - [ ] Include example events
  - [ ] Describe idempotency keys

### Deliverables
- ✅ Durable WAL in BigQuery
- ✅ Consumer stub exists and works
- ✅ System is replayable
- ✅ Replay script validated
- ✅ Git tag: `v0-ledger-verified`

### Validation
```bash
# Query recent events
bq query "SELECT type, COUNT(*) FROM research_wal.events
WHERE DATE(_PARTITIONTIME)=CURRENT_DATE() GROUP BY type"

# Test replay (dry run)
python scripts/replay_from_bq.py --start-date 2025-11-01 --dry-run
```

---

## Phase 5: v1 Fan-Out Readiness

**Goal**: Lay plumbing for Cloud Tasks / Pub/Sub worker architecture

### Tasks
- [ ] Implement `/api/collect/queue` endpoint
  - [ ] Fetch all users with seeds
  - [ ] Enqueue Cloud Task per user
  - [ ] Return queue status
  - [ ] Feature flag: `USE_TASKS_FANOUT`
- [ ] Implement `/api/collect/worker` endpoint
  - [ ] Accept `uid` parameter
  - [ ] Process single user's collection
  - [ ] Publish WAL event
  - [ ] Return processing status
- [ ] Create Cloud Tasks queue
  - [ ] Queue name: `user-collections`
  - [ ] Rate limits: 10 tasks/second
  - [ ] Retry policy: max 3 attempts
- [ ] Create worker service account
  - [ ] Grant Cloud Run Invoker role
  - [ ] Grant Pub/Sub Publisher role
  - [ ] Grant Firestore Writer role
- [ ] Add feature flags to environment
  - [ ] `USE_PUBSUB_AS_SOURCE=false`
  - [ ] `USE_TASKS_FANOUT=false`
  - [ ] `ENABLE_ANALYTICS=true`
- [ ] Add monitoring and metrics
  - [ ] Log task enqueue count
  - [ ] Log task success/failure
  - [ ] Alert on queue backlog
  - [ ] Alert on worker errors
- [ ] Create migration plan document
  - [ ] Steps to flip to v1 mode
  - [ ] Rollback procedure
  - [ ] Testing checklist
- [ ] Test fan-out in staging
  - [ ] Enable `USE_TASKS_FANOUT=true`
  - [ ] Trigger queue endpoint
  - [ ] Verify all users processed
  - [ ] Check WAL events
  - [ ] Compare results with v0

### Deliverables
- ✅ Fan-out infrastructure ready
- ✅ Worker endpoint functional
- ✅ Feature flags configured
- ✅ Monitoring in place
- ✅ Ready to flip to v1
- ✅ Git tag: `v1-ready-fanout`

### Validation
```bash
# Test queue (with flag enabled)
curl -H "Authorization: Bearer <OIDC_TOKEN>" \
  -X POST https://rw-api-xxxxx.run.app/api/collect/queue

# Check task queue
gcloud tasks queues describe user-collections

# Monitor worker logs
gcloud logs read --filter="resource.type=cloud_run_revision AND resource.labels.service_name=rw-api"
```

---

## Phase 6: Agentic Extensions (Optional)

**Goal**: Enable AI/automation agents to react to WAL events

### Tasks
- [ ] Create BigQuery view for high-value papers
  ```sql
  CREATE VIEW research_wal.vw_recent_highscore AS
  SELECT * FROM research_wal.events
  WHERE type = 'papers.upserted'
    AND JSON_EXTRACT_SCALAR(items, '$[0].score') > 3.5
    AND DATE(_PARTITIONTIME) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
  ```
- [ ] Create Agent Bridge API blueprint (`app/api/agents.py`)
  - [ ] `GET /api/events` - Query recent events
  - [ ] `POST /api/actions` - Agent-triggered actions
  - [ ] Require service account auth
- [ ] Create agent service account
  - [ ] Grant BigQuery Reader role
  - [ ] Grant Firestore Writer role (limited)
  - [ ] Grant Pub/Sub Subscriber role
- [ ] Create sample summarization agent
  - [ ] Poll high-score papers
  - [ ] Generate summaries using LLM
  - [ ] Store summaries in Firestore
  - [ ] Log agent actions to WAL
- [ ] Create notification agent (optional)
  - [ ] Subscribe to high-score events
  - [ ] Send email digests
  - [ ] Integrate with SendGrid/Mailgun
- [ ] Document agent patterns
  - [ ] Add to `docs/agents.md`
  - [ ] Include authentication setup
  - [ ] Provide example agents
  - [ ] Security best practices

### Deliverables
- ✅ Agent bridge API functional
- ✅ Sample agent working
- ✅ Documentation complete
- ✅ Git tag: `agent-bridge-alpha`

### Validation
- [ ] Agent can query events via API
- [ ] Agent can write summaries to Firestore
- [ ] Agent actions appear in WAL
- [ ] No security issues

---

## Release Criteria (v0 Production)

Before declaring v0 production-ready, verify:

### Functionality
- [ ] Users can sign up and sign in
- [ ] Users can set and update research seeds
- [ ] Daily collector runs successfully
- [ ] Digests appear in UI after collection
- [ ] Users can save/mute papers
- [ ] All feedback is tracked

### Security
- [ ] Firestore security rules enforced
- [ ] No unauthorized access to user data
- [ ] No client writes to papers collection
- [ ] OIDC authentication working for scheduler
- [ ] Service accounts follow least privilege
- [ ] No secrets in source control

### Performance
- [ ] Collector completes in < 5 minutes for 100 users
- [ ] UI loads in < 2 seconds
- [ ] API responses < 500ms (p95)
- [ ] Cost < $20/month at 100 users

### Reliability
- [ ] WAL events consistently land in BigQuery
- [ ] System can rebuild from BigQuery
- [ ] Error handling for all external APIs
- [ ] Graceful degradation if API unavailable
- [ ] Monitoring and alerting configured

### Documentation
- [ ] README with setup instructions
- [ ] Environment variables documented
- [ ] API endpoints documented
- [ ] Architecture diagrams
- [ ] Contributing guidelines

---

## Post-v0 Roadmap

### v1: Event-Sourced Architecture
- [ ] Flip to `USE_TASKS_FANOUT=true`
- [ ] Migrate to event-sourced reads
- [ ] Implement CQRS pattern
- [ ] Add event replay UI

### v2: Advanced Features
- [ ] User tiers and payments (Stripe)
- [ ] Advanced ranking with ML models
- [ ] Collaborative filtering
- [ ] Paper recommendations
- [ ] Email digests
- [ ] Slack/Discord integrations
- [ ] API for third-party integrations

### v3: Agentic Intelligence
- [ ] Auto-summarization
- [ ] Research trend detection
- [ ] Citation network analysis
- [ ] Personalized insights
- [ ] Automated annotations

---

## Development Workflow

### Daily Standup Questions
1. What did we complete yesterday?
2. What are we working on today?
3. Any blockers or dependencies?

### Definition of Done
A task is complete when:
- [ ] Code is written and tested locally
- [ ] Tests pass (if applicable)
- [ ] Code is committed with clear message
- [ ] Documentation is updated
- [ ] Deployed to staging (if applicable)
- [ ] Validated against acceptance criteria

### Git Workflow
1. Work on feature/task branch
2. Commit atomically with clear messages
3. Tag milestones when phase complete
4. Push to remote
5. Deploy to staging
6. Validate, then deploy to production

---

## Notes

- **Estimated Timeline**: 5-6 weeks for v0 completion
- **Parallelization**: Phases 0-1 must be sequential; some tasks in 2-3 can be parallel
- **Cost Control**: Stay within GCP free tier during development
- **Testing**: Manual testing acceptable for v0; add automated tests in v1

---

**Last Updated**: 2025-11-06
**Next Review**: After Phase 1 completion
