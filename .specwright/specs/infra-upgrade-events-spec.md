---
version: "1.0"
tier: B
title: Infrastructure Upgrade - Event Ledger & Fan-Out Architecture
owner: benthepsychologist
goal: Implement WAL integrity verification, replay capability, and distributed fan-out architecture
labels: [infrastructure, event-sourcing, scalability, phases-4-6]
orchestrator_contract: "standard"
repo:
  working_branch: "feat/infra-upgrade-events"
---

# Infrastructure Upgrade: Event Ledger & Fan-Out Architecture

## Objective

Upgrade Research Watcher infrastructure from synchronous v0 architecture to distributed, event-sourced v1 architecture. This includes:
1. **Phase 4**: Event Ledger & Consumer Stub - WAL integrity verification and replay capability
2. **Phase 5**: v1 Fan-Out Readiness - Cloud Tasks distributed processing
3. **Phase 6**: Agentic Extensions - AI/automation event reactors

This spec covers infrastructure evolution only. Enhanced Discovery features are tracked separately.

## Acceptance Criteria

- [ ] BigQuery WAL verified as source of truth
- [ ] Replay script can rebuild Firestore from WAL events
- [ ] Search event tracking integrated (v1 schema extended)
- [ ] Cloud Tasks fan-out architecture implemented
- [ ] Feature flags control v0 → v1 flip
- [ ] Agent bridge API functional
- [ ] All tests passing (unit + integration)
- [ ] Cost < $25/month at 100 users + 200 searches/day
- [ ] Documentation complete

## Context

### Background

**Current State (v0 - Phase 3 Complete):**
- Synchronous collector runs daily via Cloud Scheduler
- `/api/collect/run` processes all users sequentially
- Dual-write: Firestore (SoT) + Pub/Sub (WAL)
- Interactive search functional but not tracked in WAL
- BigQuery sink receives WAL events but not used as source
- No replay capability from WAL
- No distributed processing architecture

**Why This Work is Needed:**
1. **Scalability**: Sequential processing won't scale beyond ~100 users
2. **Resilience**: No recovery mechanism if Firestore state corrupted
3. **Event Intelligence**: Search events not captured for analytics/agents
4. **Agentic Future**: Need stable event stream for AI/automation agents
5. **Cost Efficiency**: Fan-out enables parallel processing with better resource utilization

### Constraints

- Must maintain backward compatibility during v0 → v1 transition
- No downtime during migration
- Feature flags must allow instant rollback
- Cannot modify core collection/scoring logic (tested in Phase 2)
- Must stay within GCP free tier + $25/month budget

## Plan

### Phase 4: Event Ledger & Consumer Stub

**Goal:** Verify WAL integrity and implement replay capability

**Tasks:**
1. **Extend WAL Schema for Search Events**
   - Add `search.executed` event type
   - Fields: `{ uid, query, resultsCount, durationMs, ts }`
   - Purpose: Track search usage for analytics and rate limit monitoring
   - Update event builder in `app/services/collector.py`

2. **Create BigQuery Validation Queries**
   - Count events by type (digest vs search)
   - Check for gaps in runIds
   - Verify provenance flags integrity
   - Daily search volume by user
   - Total S2 API usage tracking
   - Save as `scripts/bq_validation_queries.sql`

3. **Implement Replay Script**
   - Script: `scripts/replay_from_bq.py`
   - Read events from BigQuery (date range filter)
   - Rebuild Firestore collections: users, seeds, papers, digests
   - Support dry-run mode (no writes)
   - Progress reporting with tqdm
   - Idempotency: use event IDs to prevent duplicates
   - Compare replayed state with production

4. **Create Consumer Stub Endpoint**
   - Endpoint: `/_wal/push` (OIDC-secured)
   - Accept Pub/Sub push notifications
   - Parse WAL event from message data
   - Idempotent upsert to Firestore (by event ID)
   - Log processing status and errors
   - Purpose: Validate event-sourced read path

5. **Test Replay on Staging**
   - Export last 7 days of events from BigQuery
   - Clear staging Firestore (separate project/collection)
   - Run replay script
   - Compare counts: users, seeds, papers, digests
   - Validate sample paper data matches production

