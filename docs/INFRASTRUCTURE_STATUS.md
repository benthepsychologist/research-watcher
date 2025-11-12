# Research Watcher - Infrastructure Status

**Date**: 2025-11-12
**Phase**: Phase 3 Complete + Enhanced Discovery Phases 1-2 Complete
**Project ID**: research-watcher
**Project Number**: 491582996945

**Status**: 🟢 **PRODUCTION - FULLY OPERATIONAL**

**Live URLs**:
- Frontend (Custom Domain): https://app.researchwatcher.org
- Frontend (Firebase Default): https://research-watcher.web.app
- Backend API: https://rw-api-491582996945.us-central1.run.app

---

## ✅ Deployed Infrastructure (Current State)

### GCP Project
- **Project ID**: `research-watcher`
- **Region**: `us-central1`
- **Authenticated as**: ben@getmensio.com
- **Environment**: Production

### APIs Enabled
- ✅ Cloud Run API
- ✅ Cloud Pub/Sub API
- ✅ BigQuery API
- ✅ Cloud Scheduler API
- ✅ Firestore API
- ✅ Cloud Build API
- ✅ Firebase API
- ✅ Firebase Hosting API
- ✅ Identity Platform API

### Firestore (Production Data)
- ✅ Database in **Native Mode**
- ✅ Location: `us-central1`
- ✅ Database ID: `(default)`
- ✅ Collections:
  - `users/{uid}` - User profiles, quotas, preferences
  - `users/{uid}/seeds` - Research interest keywords
  - `users/{uid}/saved_papers` - Saved papers
  - `papers/{paperId}` - Deduplicated paper metadata
  - `digests/{uid}_latest` - Latest digest per user
  - `topics/{topicId}` - **1,487 OpenAlex topics cached**
  - `events/{uid}/` - User interaction events
- ✅ Security rules deployed
- ✅ Indexes deployed
- ✅ Free tier (sufficient for alpha)

### Pub/Sub (WAL Pipeline)
- ✅ Topic: `rw-wal`
- ✅ Subscription: `rw-wal-to-bq` (push to BigQuery)
- ✅ WAL events flowing from API → BigQuery
- ✅ Event types: `digest.created`, `papers.upserted`, `user.synced`

### BigQuery (Analytics & WAL Storage)
- ✅ Dataset: `research_wal`
- ✅ Table: `events` (partitioned by `publish_time`)
- ✅ Schema:
  - `data` (JSON) - Full event payload
  - `subscription_name` (STRING)
  - `message_id` (STRING)
  - `publish_time` (TIMESTAMP)
  - `attributes` (JSON)
- ✅ Receiving real events from production
- ✅ Query cost: Free tier (1 TB/month)

### Service Accounts
- ✅ **rw-api**: `rw-api@research-watcher.iam.gserviceaccount.com`
  - Roles: datastore.user, pubsub.publisher, cloudtasks.enqueuer
  - Used by: Cloud Run API service
- ✅ **scheduler-invoker**: `scheduler-invoker@research-watcher.iam.gserviceaccount.com`
  - Roles: run.invoker
  - Used by: Cloud Scheduler jobs

### Cloud Run (Backend API)
- ✅ Service: `rw-api`
- ✅ Current Revision: `rw-api-00014-f6b` (deployed 2025-11-12)
- ✅ URL: https://rw-api-491582996945.us-central1.run.app
- ✅ Region: `us-central1`
- ✅ Memory: 512Mi
- ✅ Timeout: 300s
- ✅ Max instances: 10
- ✅ Authentication: unauthenticated (public, but endpoints protected by JWT)
- ✅ Status: **LIVE** with full API (8 blueprints)
- ✅ **API Blueprints**:
  - `/api/users` - User management
  - `/api/seeds` - Research seeds CRUD
  - `/api/digest` - Daily digest retrieval
  - `/api/search` - Real-time paper search
  - `/api/saved` - Saved papers management
  - `/api/collector` - Background collection triggers
  - `/api/feedback` - User interaction tracking
  - `/api/topics` - **Topics API (6 endpoints)** ← Phase ED-1

### Cloud Scheduler (Automated Jobs)
- ✅ Job: `collect-daily`
- ✅ Schedule: `0 9 * * *` (Daily at 09:00 Buenos Aires time)
- ✅ Target: `/api/collect/run`
- ✅ Authentication: OIDC with scheduler-invoker SA
- ✅ Status: **Running daily** (collecting papers for all users)

