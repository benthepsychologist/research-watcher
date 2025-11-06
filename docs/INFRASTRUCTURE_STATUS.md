# Research Watcher - Infrastructure Status

**Date**: 2025-11-06
**Phase**: 0 Complete (Bootstrap & Environment)
**Project ID**: research-watcher
**Project Number**: 491582996945

**Note**: URLs, project numbers, and service account emails shown are specific to this GCP project. They will differ when deploying to another project.

---

## ✅ Completed Infrastructure

### GCP Project
- **Project ID**: `research-watcher`
- **Region**: `us-central1`
- **Authenticated as**: ben@getmensio.com

### APIs Enabled
- ✅ Cloud Run API
- ✅ Cloud Pub/Sub API
- ✅ BigQuery API
- ✅ Cloud Scheduler API
- ✅ Firestore API
- ✅ Cloud Build API
- ✅ Firebase API

### Firestore
- ✅ Database created in **Native Mode**
- ✅ Location: `us-central1`
- ✅ Database ID: `(default)`
- ✅ Free tier enabled
- ⚠️ **Security rules need manual deployment** (requires Firebase CLI)
  ```bash
  firebase deploy --only firestore:rules
  firebase deploy --only firestore:indexes
  ```

### Pub/Sub
- ✅ Topic created: `rw-wal`
- ✅ Subscription created: `rw-wal-to-bq`
- ✅ Connected to BigQuery sink

### BigQuery
- ✅ Dataset created: `research_wal`
- ✅ Table created: `events`
- ✅ Partitioned by: `publish_time` (DAY)
- ✅ Schema:
  - `data` (JSON) - WAL event payload
  - `subscription_name` (STRING)
  - `message_id` (STRING)
  - `publish_time` (TIMESTAMP)
  - `attributes` (JSON)

### Service Accounts
- ✅ **API Service Account**: `rw-api@research-watcher.iam.gserviceaccount.com`
  - Roles: datastore.user, pubsub.publisher, cloudtasks.enqueuer
- ✅ **Scheduler Service Account**: `scheduler-invoker@research-watcher.iam.gserviceaccount.com`
  - Roles: run.invoker (on rw-api service)
- ✅ **Local dev key**: `serviceAccountKey.json` created

### Cloud Run
- ✅ Service deployed: `rw-api`
- ✅ URL: https://rw-api-491582996945.us-central1.run.app
- ✅ Region: `us-central1`
- ✅ Service Account: `rw-api@research-watcher.iam.gserviceaccount.com`
- ✅ Memory: 512Mi
- ✅ Timeout: 300s
- ✅ Max instances: 10
- ✅ Authentication: unauthenticated (public)
- ✅ Status: **LIVE** (returns "Hello World!")

### Cloud Scheduler
- ✅ Job created: `collect-daily`
- ✅ Schedule: `0 9 * * *` (Daily at 09:00 Buenos Aires time)
- ✅ Target: `/api/collect/run`
- ✅ Authentication: OIDC with scheduler-invoker SA
- ✅ Next run: 2025-11-07 at 12:00 UTC (09:00 Buenos Aires)

### Local Development
- ✅ `.env` file created
- ✅ `serviceAccountKey.json` created
- ✅ Virtual environment ready (`.venv`)
- ✅ Dependencies listed in `requirements.txt`

---

## ⚠️ Manual Steps Required

### 1. Deploy Firestore Rules & Indexes
Requires Firebase CLI. Install and run:
```bash
npm install -g firebase-tools
firebase login
firebase use research-watcher
firebase deploy --only firestore:rules
firebase deploy --only firestore:indexes
```

### 2. Set Up Firebase Authentication
Enable in Firebase Console:
1. Go to https://console.firebase.google.com/project/research-watcher/authentication
2. Enable **Google** sign-in provider
3. Enable **Email/Password** sign-in provider

### 3. Deploy Firebase Hosting (Optional for Phase 0)
Can wait until Phase 3 (Frontend):
```bash
firebase deploy --only hosting
```

---

## 🔍 Verification Commands

### Test Cloud Run Service
```bash
curl https://rw-api-491582996945.us-central1.run.app/
# Expected: "Hello World!"
```

### Check Firestore
```bash
gcloud firestore databases list
```

### Check Pub/Sub
```bash
gcloud pubsub topics list
gcloud pubsub subscriptions list
```

### Check BigQuery
```bash
bq show research-watcher:research_wal.events
bq query "SELECT COUNT(*) FROM research_wal.events"
```

### Check Cloud Scheduler
```bash
gcloud scheduler jobs list --location=us-central1
```

### Manually Trigger Scheduler (for testing)
```bash
gcloud scheduler jobs run collect-daily --location=us-central1
```

---

## 📊 Resource Summary

| Resource | Name/ID | Status | URL/Endpoint |
|----------|---------|--------|--------------|
| Project | research-watcher | ✅ Active | - |
| Firestore | (default) | ✅ Native Mode | us-central1 |
| Pub/Sub Topic | rw-wal | ✅ Active | - |
| Pub/Sub Subscription | rw-wal-to-bq | ✅ Active → BigQuery | - |
| BigQuery Dataset | research_wal | ✅ Active | - |
| BigQuery Table | events | ✅ Partitioned | 0 rows |
| Cloud Run | rw-api | ✅ Live | https://rw-api-491582996945.us-central1.run.app |
| Cloud Scheduler | collect-daily | ✅ Scheduled | Daily 09:00 BA |

---

## 💰 Estimated Monthly Cost (0 users)

- **Firestore**: Free tier (1 GB storage, 50K reads, 20K writes/day)
- **Cloud Run**: ~$0 (minimal invocations)
- **Pub/Sub**: ~$0 (free tier: 10 GB/month)
- **BigQuery**: ~$0 (10 GB storage free, 1 TB queries/month free)
- **Cloud Scheduler**: ~$0.10 (1 job = $0.10/month)

**Total**: **~$0.10/month** during development

---

## 🎯 Next Steps

### Immediate (Phase 1)
1. Build Flask API skeleton with auth
2. Implement user management endpoints
3. Test locally with `./devserver.sh`

### Soon (Phase 2)
1. Implement external API clients (OpenAlex, Semantic Scholar, etc.)
2. Build collector logic
3. Test Pub/Sub → BigQuery pipeline
4. Deploy updated Cloud Run service

### Later (Phase 3)
1. Build frontend UI
2. Deploy Firebase Hosting
3. Enable Firebase Authentication
4. Connect frontend to API

---

## 🔐 Security Notes

- ✅ Service account key stored locally (git-ignored)
- ✅ `.env` file git-ignored
- ✅ Service accounts follow least privilege
- ✅ Cloud Scheduler uses OIDC authentication
- ⚠️ Cloud Run currently allows unauthenticated access (will lock down in Phase 1)
- ⚠️ Firestore rules not yet deployed (needs Firebase CLI)

---

## 📝 Configuration Files Created

- ✅ `firebase.json` - Firebase Hosting + Firestore config
- ✅ `firestore.rules` - Security rules (needs deployment)
- ✅ `firestore.indexes.json` - Query indexes (needs deployment)
- ✅ `Dockerfile` - Cloud Run container
- ✅ `.env` - Local environment variables
- ✅ `.env.example` - Environment template
- ✅ `.gitignore` - Secrets protection
- ✅ `serviceAccountKey.json` - Local dev credentials

---

**Phase 0 Status**: ✅ **COMPLETE**
**Ready for**: **Phase 1 - Backend Core (API Skeleton)**

---

*Last updated: 2025-11-06 18:50 UTC*
