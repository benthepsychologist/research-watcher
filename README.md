# Research Watcher

**Stay up to date. Stay engaged. Stay curious.**

## Overview

Research Watcher is a field-wide discovery platform for academic research. It transforms how researchers explore their discipline - from browsing topic maps and citation networks to defining custom research boundaries and tracking emerging areas. Built for psychologists and researchers who want to see "ALL of it" - not just filtered results.

This project is built on a modern, serverless-first stack using Python, Flask, and Google Cloud Platform. The core architecture is designed to be scalable and maintainable, starting with a simple dual-write system and providing a clear path to a fully event-sourced model.

## Current Status

**v0.3 - Enhanced Discovery Architecture (In Progress)**

- ✅ **Phase 0-2**: Foundation Complete
  - GCP infrastructure (Cloud Run, Firestore, BigQuery, Pub/Sub)
  - Flask API with authentication
  - External API clients (OpenAlex, Semantic Scholar, arXiv)
  - Paper collection, deduplication, scoring
  - Dual-write architecture (Firestore + WAL)
  - 36 bash tests + 30 pytest tests passing

- ✅ **Phase 3**: Interactive Frontend + Firebase Hosting (Complete)
  - HTMX-based frontend with Tailwind CSS
  - Firebase Auth integration
  - Paper browsing and search
  - Saved papers functionality
  - Firebase Hosting with Cloud Run backend integration
  - Production URL: https://research-watcher.web.app
  - Custom domain: app.researchwatcher.org (DNS configured, SSL pending)

- ✅ **Phase 1 (Enhanced Discovery)**: OpenAlex Topic Infrastructure (Complete)
  - 1,487 Social Sciences topics cached in Firestore (144 Psychology topics)
  - Topics API with 6 endpoints: list, detail, search, fields, stats, hierarchy
  - Hierarchical topic structure: Domain → Field → Subfield → Topic
  - Ready for frontend browsing UI

- 📋 **Next: Enhanced Discovery (Phases 2-5)**
  - **Phase 2**: Topic browsing UI (tree view, detail panels)
  - **Phase 3**: Research Networks (CRUD boundaries with versioning) ← **Killer Feature**
  - **Phase 4**: Citation & author networks (graph exploration)
  - **Phase 5**: Contextual search (scoped by topic/network/author)

See [Enhanced Discovery Spec](./.specwright/specs/enhanced-discovery-spec.md) for full details.

## Key Documents

This repository is organized and developed following clear specifications and implementation plans. All developers, human or AI, should familiarize themselves with these documents before contributing.

### Specifications

*   **[Enhanced Discovery Spec](./.specwright/specs/enhanced-discovery-spec.md):** (v0.3) Field-wide discovery with topics, research networks, and citation graphs. **Current focus.**
*   **[Infrastructure Upgrade Spec](./.specwright/specs/infra-upgrade-events-spec.md):** (v1.0) Event-sourced architecture evolution (Phases 4-6).
*   **[Original Project Spec](./docs/spec.md):** (v1.0) Foundation architecture and seed-based digests.

### Implementation Plans

*   **[Agent Implementation Plan](./docs/AIP.md):** (v1.0) Phased development strategy for foundation (Phases 0-3).
*   **[Milestones](./MILESTONES.md):** Development progress tracker.

### Architecture Overview

**Three-Layer Data Architecture:**
1. **Firestore**: Network metadata, stats, user data (20ms reads)
2. **BigQuery**: Paper storage, queries, analytics (300ms queries)
3. **Cloud Storage**: Pre-computed exploration blobs for graph visualization (3-5s download, then instant)

**Key Components:**
- **Frontend**: HTMX + Tailwind CSS (server-rendered, minimal JS)
- **Backend**: Flask + Firebase Admin SDK
- **Data Sources**: OpenAlex (primary), Semantic Scholar (semantic), arXiv (preprints)
- **Background Jobs**: Cloud Tasks + Cloud Scheduler
- **Caching**: Firestore + Cloud Storage blobs

## Technology Stack

### Core Infrastructure (GCP)
*   **Compute:** Google Cloud Run (serverless containers)
*   **Database:** Firestore (Native Mode) - user data, network metadata
*   **Data Warehouse:** Google BigQuery - paper storage, queries, analytics
*   **Storage:** Cloud Storage - pre-computed exploration blobs
*   **Queue:** Cloud Tasks - background job processing
*   **Scheduler:** Cloud Scheduler - daily collection, refreshes
*   **Events:** Google Cloud Pub/Sub - Write-Ahead Log (WAL)

### Application Stack
*   **Backend:** Python 3.11 + Flask (Cloud Run)
*   **Frontend:** HTMX + Tailwind CSS (server-rendered)
*   **Authentication:** Firebase Authentication (Google Sign-In)
*   **Hosting:** Firebase Hosting with automatic Cloud Run proxy for `/api/**`

### External APIs
*   **OpenAlex:** Primary paper source (~250M papers, free API)
*   **Semantic Scholar:** Semantic similarity and recommendations
*   **arXiv:** Open-access preprints

### Development Tools
*   **Testing:** pytest (30+ tests), bash tests (36+ tests)
*   **Environment:** Nix-based with Python virtual environment
*   **Deployment:** gcloud CLI + Firebase CLI

## Repository Structure