### Firebase Hosting (Frontend)
- ✅ Default URL: https://research-watcher.web.app
- ✅ Custom Domain: **https://app.researchwatcher.org**
- ✅ SSL Certificate: Active (Let's Encrypt, auto-renewed)
- ✅ CDN: Cloudflare (via Firebase)
- ✅ Deployment Method: gsutil → gs://research-watcher-web/
- ✅ Files:
  - `index.html` - Landing page with Google Sign-In
  - `app.html` - Main application (5 tabs: Digest, Search, Seeds, Saved, **Topics**)
  - `signout.html` - Sign-out page
- ✅ **Caching Strategy**:
  - HTML: 5 minutes (`max-age=300`)
  - JS/CSS: 1 year immutable (`max-age=31536000`)
  - Images: 1 year immutable
- ✅ **Performance Optimizations** (2025-11-12):
  - Preconnect hints for CDNs
  - Deferred scripts for HTMX
  - Aggressive browser caching
  - Load time: 1-1.5 seconds

### Firebase Authentication
- ✅ Provider: Google Sign-In (OAuth2)
- ✅ Authorized Domains:
  - `research-watcher.firebaseapp.com`
  - `research-watcher.web.app`
  - **`app.researchwatcher.org`** (custom domain)
  - `localhost` (dev)
- ✅ API Key Restrictions:
  - Browser key allows: app.researchwatcher.org, *.web.app, *.firebaseapp.com, localhost
- ✅ JWT validation: Backend verifies all API calls
- ✅ Status: **Working on custom domain** (fixed 2025-11-12)

### Custom Domain Configuration
- ✅ Domain: `app.researchwatcher.org`
- ✅ DNS Provider: Namecheap
- ✅ DNS Records:
  - A records pointing to Firebase Hosting
  - TXT record for domain verification
- ✅ SSL: Active (HTTPS enforced)
- ✅ HSTS: Enabled (`max-age=31556926`)
- ✅ **Auth Configuration**:
  - API key allows custom domain
  - CORS allows custom domain
  - Firebase authorized domains includes custom domain
  - authDomain in frontend config: `app.researchwatcher.org`

### External API Integrations
- ✅ **OpenAlex**: Primary paper source
  - ~250M papers, free API
  - Polite pool with email
  - Comprehensive metadata + abstracts
  - **Topics API**: 1,487 Social Sciences topics cached
- ✅ **Semantic Scholar**: Semantic intelligence
  - Own API key (for limited alpha)
  - Semantic similarity + recommendations
  - Optional: future user-provided keys
- ✅ **arXiv**: Open-access preprints
  - XML parsing
  - No API key required

### Data Processing Pipeline
- ✅ **Collection Flow**:
  1. Cloud Scheduler triggers `/api/collect/run` daily
  2. API fetches papers from OpenAlex + S2 + arXiv
  3. Deduplication + scoring (0-100)
  4. Upsert to Firestore `papers/` collection
  5. Create digest document `digests/{uid}_latest`
  6. Publish WAL event to Pub/Sub
  7. Pub/Sub → BigQuery for analytics
- ✅ **Scoring Algorithm**: Citations + venue + recency + OA + abstract
- ✅ **Status**: Running successfully (49+ papers collected per user)

---

## 🎯 Feature Status

### Foundation (v0)
- ✅ **Phase 0**: Infrastructure bootstrapped
- ✅ **Phase 1**: Backend core API (Flask + JWT)
- ✅ **Phase 2**: Collector + dual-write (WAL)
- ✅ **Phase 3**: Frontend + Firebase Hosting + custom domain

### Enhanced Discovery (v0.3)
- ✅ **Phase ED-1**: OpenAlex Topic Infrastructure
  - 1,487 Social Sciences topics cached
  - 144 Psychology topics (primary focus)
  - 6 API endpoints (list, detail, search, fields, stats, hierarchy)
- ✅ **Phase ED-2**: Topic Browsing UI
  - New "📚 Topics" tab in navigation
  - Real-time keyword search with debounce
  - Field filter dropdown (6 fields)
  - Topic detail panel (hierarchy, stats, keywords)
  - Responsive 3-column grid design
- ⏳ **Phase ED-3**: Research Networks (CRUD + Versioning) - Next up
- ⏳ **Phase ED-4**: Citation & Author Networks
- ⏳ **Phase ED-5**: Contextual Search

### Current User Experience
Users can now:
- ✅ Sign in with Google on custom domain
- ✅ View daily digest of 50 papers matching research interests
- ✅ Search papers in real-time across all sources
- ✅ Manage research interest seeds (keywords)
- ✅ Save papers to reading list
- ✅ **Browse 1,487 topics across 6 fields** (ED Phase 2)
- ✅ **Search topics by keyword** (ED Phase 2)
- ✅ **View topic details with hierarchy** (ED Phase 2)

---

## 🔧 Recent Changes (2025-11-12 Hotfixes)

### Hotfix 1: Custom Domain Authentication
**Problem**: Firebase auth blocked on app.researchwatcher.org
**Fixed**:
- Updated Firebase API key referrer restrictions
- Added custom domain to backend CORS
- Added to Firebase authorized domains
- Deployed backend revision `rw-api-00014-f6b`

### Hotfix 2: Performance Optimization
**Problem**: 2-3 second page loads
**Fixed**:
- Added preconnect hints for CDNs
- Added defer to HTMX script
- Configured aggressive caching headers
- **Result**: 1-1.5 second loads (40-50% improvement)

### Hotfix 3: Topics Tab Visibility
**Problem**: 5th tab (Topics) hidden on smaller screens
**Fixed**:
- Added `flex-wrap` to navigation container
- Added `overflow-x-auto` for scrolling
- Responsive spacing (`space-x-4 sm:space-x-8`)

### Hotfix 4: Auth Redirect to Custom Domain
**Problem**: After login, redirected to wrong domain
**Fixed**:
- Changed `authDomain` in Firebase config from `research-watcher.firebaseapp.com` to `app.researchwatcher.org`
- Users now stay on custom domain throughout auth flow

---

## 🔍 Verification Commands

### Test Backend API
```bash
# Health check
curl https://rw-api-491582996945.us-central1.run.app/

# Topics fields (public endpoint)
curl https://rw-api-491582996945.us-central1.run.app/api/topics/fields | jq

# Topics stats
curl https://rw-api-491582996945.us-central1.run.app/api/topics/stats | jq
```

### Test Frontend
```bash
# Landing page
curl https://app.researchwatcher.org/index.html | grep "Research Watcher"

# App page (should have Topics tab)
curl https://app.researchwatcher.org/app.html | grep "📚 Topics"

# Check SSL
curl -I https://app.researchwatcher.org | grep -i "strict-transport"
```

### Check Firestore Data
```bash
# Count topics
gcloud firestore databases list
# Manual check in console: https://console.firebase.google.com/project/research-watcher/firestore

# Expected: 1,487 documents in topics/ collection
```

### Check BigQuery WAL Events
```bash
# Count events
bq query "SELECT COUNT(*) FROM research_wal.events"

# Recent events
bq query "SELECT type, uid, TIMESTAMP(publish_time) as time FROM research_wal.events ORDER BY publish_time DESC LIMIT 10"
```

### Check Cloud Scheduler
```bash
# List jobs
gcloud scheduler jobs list --location=us-central1

# Manually trigger (for testing)
gcloud scheduler jobs run collect-daily --location=us-central1
```

### Check Cloud Run Logs
```bash
# Recent logs
gcloud logs read --limit=20 --service=rw-api

# Error logs only
gcloud logs read --limit=20 --service=rw-api --severity=ERROR
```

---

## 📊 Resource Summary

| Resource | Name/ID | Status | URL/Endpoint |
|----------|---------|--------|--------------|
| **Frontend** | research-watcher | ✅ Live | https://app.researchwatcher.org |
| Custom Domain | app.researchwatcher.org | ✅ Active + SSL | - |
| **Backend API** | rw-api | ✅ Live (rev 00014-f6b) | https://rw-api-491582996945.us-central1.run.app |
| Firestore | (default) | ✅ Native Mode | 1,487 topics + user data |
| Topics Collection | topics/ | ✅ Cached | 1,487 documents |
| Pub/Sub Topic | rw-wal | ✅ Active | - |
| BigQuery Dataset | research_wal | ✅ Receiving events | - |
| Cloud Scheduler | collect-daily | ✅ Running daily | 09:00 Buenos Aires |
| Firebase Auth | Google Sign-In | ✅ Working | Custom domain enabled |

---

## 💰 Current Monthly Cost (Alpha - ~5 Users)

- **Firestore**: ~$0.02 (within free tier)
- **Cloud Run**: ~$2-5 (512Mi, minimal traffic)
- **Pub/Sub**: ~$0 (free tier)
- **BigQuery**: ~$0 (free tier, minimal storage/queries)
- **Cloud Scheduler**: $0.10 (1 job)
- **Firebase Hosting**: $0 (Spark plan, within limits)
- **Custom Domain**: $0 (DNS via Namecheap, paid annually)

**Total**: **~$2-7/month** during alpha phase

**Estimated at Scale**:
- 20 users (Alpha tier, free): ~$75/month
- 100 users (30% paid Beta): +$40/month net (sustainable)
- 1,000 users (50% paid): +$3,150/month net (profitable)

---

## 🎯 Next Steps

### Immediate (Phase ED-3)
1. **Research Networks Feature** (the "KILLER FEATURE")
   - CRUD API for network boundaries
   - Version control (Git-style branching)
   - Exclusion lists (pruning support)
   - Background compute + caching architecture
   - Three-layer data architecture (Firestore/BigQuery/Cloud Storage)

### Soon (Phase ED-4)
1. Citation & author networks
2. Paper-to-paper discovery
3. Co-author graphs

### Later (Phase ED-5)
1. Contextual search (scoped by network/topic/author)

### Infrastructure Upgrades (v1.0)
1. Event-sourced architecture
2. Fan-out processing with Cloud Tasks
3. Agent Bridge API

---

## 🔐 Security Status

- ✅ Service account keys stored securely (git-ignored)
- ✅ `.env` file git-ignored
- ✅ Service accounts follow least privilege
- ✅ Cloud Scheduler uses OIDC authentication
- ✅ API endpoints protected by JWT validation
- ✅ Firestore security rules deployed
- ✅ CORS configured for custom domain
- ✅ SSL/TLS enforced (HSTS enabled)
- ✅ API key restrictions configured
- ✅ Firebase authorized domains locked down

---

## 📝 Configuration Files

| File | Purpose | Status |
|------|---------|--------|
| `firebase.json` | Firebase Hosting + caching headers | ✅ Deployed |
| `firestore.rules` | Security rules | ✅ Deployed |
| `firestore.indexes.json` | Query indexes | ✅ Deployed |
| `Dockerfile` | Cloud Run container | ✅ Active |
| `.env` | Local environment | ✅ Configured |
| `requirements.txt` | Python dependencies | ✅ Up to date |
| `app/__init__.py` | Flask app factory | ✅ With CORS for custom domain |
| `public/app.html` | Main application | ✅ With Topics tab + performance opts |
| `public/index.html` | Landing page | ✅ With custom authDomain |

---

## 🧪 Testing Status

### Backend Tests
- ✅ 30+ pytest tests passing
- ✅ API client tests (OpenAlex, S2, arXiv)
- ✅ Deduplication logic tested
- ✅ Scoring algorithm validated
- ✅ Topics API integration tests

### Bash Integration Tests
- ✅ 36 bash tests passing
- ✅ End-to-end collector test
- ✅ WAL event verification
- ✅ BigQuery sink validation

### Manual E2E Tests
- ✅ Authentication flow (Google Sign-In)
- ✅ All 5 tabs functional
- ✅ Topics browsing and search
- ✅ Paper search working
- ✅ Seeds management
- ✅ Saved papers
- ✅ Daily digest generation

---

## 📚 Documentation

| Document | Purpose | Status |
|----------|---------|--------|
| README.md | Project overview | ✅ Up to date |
| MILESTONES.md | Progress tracker | ✅ Active |
| ARCHITECTURE.md | System design | ✅ Updated for v0.3 |
| TROUBLESHOOTING.md | Common issues | ✅ **NEW** (2025-11-12) |
| DEPLOYMENT.md | Deployment procedures | ✅ **NEW** (2025-11-12) |
| INFRASTRUCTURE_STATUS.md | This file | ✅ **UPDATED** (2025-11-12) |
| API_REFERENCE.md | API docs | ⏳ To be created |
| .specwright/specs/ | Feature specifications | ✅ Active |

---

**Infrastructure Status**: ✅ **PRODUCTION READY**
**Current Phase**: **Enhanced Discovery Phase 3 (Research Networks)**
**Overall Health**: 🟢 **EXCELLENT**

---

*Last updated: 2025-11-12 21:00 UTC*
*Maintainer: Development Team*
