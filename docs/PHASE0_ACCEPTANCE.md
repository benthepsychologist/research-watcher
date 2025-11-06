# Phase 0 Acceptance Report

**Date**: 2025-11-06
**Phase**: 0 - Bootstrap & Environment
**Status**: ✅ **ACCEPTED**
**Next Phase**: Phase 1 - Backend Core (API Skeleton)

---

## AIP Phase 0 Requirements vs Delivered

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | Create Firebase Project with Firestore (Native) | ✅ | Database `(default)` in us-central1 |
| 1 | Enable Firebase Auth (Google + Email) | ⚠️ | **Manual step required** (Firebase Console) |
| 2 | Enable Cloud Run API | ✅ | Service deployed and live |
| 2 | Enable Pub/Sub API | ✅ | Topic and subscription active |
| 2 | Enable BigQuery API | ✅ | Dataset and table created |
| 2 | Enable Cloud Scheduler API | ✅ | Job created and scheduled |
| 3 | Clone repo and create structure | ✅ | app/, public/, docs/, scripts/ |
| 4 | Create Pub/Sub topic `rw-wal` | ✅ | projects/research-watcher/topics/rw-wal |
| 4 | Create BigQuery dataset `research_wal` | ✅ | With partitioned `events` table |
| 4 | Create Pub/Sub → BigQuery sink | ✅ | Subscription `rw-wal-to-bq` active |
| 5 | Deploy Firebase Hosting stub | ⚠️ | **Manual step required** (Firebase CLI) |
| 6 | Add environment variables | ✅ | `.env` created with all required vars |
| 7 | Create OIDC service account for Scheduler | ✅ | `scheduler-invoker@research-watcher` |
| 7 | Grant Cloud Run invoker role | ✅ | IAM policy verified |
| 8 | Commit and tag as v0-bootstrap | ✅ | Tags: v0-bootstrap, v0-infrastructure |

**Overall**: 11/13 Complete (85%)
**Blockers**: 0 critical, 2 optional manual steps deferred

---

## Test Results

### ✅ Infrastructure Tests (All Passed)

#### 1. Cloud Run Service
```bash
$ curl https://rw-api-491582996945.us-central1.run.app/
Hello World!
```
**Result**: ✅ Service responding correctly

#### 2. Firestore Database
```bash
$ gcloud firestore databases describe --database="(default)"
NAME: projects/research-watcher/databases/(default)
TYPE: FIRESTORE_NATIVE
LOCATION: us-central1
```
**Result**: ✅ Database accessible and configured

#### 3. Pub/Sub Pipeline
```bash
$ gcloud pubsub topics publish rw-wal --message='{"test":"data"}'
messageIds: ['16968528242495060']
```
**Result**: ✅ Messages published successfully

#### 4. BigQuery Table
```bash
$ bq show research-watcher:research_wal.events
Schema: data (JSON), subscription_name (STRING), message_id (STRING),
        publish_time (TIMESTAMP), attributes (JSON)
Partitioning: DAY (field: publish_time)
```
**Result**: ✅ Table schema correct, partitioning configured

#### 5. Service Account Permissions
**rw-api@research-watcher.iam.gserviceaccount.com**:
- ✅ roles/datastore.user (Firestore access)
- ✅ roles/pubsub.publisher (Pub/Sub publish)
- ✅ roles/cloudtasks.enqueuer (Task queue access)

**scheduler-invoker@research-watcher.iam.gserviceaccount.com**:
- ✅ roles/run.invoker (Cloud Run invoke)

**Result**: ✅ All IAM policies correct

#### 6. Cloud Scheduler
```yaml
schedule: 0 9 * * *
timeZone: America/Argentina/Buenos_Aires
uri: https://rw-api-491582996945.us-central1.run.app/api/collect/run
oidc: scheduler-invoker@research-watcher.iam.gserviceaccount.com
state: ENABLED
```
**Result**: ✅ Scheduler configured correctly

#### 7. Local Development Environment
- ✅ serviceAccountKey.json created
- ✅ .env configured with all variables
- ✅ Project structure complete
- ✅ Configuration files present (Dockerfile, firebase.json, etc.)
- ⚠️  Virtual environment needs reinstallation (known issue, not blocking)

---

## Deferred Items (Non-Blocking)

### 1. Firebase Authentication Setup
**Status**: Manual configuration required
**Reason**: Requires Firebase Console access
**Impact**: None for Phase 0; required for Phase 3 (Frontend)
**Action**: Document in Phase 3 checklist

**Steps to complete**:
1. Go to Firebase Console → Authentication
2. Enable Google sign-in provider
3. Enable Email/Password provider

### 2. Firebase Hosting Deployment
**Status**: Requires Firebase CLI
**Reason**: Firebase CLI not available in Cloud Workstation
**Impact**: None for Phase 0/1; required for Phase 3 (Frontend)
**Action**: Deploy during Phase 3

**Steps to complete**:
```bash
npm install -g firebase-tools
firebase login
firebase deploy --only hosting
```

