Research Watcher – Specification v1.0

Date: 2025-11-05
Status: Agreed
Version: 1.0

⸻

Overview

Research Watcher is a public-facing research-intelligence web application.
It delivers ranked, daily digests of academic papers based on user interests (authors, venues, keywords).

The initial release (v0) is free to use and requires Google or email sign-in.
The system collects metadata from open academic APIs once per day and maintains a durable event log for analytics and future event-sourced upgrades.

⸻

Design Principles

Pragmatic Scalability (v0 → v1)

Start with a synchronous, dual-write architecture (v0) for ease of build and debugging.
Preserve a smooth upgrade path to asynchronous fan-out (v1) using Cloud Tasks or Pub/Sub workers.

Dual-Write for Durability

Each collector run:
	1.	Writes directly to Firestore for immediate UI consistency.
	2.	Publishes a compact JSON Write-Ahead Log (WAL) event to Pub/Sub.

Pub/Sub events are automatically streamed to BigQuery, forming a permanent ledger and replayable history.

Secure by Default
	•	All user routes require Firebase Authentication.
	•	Firestore Security Rules enforce strict per-user access.
	•	/api/collect/run accepts only OIDC-signed requests from Cloud Scheduler.
	•	Secrets never enter source control; environment variables control configuration.

Modular Architecture

Flask Blueprints isolate domains (collector, digests, seeds, etc.).
Service layer modules wrap each external API (OpenAlex, Semantic Scholar, Crossref, arXiv).
This keeps the system testable, maintainable, and extendable.

Serverless-First Stack

Fully hosted on Google Cloud Platform / Firebase for scalability and zero-ops.

⸻

Architecture Summary