```
research-watcher/
├── app/                      # Flask application
│   ├── __init__.py          # App factory
│   ├── api/                 # API blueprints
│   │   ├── users.py         # User management
│   │   ├── seeds.py         # Interest seeds (topics, authors, venues)
│   │   ├── digest.py        # Paper digests
│   │   ├── search.py        # Paper search
│   │   ├── collector.py     # Background paper collection
│   │   └── feedback.py      # User feedback
│   └── services/            # Business logic
│       ├── collector.py     # Paper collection + deduplication
│       ├── openalex_client.py    # OpenAlex API client
│       ├── semantic_scholar.py   # Semantic Scholar client
│       └── arxiv_client.py       # arXiv client
├── public/                  # Frontend (HTMX + Tailwind)
│   ├── index.html          # Landing page
│   ├── app.html            # Main app (post-login)
│   ├── js/                 # Client-side JavaScript
│   └── css/                # Styles
├── scripts/                # Utility scripts
│   ├── test_api_clients.py      # API client tests
│   └── create_test_user.py      # Test user creation
├── tests/                  # Test suite
│   ├── test_api.py         # API integration tests
│   └── test_services.py    # Service unit tests
├── docs/                   # Documentation
│   ├── spec.md            # Original specification (v1.0)
│   └── AIP.md             # Agent Implementation Plan
├── .specwright/specs/     # New specifications
│   ├── enhanced-discovery-spec.md    # v0.3 (current focus)
│   └── infra-upgrade-events-spec.md  # v1.0 (future)
├── MILESTONES.md          # Development progress
├── requirements.txt       # Python dependencies
└── devserver.sh          # Development server script
```

## Development Environment

This project is configured to run in a Nix-based environment managed by Firebase Studio.

1.  **Activate Virtual Environment:** The environment uses a Python virtual environment located at `.venv`. You must activate it to access project dependencies:
    ```bash
    source .venv/bin/activate
    ```

2.  **Install Dependencies:** If new packages are added to `requirements.txt`, install them:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Development Server:** The Flask development server can be started using the provided script. This will make the API available for local testing and development.
    ```bash
    ./devserver.sh
    ```

4.  **Run Tests:**
    ```bash
    # Python tests
    pytest tests/

    # API client tests
    python scripts/test_api_clients.py
    ```

## Deployment

### Frontend (Firebase Hosting)

```bash
# Deploy frontend to Firebase Hosting
export GOOGLE_APPLICATION_CREDENTIALS="./serviceAccountKey.json"
npx firebase deploy --only hosting --project research-watcher
```

**Production URLs:**
- Primary: https://research-watcher.web.app
- Custom domain: https://app.researchwatcher.org (when SSL active)

### Backend (Cloud Run)

```bash
# Build and deploy to Cloud Run
gcloud builds submit --tag gcr.io/research-watcher/rw-api
gcloud run deploy rw-api \
  --image gcr.io/research-watcher/rw-api \
  --region us-central1 \
  --platform managed
```

**Backend URL:** https://rw-api-491582996945.us-central1.run.app

**Note:** Firebase Hosting automatically proxies `/api/**` requests to Cloud Run.

## API Endpoints

### Topics API (Enhanced Discovery Phase 1)

All endpoints require Firebase Authentication (Bearer token in Authorization header).

- `GET /api/topics` - List all topics (flat or hierarchy format)
  - Query params: `?field=Psychology&format=hierarchy`
- `GET /api/topics/{topicId}` - Get topic details
- `GET /api/topics/search` - Search topics by keyword
  - Query params: `?q=memory&field=Psychology&limit=20`
- `GET /api/topics/fields` - List all fields with topic counts
- `GET /api/topics/stats` - Get topic collection statistics

### Other APIs

- `POST /api/users/sync` - Sync user profile
- `GET /api/users/profile` - Get user profile
- `GET /api/seeds` - Get research seeds
- `POST /api/seeds` - Update seeds
- `GET /api/digest/latest` - Get latest digest
- `GET /api/search` - Search papers
- `GET /api/saved` - Get saved papers
- `POST /api/saved` - Save a paper
- `DELETE /api/saved/{id}` - Remove saved paper

## Key Concepts for AI Agents

### Research Networks (Core Feature)
- User-defined boundaries for tracking research areas
- Flexible composition: topics + papers + authors + citations
- Git-style versioning with branching
- Visual pruning with exclusion lists
- Background compute generates exploration blobs

### Three-Layer Architecture
1. **Firestore** (20ms): Network metadata, instant dashboard
2. **BigQuery** (300ms): Paper storage, paginated browsing
3. **Cloud Storage** (3-5s): Pre-computed blobs, graph exploration

### Data Flow
```
User creates network → Firestore (instant)
                    ↓
Background job (60s) → BigQuery queries
                    ↓
                    Compute graph structure
                    ↓
                    Upload blob to Cloud Storage
                    ↓
User explores → Download blob (3-5s)
             ↓
             All interactions instant (in-memory)
```

### Current Priorities
1. OpenAlex topic infrastructure (Phase 1)
2. Topic browsing UI (Phase 2)
3. Research Networks with CRUD + versioning (Phase 3) ← **Killer Feature**

Please refer to the [Enhanced Discovery Spec](./.specwright/specs/enhanced-discovery-spec.md) for complete implementation details.
