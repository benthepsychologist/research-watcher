🧭 AgentsWay Implementation Plan (AIP 1.0)

Project: Research Watcher
Spec Version: 1.0 (2025-11-05)
Implementation Phase: v0 → v1-ready
Mode: Dual-write (event-driven DB SoT + Pub/Sub WAL)

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
	5.	Deploy Firebase Hosting stub: index.html, privacy.html, etc.
	6.	Add env vars to Secrets Manager / Cloud Run (see spec).
	7.	Create OIDC service account for Cloud Scheduler; grant invoker role to Cloud Run.
	8.	Commit and tag as v0-bootstrap.

✅ Output: Firebase + GCP infrastructure online; Cloud Run service placeholder deploys; Hosting rewrite verified.

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

📥 Phase 2 – Collector + Dual-Write (WAL Emission)

Goal: Implement daily collector pipeline with FireStore writes + Pub/Sub publish.

Steps
	1.	Build clients for OpenAlex, Semantic Scholar, Crossref, arXiv (services/).
	2.	Implement collect_and_rank() → fetch, dedupe, score.
	3.	Implement /api/collect/run:
	•	Verify OIDC token from Scheduler SA.
	•	For each user with seeds: fetch papers → upsert Firestore (papers/, digests/{uid}/latest).
	•	Publish WAL to Pub/Sub (rw-wal).
	4. 	Create daily Cloud Scheduler job (09:00 BA time).
	5.	Confirm BigQuery sink populates research_wal.events.
	6.	Enforce users.quota.runsPerDay.
	7.	Commit and tag v0-collector-dual-write.

✅ Output: End-to-end daily collector run writing Firestore and Pub/Sub WAL events.

⸻

📊 Phase 3 – Frontend and User Flow

Goal: Minimal web UI for sign-in, seed entry, and digest view.

Steps
	1.	Firebase Hosting public/ directory ready.
	2.	Auth flow: Google or email login → call /api/users/sync.
	3.	Simple HTML/JS for:
	•	Seed management (/api/seeds)
	•	Digest viewer (/api/digest/latest)
	•	Feedback (/api/feedback)
	4.	Add CORS + JWT headers handling.
	5.	Verify Hosting rewrite to Cloud Run:

"rewrites": [
  { "source": "/api/**", "run": { "serviceId": "rw-api", "region": "us-central1" } },
  { "source": "**", "destination": "/index.html" }
]

	6.	Deploy Hosting v0 to Firebase.
	7.	Commit and tag v0-frontend.

✅ Output: Usable public web app with Auth and functional backend calls.

⸻

🧩 Phase 4 – Event Ledger & Consumer Stub

Goal: Verify WAL integrity and prepare for event-sourced flip.

Steps
	1.	Define event schema (v1) in code and BigQuery table.
	2.	Create sample consumer endpoint /_wal/push (secured OIDC) → parse event → idempotent upsert.
	3.	Verify Pub/Sub → consumer → Firestore works on test topic.
	4.	Query BigQuery for recent events:

SELECT type, COUNT(*) FROM research_wal.events
WHERE DATE(_PARTITIONTIME)=CURRENT_DATE()
GROUP BY type;

	5.	Add replay script (BigQuery → Firestore) for full restore.
	6.	Commit and tag v0-ledger-verified.

✅ Output: Durable WAL in BigQuery; consumer stub exists; system replayable.

⸻

⚡ Phase 5 – v1 Fan-Out Readiness

Goal: Lay the plumbing for Cloud Tasks / Pub/Sub worker architecture.

Steps
	1.	Implement /api/collect/queue → enqueue per-user tasks (stubbed in v0).
	2.	Implement /api/collect/worker → process single user by UID.
	3.	Feature flags:

USE_PUBSUB_AS_SOURCE=false
USE_TASKS_FANOUT=false

	4.	Create IAM roles for Tasks and Worker service accounts.
	5.	Add monitoring metrics (Pub/Sub backlog, Firestore writes).
	6.	Commit and tag v1-ready-fanout.

✅ Output: All hooks exist to move from synchronous collector to distributed fan-out.

⸻

🧠 Phase 6 – Agentic Execution Extension (optional)

Goal: Enable AI/automation agents to react to WAL events.

Steps
	1.	Create BigQuery view vw_recent_highscore for score>3.5.
	2.	Agent subscribes via Pub/Sub filter or polls view daily.
	3.	Add Agent Bridge API (/api/events, /api/actions).
	4.	Use service account with least privilege.
	5.	Validate end-to-end agent loop: detect → summarize → store summary to Firestore.
	6.	Commit and tag agent-bridge-alpha.

✅ Output: Extensible agent hooks for summarization, notifications, and analysis.

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