Layer	Service	Notes
Backend API	Flask (Python 3) on Cloud Run	REST JSON endpoints under /api
Auth	Firebase Auth (Google + Email)	Required for all user routes
Database	Firestore (Native Mode)	Primary app database
Hosting	Firebase Hosting	Serves static frontend, proxies /api/* to Cloud Run
Scheduler	Cloud Scheduler	Triggers collector daily (09:00 America/Argentina/Buenos_Aires)
Event Bus	Cloud Pub/Sub (rw-wal)	Receives WAL events
Ledger	BigQuery Sink (research_wal.events)	Permanent, queryable event log


⸻

Project Structure

/
├── app/
│   ├── __init__.py                # App factory + SDK initialization
│   ├── api/                       # Flask Blueprints
│   │   ├── collector.py           # /collect/run, /queue, /worker
│   │   ├── digest.py              # /digest/latest
│   │   ├── feedback.py            # /feedback
│   │   ├── seeds.py               # /seeds
│   │   └── users.py               # /users/sync
│   ├── services/                  # External API clients
│   │   ├── openalex.py
│   │   ├── semantic_scholar.py
│   │   ├── crossref.py
│   │   └── arxiv.py
│   └── utils/
│       └── auth.py                # @login_required decorator (Firebase JWT)
│
├── public/
│   ├── index.html                 # Landing page
│   ├── app.html                   # Authenticated UI (Phase 3)
│   ├── about.html                 # About page (Phase 3)
│   └── privacy.html               # Privacy policy (Phase 3)
│
├── tests/
│   ├── __init__.py
│   ├── test_phase0_infrastructure.py  # Phase 0 integration tests
│   └── README.md                      # Testing documentation
│
├── scripts/
│   ├── test_phase0_infrastructure.sh  # Bash integration tests
│   └── devserver.sh                   # Local development server
│
├── docs/
│   ├── AIP.md                     # Architecture & Implementation Plan
│   ├── spec.md                    # Technical specification
│   ├── SETUP.md                   # Infrastructure setup guide
│   ├── TESTING.md                 # Testing guide
│   ├── INFRASTRUCTURE_STATUS.md   # Current deployment status
│   └── PHASE0_ACCEPTANCE.md       # Phase 0 acceptance report
│
├── main.py                        # Entrypoint for Gunicorn/Cloud Run
├── requirements.txt               # Dependencies (pip)
├── pytest.ini                     # Pytest configuration
├── Dockerfile                     # Cloud Run container
├── .dockerignore                  # Docker build exclusions
├── firebase.json                  # Hosting + rewrite rules
├── firestore.rules                # Security rules
├── firestore.indexes.json         # Firestore indexes
├── MILESTONES.md                  # Development plan and milestones
├── .env                           # Local dev environment (git-ignored)
├── .env.example                   # Environment variable template
└── serviceAccountKey.json         # Local dev only (git-ignored)


⸻

Environment Variables

Key	Description	Default
GOOGLE_APPLICATION_CREDENTIALS	Path to local service key (dev only)	./serviceAccountKey.json
GOOGLE_CLOUD_PROJECT	Firebase/GCP project ID	(required)
S2_API_KEY	Optional Semantic Scholar API key	(optional)
OPENALEX_EMAIL	Contact email for OpenAlex	(required)
CROSSREF_MAILTO	Contact email for Crossref	(required)
USE_PUBSUB_AS_SOURCE	false (v0 dual-write) / true (v1 event-sourced)	false
USE_TASKS_FANOUT	Enable Cloud Tasks per-user fan-out	false
ENABLE_ANALYTICS	Controls Pub/Sub → BigQuery sink	true
FLASK_ENV	Flask environment (development/production)	development
PORT	Local development server port	3000
LOG_LEVEL	Logging verbosity (DEBUG/INFO/WARNING/ERROR)	INFO


⸻

Endpoints (Base URL: /api)

Method	Path	Description	Auth
POST	/api/users/sync	Create or verify user profile (idempotent)	✅
POST	/api/seeds	Update user research seeds; enforce quota	✅
GET	/api/digest/latest	Retrieve user’s latest digest	✅
POST	/api/collect/run	Trigger daily collector (Cloud Scheduler OIDC only)	🔒 Scheduler
POST	/api/collect/queue	Stub for v1 fan-out	🔒
POST	/api/collect/worker	Stub for v1 per-user worker	🔒
POST	/api/feedback	Record user action (save/mute/etc.)	✅


⸻

Data Model

users/{uid}

{
  "email": "user@example.com",
  "createdAt": "<Timestamp>",
  "tier": "free",
  "quota": { "runsPerDay": 3, "maxSeeds": 5 }
}

seeds/{uid}

{
  "authors": ["authorId1"],
  "venues": ["venueId1"],
  "keywords": ["machine learning"],
  "papers": ["paperId1"]
}

papers/{paperId}

{
  "title": "A Paper Title",
  "authors": ["..."],
  "abstract": "trimmed abstract...",
  "source_url": "https://doi.org/...",
  "score": 3.87,
  "isOA": true,
  "links": { "doi": "10.1234/xyz" },
  "sourceFlags": { "s2": true, "openalex": true, "crossref": true, "arxiv": false },
  "firstSeenAt": "<Timestamp>",
  "lastSeenAt": "<Timestamp>",
  "updatedAt": "<Timestamp>"
}

digests/{uid}/latest

{
  "generatedAt": "<Timestamp>",
  "runId": "uid:YYYY-MM-DD",
  "paperIds": ["paperId1", "paperId2"]
}

events/{uid}/{eventId}

{
  "type": "paper.saved",
  "ts": "<ServerTimestamp>",
  "payload": { "paperId": "xyz789" }
}


⸻

Write-Ahead Log (Event Envelope)

Canonical schema (v1):

{
  "v": 1,
  "type": "papers.upserted",
  "runId": "uid:YYYY-MM-DD",
  "uid": "abc123",
  "ts": "2025-11-05T12:00:00Z",
  "items": [{
    "key": "doi:10.1234/xyz",
    "title": "...",
    "year": 2024,
    "venue": "Journal ...",
    "citations": 42,
    "oa": true,
    "links": {"doi": "10.1234/xyz"},
    "score": 3.87,
    "provenance": {"s2": true, "openalex": true, "arxiv": false},
    "updatedAt": "2025-11-05T12:00:00Z"
  }]
}


⸻

Firestore Security Rules

rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Users manage only their own profile
    match /users/{uid} {
      allow read, write: if request.auth != null && request.auth.uid == uid;
    }

    // Seeds - users manage their own research seeds
    match /seeds/{uid} {
      allow read, write: if request.auth != null && request.auth.uid == uid;
    }

    // Digests - users can only read their own digests
    match /digests/{uid}/{doc=**} {
      allow read: if request.auth != null && request.auth.uid == uid;
      allow write: if false; // Admin SDK only
    }

    // User events - users can create and read their own events
    match /events/{uid}/{doc=**} {
      allow create, read: if request.auth != null && request.auth.uid == uid;
      allow update, delete: if false; // Events are immutable
    }

    // Papers: global catalog (read-only for authenticated users)
    match /papers/{doc=**} {
      allow read: if request.auth != null;
      allow write: if false; // Admin SDK only
    }
  }
}


⸻

Pub/Sub → BigQuery Sink
	•	Topic: rw-wal
	•	BigQuery Dataset: research_wal
	•	Table: events (partitioned by publish_time)
	•	Schema Fields (BigQuery Native):
		◦	data (JSON) - Contains the WAL event payload with fields: v, type, runId, uid, ts, items
		◦	subscription_name (STRING) - Name of the Pub/Sub subscription
		◦	message_id (STRING) - Unique message identifier
		◦	publish_time (TIMESTAMP) - When the message was published (partition field)
		◦	attributes (JSON) - Message attributes from Pub/Sub
	•	Note: The Pub/Sub → BigQuery subscription auto-creates this schema. The WAL event structure (v, type, runId, uid, ts, items) is stored in the data field as JSON.
	•	Purpose: Durable, queryable event ledger for replay, analytics, and migration to full event sourcing.

⸻

Feature Flags

Variable	Default	Description
USE_PUBSUB_AS_SOURCE	false	Dual-write (Firestore + Pub/Sub). When true, collector publishes only.
USE_TASKS_FANOUT	false	Enables Cloud Tasks per-user fan-out (v1).
ENABLE_ANALYTICS	true	Controls Pub/Sub → BigQuery sink.


⸻

Security & Compliance
	•	/api/collect/run accepts requests only from Cloud Scheduler using OIDC authentication.
	•	Firebase Auth required for all user endpoints.
	•	Admin SDK handles Firestore writes; client apps have read-only access to papers.
	•	All secrets stored as environment variables.
	•	No PHI or sensitive personal data is collected.

⸻

Operational Cadence

Task	Service	Frequency
Collector	Cloud Scheduler → /api/collect/run	Daily 09:00 BA Time
WAL Sink	Pub/Sub → BigQuery	Continuous
Backup	BigQuery to GCS (export)	Monthly


⸻

Upgrade Path

Stage	SoT	Architecture
v0	Firestore (app), BigQuery (ledger)	Dual-write (synchronous)
v1	BigQuery / PubSub Lite	Event-sourced (fan-out + consumers)
v2	Same + Agents	Agentic event-driven extensions


⸻

Summary

Version 1.0 defines a secure, modular, event-driven v0 architecture that:
	•	ships quickly,
	•	stores data safely,
	•	logs every collector run to a durable WAL, and
	•	preserves a frictionless path to full event-sourced and agentic operation.

This document supersedes all earlier drafts.
