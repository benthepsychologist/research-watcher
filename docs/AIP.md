🧭 AgentsWay Implementation Plan (AIP 1.1)

Project: Research Watcher
Spec Version: 1.0 (2025-11-05)
Implementation Phase: v0 → v1-ready
Mode: Dual-write (event-driven DB SoT + Pub/Sub WAL)
Last Updated: 2025-11-08 (Phase 2 complete, Phase 3 expanded)

⸻

⚙️ Phase 0 – Bootstrap & Environment

Goal: Stand up base Firebase + GCP project scaffolding.

Steps
	1.	Create Firebase Project → enable Firestore (Native), Auth (Google + Email).
	2.	Enable APIs: Cloud Run, Pub/Sub, BigQuery, Cloud Scheduler.
	3.	Clone repo template and structure as per spec (tree ready).
	4.	Create GCP resources:
	•	Topic rw-wal (Pub/Sub)
	•	Dataset research_wal, table events (BigQuery)
	•	Sink from topic → table
	5.	Deploy Firebase Hosting stub: index.html, privacy.html, etc. (Note: Deferred to Phase 3 - requires Firebase CLI installation)
	6.	Add env vars to Secrets Manager / Cloud Run (see spec).
	7.	Create OIDC service account for Cloud Scheduler; grant invoker role to Cloud Run.
	8.	Commit and tag as v0-bootstrap.

✅ Output: Firebase + GCP infrastructure online; Cloud Run service placeholder deploys; Hosting configuration ready (deployment deferred to Phase 3).

⸻

🧱 Phase 1 – Backend Core (API Skeleton)

Goal: Deploy Flask API on Cloud Run with auth, routing, and blueprints.

Steps
	1.	Scaffold app/__init__.py with App Factory and Firebase Admin init.
	2.	Add JWT validator (utils/auth.py) for Firebase ID tokens.
	3.	Create Blueprints: collector, digest, feedback, seeds, users.
	4.	Implement @login_required decorator and apply to protected routes.
	5.	Verify /api/users/sync works (idempotent profile creation).
	6.	Add .env, Dockerfile, and requirements.txt.
	7.	Deploy to Cloud Run (rw-api service).
	8.	Validate with curl /api/users/sync using test token.
	9.	Commit and tag v0-api-skeleton.

✅ Output: Functional secured API endpoints with Auth and Firestore connection.

⸻

📥 Phase 2 – Collector + Dual-Write (WAL Emission) ✅ COMPLETE

Goal: Implement daily collector pipeline with Firestore writes + Pub/Sub publish.

Steps
	1.	✅ Build clients for OpenAlex, Semantic Scholar, arXiv (services/).
		•	Note: Dropped Crossref in favor of S2 semantic intelligence
		•	Using own S2 API key during limited alpha
	2.	✅ Implement collect_and_rank() → fetch, dedupe, score.
		•	Multi-source deduplication (DOI/arXiv ID/title hash)
		•	Scoring: citations (30pts) + recency (25pts) + venue (20pts) + OA (15pts) + abstract (10pts)
	3.	✅ Implement /api/collect/run:
		•	Verify OIDC token from Scheduler SA
		•	For each user with seeds: fetch papers → upsert Firestore (papers/, digests/{uid}_latest)
		•	Publish WAL to Pub/Sub (rw-wal)
		•	Document ID sanitization (replace / with _)
	4. 	✅ Cloud Scheduler job already configured (09:00 BA time).
	5.	✅ Confirm BigQuery sink populates research_wal.events.
	6.	⏭️ Quota enforcement deferred to Phase 3.
	7.	✅ Commit and tag v0-collector-dual-write.

✅ Output: End-to-end daily collector run writing Firestore and Pub/Sub WAL events.
📊 Test Results: 1 user, 49 papers, 1 digest, 0 errors, WAL in BigQuery verified.

⸻

📊 Phase 3 – Frontend and User Flow (EXPANDED v1.1)

Goal: Interactive web UI with sign-in, seed management, digest view, AND real-time search.

Architecture: HTMX-powered SPA with Firebase Auth

Steps

Backend (Interactive Search):
	1.	Implement /api/search endpoint (GET, @login_required):
		•	Query params: ?q={query}&days_back={7}&max_results={20}
		•	Reuse collect_and_rank() logic from Phase 2
		•	Return JSON: { papers: [...], query: "...", count: N }
		•	Client-side rate limiting (1 req/sec for S2 compliance)
		•	Track search events in Firestore events/{uid}/searches