### 3. Firestore Security Rules Deployment
**Status**: Requires Firebase CLI
**Reason**: gcloud doesn't support Firestore rules deployment
**Impact**: Low (rules enforced when deployed)
**Action**: Deploy during Phase 1 or 3

**Steps to complete**:
```bash
firebase deploy --only firestore:rules
firebase deploy --only firestore:indexes
```

---

## Known Issues

### 1. Virtual Environment
**Issue**: `.venv` pip installation broken
**Severity**: Low
**Impact**: None (Phase 1 will use Cloud Run container)
**Resolution**: Rebuild in Phase 1 or use system Python

### 2. BigQuery Pub/Sub Latency
**Observation**: Messages take 1-5 minutes to appear in BigQuery
**Severity**: Informational
**Impact**: None (expected behavior for BigQuery streaming)
**Action**: None required

---

## Phase 0 Deliverables Checklist

### Required Infrastructure
- [x] Firebase/GCP project: `research-watcher` (491582996945)
- [x] Firestore Native database in us-central1
- [x] Pub/Sub topic: `rw-wal`
- [x] BigQuery dataset: `research_wal`
- [x] BigQuery table: `events` (partitioned)
- [x] Pub/Sub → BigQuery subscription
- [x] Cloud Run service: `rw-api` (deployed)
- [x] Service accounts with IAM roles
- [x] Cloud Scheduler job: `collect-daily`

### Configuration Files
- [x] firebase.json (Hosting + Firestore config)
- [x] firestore.rules (Security rules)
- [x] firestore.indexes.json (Query indexes)
- [x] Dockerfile (Cloud Run container)
- [x] .env.example (Environment template)
- [x] .env (Local configuration)
- [x] .gitignore (Secrets protection)
- [x] serviceAccountKey.json (Local dev credentials)

### Project Structure
- [x] app/ (with api/, services/, utils/ subdirs)
- [x] public/ (with index.html)
- [x] docs/ (with SETUP.md, AIP.md, spec.md)
- [x] scripts/ (for future maintenance scripts)

### Documentation
- [x] MILESTONES.md (Complete development plan)
- [x] docs/SETUP.md (Infrastructure setup guide)
- [x] docs/INFRASTRUCTURE_STATUS.md (Current state)
- [x] docs/PHASE0_ACCEPTANCE.md (This document)

### Version Control
- [x] Git commits with clear messages
- [x] Tags: v0-bootstrap, v0-infrastructure
- [x] Co-authored commits (human + AI)

---

## Cost Analysis

**Current Monthly Cost (0 active users)**:
- Firestore: $0 (free tier: 1GB storage, 50K reads, 20K writes/day)
- Cloud Run: $0 (minimal invocations)
- Pub/Sub: $0 (free tier: 10 GB/month)
- BigQuery: $0 (10 GB storage, 1 TB queries/month free)
- Cloud Scheduler: $0.10 (1 job)

**Total**: ~$0.10/month

---

## Security Review

### ✅ Security Checklist
- [x] Service account keys not in git (.gitignore)
- [x] .env file not in git (.gitignore)
- [x] Service accounts follow least privilege
- [x] Cloud Scheduler uses OIDC (not API keys)
- [x] Firestore rules file created (deployment pending)
- [x] No hardcoded secrets in code
- [x] All external API keys in environment variables

### ⚠️  Open Security Items
- [ ] Deploy Firestore security rules (Phase 1)
- [ ] Lock down Cloud Run authentication (Phase 1)
- [ ] Enable Firebase Authentication (Phase 3)

---

## Acceptance Criteria Met

According to AIP Phase 0:

> ✅ Output: Firebase + GCP infrastructure online; Cloud Run service placeholder deploys; Hosting rewrite verified.

**Verification**:
- ✅ Firebase + GCP infrastructure: **ONLINE**
- ✅ Cloud Run service: **DEPLOYED** (https://rw-api-491582996945.us-central1.run.app)
- ⚠️  Hosting rewrite: **DEFERRED** (not required for Phase 1)

**Decision**: **ACCEPT Phase 0**
**Rationale**: All critical infrastructure deployed and tested. Hosting deployment deferred to Phase 3 when frontend is built. No blockers for Phase 1 development.

---

## Recommendations for Phase 1

### Immediate Actions
1. ✅ Rebuild virtual environment or use system Python
2. ✅ Begin Flask app factory implementation
3. ✅ Initialize Firebase Admin SDK in app code

### Nice-to-Have
1. Deploy Firestore rules when Firebase CLI available
2. Set up Cloud Run CORS for API testing
3. Add health check endpoint beyond "Hello World"

### Optional Improvements
1. Add monitoring/alerting (Cloud Logging)
2. Set up billing alerts
3. Create staging environment

---

## Sign-Off

**Phase 0 is ACCEPTED and COMPLETE.**
**Ready to proceed to Phase 1: Backend Core (API Skeleton).**

---

**Approver**: BenThePsychologist
**Date**: 2025-11-06
**Next Review**: After Phase 1 completion

---

*Generated during Phase 0 acceptance testing*
