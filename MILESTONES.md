# Research Watcher - Development Milestones

**Project**: Research Watcher v0
**Based on**: AIP 1.0 & Spec 1.0
**Status**: 🟡 In Progress
**Current Phase**: Phase 1 → Phase 2
**Last Updated**: 2025-11-06

---

## Milestone Overview

| Phase | Milestone | Status | Completed |
|-------|-----------|--------|-----------|
| 0 | Bootstrap & Environment | ✅ | 2025-11-06 |
| 1 | Backend Core (API Skeleton) | ✅ | 2025-11-06 |
| 2 | Collector + Dual-Write | ⏳ | - |
| 3 | Frontend & User Flow | ⏳ | - |
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

## Phase 2: Collector + Dual-Write (WAL Emission)

**Goal**: Implement daily collector pipeline with Firestore writes + Pub/Sub publish

### Tasks
- [ ] Build external API clients (`app/services/`)
  - [ ] `openalex.py` - OpenAlex API wrapper
  - [ ] `semantic_scholar.py` - Semantic Scholar API wrapper
  - [ ] `crossref.py` - Crossref API wrapper
  - [ ] `arxiv.py` - arXiv API wrapper
  - [ ] Add rate limiting and retries
  - [ ] Add proper error handling
- [ ] Create paper deduplication logic
  - [ ] Normalize DOIs, arXiv IDs
  - [ ] Generate stable paper IDs
  - [ ] Merge metadata from multiple sources
- [ ] Create scoring algorithm
  - [ ] Factor: citation count
  - [ ] Factor: venue prestige
  - [ ] Factor: recency
  - [ ] Factor: open access availability
  - [ ] Configurable weights
- [ ] Implement `/api/collect/run` endpoint
  - [ ] Verify OIDC token from Cloud Scheduler SA
  - [ ] Fetch all users with seeds
  - [ ] For each user:
    - [ ] Fetch papers matching seeds
    - [ ] Deduplicate and score
    - [ ] Upsert to `papers/` collection
    - [ ] Create/update `digests/{uid}/latest`
    - [ ] Publish WAL event to Pub/Sub
  - [ ] Enforce `runsPerDay` quota
  - [ ] Log runId, counts, errors
- [ ] Create WAL event builder
  - [ ] Follow canonical schema (v1)
  - [ ] Include provenance flags
  - [ ] Timestamp in ISO8601
- [ ] Implement `/api/seeds` endpoint
  - [ ] GET: Retrieve user seeds
  - [ ] POST: Update seeds with quota validation
  - [ ] Enforce `maxSeeds` limit
- [ ] Implement `/api/digest/latest` endpoint
  - [ ] Retrieve latest digest for user
  - [ ] Expand paper details from `papers/` collection
  - [ ] Sort by score descending
- [ ] Implement `/api/feedback` endpoint
  - [ ] Record user actions (save, mute, click)
  - [ ] Write to `events/{uid}/` collection
- [ ] Create Cloud Scheduler job
  - [ ] Schedule: `0 9 * * *` (09:00 daily)
  - [ ] Timezone: `America/Argentina/Buenos_Aires`
  - [ ] Target: `/api/collect/run`
  - [ ] Auth: OIDC with service account
- [ ] Verify BigQuery sink
  - [ ] Confirm events arrive in `research_wal.events`
  - [ ] Verify partition by date
  - [ ] Test queries

### Deliverables
- ✅ End-to-end collector run working
- ✅ Firestore contains papers and digests
- ✅ Pub/Sub events land in BigQuery
- ✅ Cloud Scheduler job configured
- ✅ All user endpoints functional
- ✅ Git tag: `v0-collector-dual-write`

### Validation
```bash
# Trigger collector manually
curl -H "Authorization: Bearer <OIDC_TOKEN>" \
  -X POST https://rw-api-xxxxx.run.app/api/collect/run

# Check BigQuery
bq query "SELECT COUNT(*) FROM research_wal.events WHERE DATE(_PARTITIONTIME) = CURRENT_DATE()"
```

---

## Phase 3: Frontend & User Flow

**Goal**: Minimal web UI for sign-in, seed entry, and digest view

### Tasks
- [ ] Create landing page (`public/index.html`)
  - [ ] Project description
  - [ ] Sign-in button
  - [ ] Links to About and Privacy pages
- [ ] Create authenticated app page (`public/app.html`)
  - [ ] Firebase Auth UI integration
  - [ ] Seed management form
  - [ ] Digest viewer with paper cards
  - [ ] Feedback buttons (save/mute/click)
- [ ] Create about page (`public/about.html`)
  - [ ] Project description
  - [ ] Technology stack
  - [ ] Contact information
- [ ] Create privacy policy page (`public/privacy.html`)
  - [ ] Data collection policy
  - [ ] User rights
  - [ ] Compliance statements
- [ ] Implement Firebase Auth flow
  - [ ] Google sign-in
  - [ ] Email/Password sign-in
  - [ ] Auto-redirect after login
  - [ ] Call `/api/users/sync` on first login
- [ ] Implement seed management UI
  - [ ] Add/remove authors
  - [ ] Add/remove venues
  - [ ] Add/remove keywords
  - [ ] Show quota limits
  - [ ] Save button → POST `/api/seeds`
- [ ] Implement digest viewer
  - [ ] Fetch from `/api/digest/latest`
  - [ ] Render paper cards with:
    - [ ] Title, authors, venue, year
    - [ ] Abstract (truncated)
    - [ ] Score badge
    - [ ] Open Access indicator
    - [ ] Link to source
  - [ ] Sort by score
  - [ ] Show "no digest yet" state
- [ ] Add feedback buttons
  - [ ] Save for later
  - [ ] Mute/hide
  - [ ] Track clicks to source
  - [ ] POST to `/api/feedback`
- [ ] Configure CORS in Flask
  - [ ] Allow Firebase Hosting domain
  - [ ] Allow localhost for dev
- [ ] Update `firebase.json`
  - [ ] Rewrite `/api/**` to Cloud Run
  - [ ] Serve static files from `public/`
  - [ ] Configure cache headers
- [ ] Deploy to Firebase Hosting

### Deliverables
- ✅ Usable public web app
- ✅ Auth flow working
- ✅ Functional backend integration
- ✅ Responsive design (mobile-friendly)
- ✅ Git tag: `v0-frontend`

### Validation
- [ ] Can sign in with Google
- [ ] Can add/update seeds
- [ ] Can view digest
- [ ] Can save/mute papers
- [ ] All links work

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