6. **Documentation**
   - Create `docs/event-sourcing.md`
   - Document WAL schema (v1 + search events)
   - Explain idempotency keys (runId, eventId)
   - Consumer pattern with examples
   - Replay procedure

**Deliverables:**
- ✅ Search events tracked in BigQuery WAL
- ✅ Replay script functional and tested
- ✅ Consumer stub validates event processing
- ✅ System can rebuild from WAL
- ✅ Git tag: `v0-ledger-verified`

**Files to Touch:**
- `app/api/search.py` - Add WAL event publishing
- `app/services/collector.py` - Search event builder
- `scripts/replay_from_bq.py` - NEW
- `scripts/bq_validation_queries.sql` - NEW
- `app/api/wal_consumer.py` - NEW (consumer blueprint)
- `docs/event-sourcing.md` - NEW

---

### Phase 5: v1 Fan-Out Readiness

**Goal:** Implement distributed processing with Cloud Tasks

**Tasks:**
1. **Create Cloud Tasks Queue**
   - Queue name: `user-collections`
   - Rate limits: 10 tasks/second
   - Retry policy: max 3 attempts, exponential backoff
   - Max concurrent dispatches: 50
   - Service account: `rw-api@research-watcher.iam.gserviceaccount.com`

2. **Implement Queue Endpoint**
   - Endpoint: `/api/collect/queue` (OIDC-secured)
   - Fetch all users with seeds from Firestore
   - For each user: enqueue Cloud Task
   - Task payload: `{ uid, runId, seeds }`
   - Task target: `/api/collect/worker`
   - Return: `{ status, usersQueued, runId }`
   - Feature flag: `USE_TASKS_FANOUT`

3. **Implement Worker Endpoint**
   - Endpoint: `/api/collect/worker` (OIDC-secured)
   - Accept: `{ uid, runId, seeds }`
   - Process single user collection (reuse Phase 2 logic)
   - Upsert papers and digest to Firestore
   - Publish WAL event to Pub/Sub
   - Return: `{ uid, papersCollected, digestCreated }`
   - Idempotency: check runId, skip if already processed

4. **Add Feature Flags**
   - `USE_TASKS_FANOUT=false` - Enable distributed processing
   - `USE_PUBSUB_AS_SOURCE=false` - (Future) Read from Pub/Sub instead of Firestore
   - `ENABLE_SEARCH_CACHING=false` - (Future) Cache search results
   - Store in Cloud Run environment variables
   - Document in `.env.example`

5. **Create IAM Roles**
   - Grant `rw-api` service account:
     - `roles/cloudtasks.enqueuer` - Enqueue tasks
     - `roles/run.invoker` - Invoke worker endpoint
   - Grant Cloud Tasks service account:
     - `roles/run.invoker` - Invoke `/api/collect/worker`

6. **Add Monitoring**
   - Log Aggregation Metrics:
     - Task enqueue count per run
     - Task success/failure rates
     - Worker processing duration (p50, p95, p99)
     - Total papers collected per run
   - Alerts:
     - Cloud Tasks queue backlog > 100 tasks for 5 minutes
     - Worker error rate > 5% over 15 minutes
     - S2 API rate > 100 req/5min (quota warning)

7. **Migration Plan**
   - Create `docs/v0-to-v1-migration.md`
   - Steps to flip `USE_TASKS_FANOUT=true`
   - Rollback procedure (flip back to false)
   - Testing checklist (staging → production)
   - Comparison: v0 vs v1 results
   - Cost analysis before/after

8. **Test in Staging**
   - Enable `USE_TASKS_FANOUT=true` on staging service
   - Trigger `/api/collect/queue` manually
   - Verify all users processed in parallel
   - Check WAL events in BigQuery
   - Compare results with v0 baseline
   - Measure: total duration, cost, error rate

**Deliverables:**
- ✅ Cloud Tasks queue configured
- ✅ Fan-out architecture implemented
- ✅ Worker endpoint functional
- ✅ Feature flags control v0/v1 mode
- ✅ Monitoring and alerting in place
- ✅ Migration plan documented
- ✅ Staging validation complete
- ✅ Git tag: `v1-ready-fanout`

**Files to Touch:**
- `app/api/collector.py` - Add `/queue` and `/worker` endpoints
- `.env.example` - Document feature flags
- `docs/v0-to-v1-migration.md` - NEW
- `scripts/create_cloud_tasks_queue.sh` - NEW
- `scripts/test_fanout.sh` - NEW