Frontend (HTMX + Firebase Auth):
	2.	Create app.html (authenticated SPA):
		•	HTMX 1.9+ for dynamic content loading
		•	Tailwind CSS (CDN) for styling
		•	Firebase Auth UI widget (Google + Email)
		•	Navigation: Digest | Search | Seeds | Saved

	3.	Implement page components (HTMX partials):
		•	Digest View: Load /api/digest/latest on page load
		•	Interactive Search: Real-time search form → /api/search
		•	Seed Management: CRUD interface for /api/seeds
		•	Saved Papers: User's saved/muted papers from feedback
		•	Paper Cards: Reusable template with title, authors, score, abstract

	4.	Auth flow:
		•	Landing page (index.html) → Sign In button
		•	Firebase Auth popup → Get ID token
		•	Store token in localStorage
		•	Redirect to app.html
		•	All HTMX requests include Authorization: Bearer {token}
		•	Call /api/users/sync on first login

	5.	Add CORS configuration to Flask:
		•	Allow Firebase Hosting domain
		•	Allow localhost:5000 for dev
		•	Credentials: true for auth headers

	6.	Configure Firebase Hosting rewrites:

{
  "hosting": {
    "public": "public",
    "rewrites": [
      { "source": "/api/**", "run": { "serviceId": "rw-api", "region": "us-central1" } },
      { "source": "**", "destination": "/index.html" }
    ]
  }
}

	7.	Deploy to Firebase Hosting:
		•	firebase deploy --only hosting
		•	Verify /app.html accessible
		•	Test auth flow end-to-end

	8.	Quota enforcement (deferred from Phase 2):
		•	Implement maxSeeds validation in /api/seeds POST
		•	Add runsPerDay check in collector (prevent double-runs)
		•	Display quota limits in UI

	9.	Commit and tag v0-frontend.

✅ Output:
	•	Usable web app with Auth and backend integration
	•	Users can view daily digest
	•	Users can search papers interactively
	•	Users can manage seeds and save papers
	•	Quota limits enforced

🎯 Alpha User Experience:
	•	Sign in with Google
	•	Add 3 research seeds (LLMs, quantum computing, etc.)
	•	View daily digest (49 papers from automated collection)
	•	Search for "transformer models" → get real-time results
	•	Save interesting papers
	•	Return tomorrow for fresh digest

⸻

🧩 Phase 4 – Event Ledger & Consumer Stub

Goal: Verify WAL integrity and prepare for event-sourced flip.

Steps
	1.	✅ Event schema (v1) already defined in Phase 2 (digest.created).
	2.	Extend WAL schema for interactive search:
		•	Add event type: search.executed
		•	Fields: { query, resultsCount, durationMs, uid, ts }
		•	Purpose: Track search usage for analytics and S2 rate limit monitoring
	3.	Create sample consumer endpoint /_wal/push (secured OIDC) → parse event → idempotent upsert.
	4.	Verify Pub/Sub → consumer → Firestore works on test topic.
	5.	Query BigQuery for search analytics:

-- Daily search volume
SELECT DATE(ts) as date, COUNT(*) as searches
FROM research_wal.events
WHERE type = 'search.executed'
GROUP BY date
ORDER BY date DESC;

-- User search patterns (for quota planning)
SELECT uid, COUNT(*) as daily_searches
FROM research_wal.events
WHERE type = 'search.executed'
  AND DATE(ts) = CURRENT_DATE()
GROUP BY uid
ORDER BY daily_searches DESC;

	6.	Add replay script (BigQuery → Firestore) for full restore.
	7.	Analytics dashboard (optional):
		•	S2 API usage tracking
		•	Search vs digest usage ratio
		•	Most searched topics
	8.	Commit and tag v0-ledger-verified.

✅ Output:
	•	Durable WAL in BigQuery
	•	Consumer stub exists
	•	System replayable
	•	Search analytics tracked for quota planning

⸻

⚡ Phase 5 – v1 Fan-Out Readiness

Goal: Lay the plumbing for Cloud Tasks / Pub/Sub worker architecture.

Note: Interactive search remains synchronous (user-initiated), this phase only affects scheduled collection.

Steps
	1.	Implement /api/collect/queue → enqueue per-user tasks (stubbed in v0).
	2.	Implement /api/collect/worker → process single user by UID.
		•	Same logic as current /api/collect/run but for single user
		•	Returns individual stats
	3.	Feature flags:

USE_PUBSUB_AS_SOURCE=false  # Phase 6 event-sourcing
USE_TASKS_FANOUT=false      # This phase
ENABLE_SEARCH_CACHING=false # Future optimization

	4.	Create IAM roles for Tasks and Worker service accounts.
	5.	Add monitoring metrics:
		•	Pub/Sub backlog
		•	Firestore writes/sec
		•	S2 API rate (searches/sec) ← NEW for search tracking
		•	Cloud Tasks queue depth
	6.	Rate limiting strategy:
		•	Daily collector: Batch processing, 13 users sequential
		•	Interactive search: Per-user throttling (1 req/sec client-side)
		•	Combined: Monitor total S2 usage, alert if >100 req/5min
	7.	Commit and tag v1-ready-fanout.

✅ Output:
	•	All hooks exist to move from synchronous collector to distributed fan-out
	•	Search remains synchronous (appropriate for user-facing feature)
	•	Rate limiting monitoring in place

⸻

🧠 Phase 6 – Agentic Execution Extension (optional)

Goal: Enable AI/automation agents to react to WAL events.

Steps
	1.	Create BigQuery views for agent triggers:

-- High-score papers (existing)
CREATE VIEW vw_recent_highscore AS
SELECT * FROM research_wal.events
WHERE type = 'digest.created'
  AND score > 3.5
  AND DATE(ts) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY);

-- Trending topics (from search data)
CREATE VIEW vw_trending_searches AS
SELECT
  JSON_EXTRACT_SCALAR(items, '$.query') as query,
  COUNT(*) as search_count,
  COUNT(DISTINCT uid) as unique_users
FROM research_wal.events
WHERE type = 'search.executed'
  AND DATE(ts) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY query
ORDER BY search_count DESC
LIMIT 50;

	2.	Agent subscribes via Pub/Sub filter or polls views daily.
	3.	Add Agent Bridge API:
		•	GET /api/events → Query recent WAL events (service account auth)
		•	POST /api/actions → Agent-triggered actions (summarize, notify)
		•	GET /api/analytics/trending → Expose trending topics to agents
	4.	Use service account with least privilege (read-only BigQuery).
	5.	Example agents:
		•	Summarization Agent: Detect high-score papers → generate summaries
		•	Notification Agent: Email digests for saved papers
		•	Trend Detection Agent: Identify emerging research areas from searches
		•	Research Graph Agent: Build citation networks from collected papers
	6.	Commit and tag agent-bridge-alpha.

✅ Output:
	•	Extensible agent hooks for summarization, notifications, and analysis
	•	Search data feeds agent trend detection
	•	Bridge API for external automation

⸻

🔐 Governance & Ops Checklist

Area	Action
Security	Confirm all service accounts least privilege + OIDC only.
Cost control	Enable Budgets & Alerts in GCP; set Firestore quota.
Backups	BigQuery → GCS monthly export.
Monitoring	Cloud Logging → alert if collect fails > 1 day.
Docs	README.md includes setup instructions + env vars.


⸻

🧩 Phase States (Release Milestones)

Tag	Description
v0-bootstrap	Environment and infra ready
v0-api-skeleton	Auth and routes functional
v0-collector-dual-write	Firestore + WAL working
v0-frontend	Public UI operational
v0-ledger-verified	BigQuery sink validated
v1-ready-fanout	Queue architecture prepared
agent-bridge-alpha	Agentic layer prototype


⸻

🧾 Execution Principles
	•	Atomic commits: Each phase tags a working state; no multi-phase commits.
	•	Feature flags: Control fan-out and event-sourced modes without branching.
	•	Observability: Always log runId, uid, ts, count, and error summary.
	•	Idempotency everywhere: Stable keys + runId checks.
	•	Reversibility: Any phase can rebuild from BigQuery WAL.

⸻

✅ Deliverable Definition of Done (v0)
	•	Daily collector successfully runs via Scheduler and OIDC.
	•	Firestore contains papers and digests visible in UI.
	•	Pub/Sub events land in BigQuery ledger.
	•	Security rules enforced; no client writes to papers.
	•	Cost < $20/month at 100 users.

⸻

This AIP 1.0 maps one-to-one with your Spec 1.0 and provides an agent-friendly, reversible execution ladder from v0 to agentic v2.