---

### Phase 6: Agentic Extensions

**Goal:** Enable AI/automation agents to react to WAL events

**Tasks:**
1. **Create BigQuery Views for Agents**
   ```sql
   -- High-score papers (existing digest.created events)
   CREATE VIEW research_wal.vw_recent_highscore AS
   SELECT * FROM research_wal.events
   WHERE type = 'digest.created'
     AND JSON_EXTRACT_SCALAR(items, '$[0].score') > 70
     AND DATE(ts) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY);

   -- Trending search topics
   CREATE VIEW research_wal.vw_trending_searches AS
   SELECT
     JSON_EXTRACT_SCALAR(data, '$.query') as query,
     COUNT(*) as search_count,
     COUNT(DISTINCT uid) as unique_users,
     AVG(CAST(JSON_EXTRACT_SCALAR(data, '$.resultsCount') AS INT64)) as avg_results
   FROM research_wal.events
   WHERE type = 'search.executed'
     AND DATE(ts) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
   GROUP BY query
   ORDER BY search_count DESC
   LIMIT 50;

   -- User search patterns (for quota planning)
   CREATE VIEW research_wal.vw_user_search_activity AS
   SELECT
     uid,
     DATE(ts) as date,
     COUNT(*) as searches_per_day,
     SUM(CAST(JSON_EXTRACT_SCALAR(data, '$.resultsCount') AS INT64)) as total_results
   FROM research_wal.events
   WHERE type = 'search.executed'
   GROUP BY uid, date
   ORDER BY date DESC, searches_per_day DESC;
   ```

2. **Create Agent Bridge API**
   - Blueprint: `app/api/agents.py`
   - Endpoints:
     - `GET /api/events` - Query recent WAL events (service account auth)
     - `GET /api/analytics/trending` - Expose trending topics
     - `POST /api/actions` - Agent-triggered actions (summarize, notify)
   - Authentication: Service account OIDC tokens only
   - Rate limiting: 60 req/min per agent

3. **Create Agent Service Account**
   - Account: `agents@research-watcher.iam.gserviceaccount.com`
   - Roles:
     - `roles/bigquery.dataViewer` - Read WAL events
     - `roles/firestore.viewer` - Read papers (for summarization)
     - Custom role: `agentWriter` with limited Firestore write permissions
       - Can write to: `summaries/`, `notifications/`, `insights/`
       - Cannot write to: `users/`, `papers/`, `digests/`, `seeds/`

4. **Implement Sample Summarization Agent**
   - Script: `agents/summarizer.py`
   - Poll: `vw_recent_highscore` every 4 hours
   - For each paper > 70 score without summary:
     - Fetch full abstract from Firestore
     - Generate 3-sentence summary using Gemini API
     - Store in `summaries/{paperId}` with provenance
     - Log agent action to WAL
   - Idempotency: skip if summary exists
   - Cost: ~$0.01 per 100 summaries

5. **Implement Trend Detection Agent (Optional)**
   - Script: `agents/trend_detector.py`
   - Poll: `vw_trending_searches` daily
   - Identify: queries with >3 unique users in last 7 days
   - Create: `insights/trending_topics` document
   - Action: Notify admin via email if emerging trend detected
   - Purpose: Discover new research areas for seed suggestions

6. **Documentation**
   - Create `docs/agents.md`
   - Agent authentication setup (service account)
   - Available BigQuery views and their schemas
   - Agent API reference
   - Example agents with code
   - Security best practices
   - Cost considerations

**Deliverables:**
- ✅ BigQuery views for agent triggers
- ✅ Agent bridge API functional
- ✅ Service account with least privilege
- ✅ Sample summarization agent working
- ✅ Agent actions logged to WAL
- ✅ Documentation complete
- ✅ Git tag: `agent-bridge-alpha`

**Files to Touch:**
- `app/api/agents.py` - NEW (agent bridge blueprint)
- `agents/summarizer.py` - NEW
- `agents/trend_detector.py` - NEW
- `scripts/create_agent_sa.sh` - NEW
- `scripts/bq_create_views.sql` - NEW
- `docs/agents.md` - NEW

## Models & Tools

**Primary Tools:**
- `gcloud` - GCP infrastructure management
- `bq` - BigQuery CLI for queries and table operations
- `pytest` - Python testing framework
- `bash` - Shell scripts for automation
- `gsutil` - Cloud Storage operations (if needed)

**Python Libraries:**
- `google-cloud-bigquery` - BigQuery Python client
- `google-cloud-tasks` - Cloud Tasks Python client
- `tqdm` - Progress bars for replay script
- `google-generativeai` - Gemini API for summarization (Phase 6)

**GCP Services:**
- BigQuery - WAL storage and analytics
- Cloud Tasks - Distributed job queue
- Pub/Sub - Event streaming
- Cloud Run - Serverless API hosting
- Firestore - Document database

**Models:**
- `claude-sonnet` - Main implementation and code generation
- `gemini-1.5-flash` - Agent summarization (Phase 6)

## Repository

**Branch:** `feat/infra-upgrade-events`

**Merge Strategy:** squash

**Working Directory:** `/home/user/research-watcher`

---

## Implementation Notes

### Testing Strategy

**Phase 4 Tests:**
- Unit tests for event schema validation
- Integration tests for replay script
- End-to-end test: BigQuery → Firestore replay
- Comparison tests: replayed state vs production

**Phase 5 Tests:**
- Unit tests for queue/worker endpoints
- Integration tests with Cloud Tasks
- Load tests: 100 concurrent users
- Feature flag toggling tests
- Rollback validation

**Phase 6 Tests:**
- Agent authentication tests
- BigQuery view query tests
- Summarization agent dry-run
- Cost estimation tests

### Cost Considerations

**Current (v0):**
- Cloud Run: ~$5/month (100 users, 1 run/day)
- Firestore: ~$2/month (reads + writes)
- Pub/Sub: Free tier
- BigQuery: ~$1/month (WAL storage + queries)
- Total: ~$8/month

**After Upgrade (v1):**
- Cloud Run: ~$8/month (parallel workers)
- Cloud Tasks: ~$2/month (100 users × 30 days)
- Firestore: ~$3/month (increased reads for replay)
- BigQuery: ~$3/month (views + analytics queries)
- Gemini API: ~$5/month (summarization, 100 papers/day)
- Total: ~$21/month

**Budget:** $25/month ✅

### Security Considerations

1. **Service Account Permissions:**
   - Principle of least privilege
   - Separate SAs for: API, agents, tasks, scheduler
   - No user credentials in code

2. **OIDC Authentication:**
   - All internal endpoints use OIDC
   - No API keys in environment variables
   - Token validation on every request

3. **Firestore Security:**
   - Agent SA cannot modify user data
   - Custom role limits write scope
   - Audit logging enabled

4. **BigQuery Access:**
   - Agents read-only access to views
   - No direct table access
   - Query logs for monitoring

### Rollback Plan

If v1 fan-out causes issues:

1. **Immediate:** Flip `USE_TASKS_FANOUT=false` (via Cloud Run env var)
2. **Verify:** Next collector run uses v0 synchronous path
3. **Monitor:** Check Firestore writes, WAL events, error logs
4. **Investigation:** Review Cloud Tasks queue, worker logs
5. **Fix:** Address root cause in staging before re-enabling

Rollback time: < 2 minutes (env var update)

### Migration Checklist

Before flipping to v1:
- [ ] Cloud Tasks queue created and configured
- [ ] Worker endpoint tested in staging
- [ ] Feature flag tested (toggle v0 ↔ v1)
- [ ] Monitoring dashboards configured
- [ ] Alert policies active
- [ ] Cost budget alerts set
- [ ] Team notified of migration window
- [ ] Rollback procedure documented and tested

### Future Enhancements (Post-v1)

**Event-Sourced Reads (v2):**
- Flip `USE_PUBSUB_AS_SOURCE=true`
- Read all data from Pub/Sub stream
- Firestore becomes cache/projection
- CQRS pattern fully implemented

**Advanced Agents (v2):**
- Citation network builder
- Personalized ranking models
- Cross-reference detection
- Research timeline generation

**Search Optimization (v1.5):**
- Enable `ENABLE_SEARCH_CACHING=true`
- Cache common queries in Firestore
- TTL: 4 hours
- Reduces S2 API costs by ~60%