# Research Watcher - Quick Start Guide

## You are here: Ready for End-to-End Testing

All code is deployed and ready. You just need to enable Firebase Authentication manually and test the full user journey.

## What's Deployed

✅ **Frontend**: https://storage.googleapis.com/research-watcher-web/index.html
- Landing page with Google Sign-In button
- App page with Digest, Search, Seeds, and Saved tabs
- HTMX-powered SPA with smooth interactions

✅ **Backend API**: https://rw-api-491582996945.us-central1.run.app
- `/api/users/sync` - User profile sync
- `/api/seeds` - Manage research seeds (GET/POST)
- `/api/search` - Interactive paper search
- `/api/collect/run` - Trigger digest collection
- `/api/digest/latest` - Get personalized digest

✅ **Infrastructure**:
- Firestore: `users/`, `seeds/`, `papers/`, `digests/` collections
- Pub/Sub: `rw-wal` topic for event sourcing
- BigQuery: `rw_analytics.rw_wal` table for analytics

## Step 0: Get Firebase Configuration (5 minutes) 🚨 START HERE

The Firebase API key in the code is invalid. You need to get the correct configuration first.

1. **Go to Firebase Console**:
   - Visit: https://console.firebase.google.com/project/research-watcher/settings/general
   - Scroll to **"Your apps"** section

2. **Create or View Web App**:
   - If no web app exists, click **"Add app"** → **Web** (`</>`)
   - Enter nickname: `Research Watcher Web`
   - Check "Also set up Firebase Hosting"
   - Click **"Register app"**

3. **Copy Firebase Config**:
   - Copy the `firebaseConfig` object shown
   - It should look like:
     ```javascript
     const firebaseConfig = {
       apiKey: "AIzaSy...",
       authDomain: "research-watcher.firebaseapp.com",
       projectId: "research-watcher",
       storageBucket: "research-watcher.firebasestorage.app",
       messagingSenderId: "491582996945",
       appId: "1:491582996945:web:..."
     };
     ```

4. **Update Files**:
   - Replace the `firebaseConfig` in `public/index.html` (lines ~123-130)
   - Replace the `firebaseConfig` in `public/app.html` (lines ~123-130)
   - Use the config you just copied

5. **Deploy Updated Files**:
   ```bash
   gsutil -m cp public/index.html public/app.html gs://research-watcher-web/
   ```

📖 **Detailed instructions**: [GET_FIREBASE_CONFIG.md](./GET_FIREBASE_CONFIG.md)

## Step 1: Enable Firebase Authentication (5 minutes)

🚨 **YOU MUST DO THIS MANUALLY** - Cannot be automated via CLI

1. **Go to Firebase Console**:
   - Visit: https://console.firebase.google.com/project/research-watcher/authentication/providers

2. **Enable Google Sign-In**:
   - Click "Authentication" → "Sign-in method" tab
   - Click "Google" provider
   - Toggle "Enable" to **ON**
   - Set **Project support email**: `ben@getmensio.com`
   - Click **Save**

3. **Add Authorized Domains**:
   - Go to "Authentication" → "Settings" tab
   - Under "Authorized domains", verify these are present:
     - ✅ `research-watcher.firebaseapp.com`
     - ✅ `research-watcher.web.app`
     - ✅ `storage.googleapis.com` (ADD THIS if not present)
     - ✅ `localhost` (for local development)

📖 **Detailed instructions**: [FIREBASE_AUTH_SETUP.md](./FIREBASE_AUTH_SETUP.md)

## Step 2: Test Frontend Manually (10 minutes)

### Test Sign-In Flow

1. **Open Landing Page**:
   ```
   https://storage.googleapis.com/research-watcher-web/index.html
   ```

2. **Click "Get Started" button**
   - Google Sign-In popup should appear
   - Select your Google account
   - Grant permissions
   - Should redirect to `/app.html` automatically

3. **Verify App Loaded**:
   - Header shows your email
   - Four tabs visible: Digest | Search | Seeds | Saved
   - No errors in browser console (F12)

### Test Seeds Management

4. **Click "Seeds" tab**
   - Should show empty state: "No seeds yet..."
   - Add seeds: `machine learning, transformer models, quantum computing`
   - Seeds appear in list instantly
   - Refresh page - seeds should persist

5. **Remove a seed**
   - Click "Remove" button next to a seed
   - Seed disappears instantly
   - Verify in Firestore (optional)

### Test Interactive Search

6. **Click "Search" tab**
   - Enter query: `transformer models`
   - Click "Search" button
   - Results load within 3-5 seconds
   - Paper cards show title, authors, venue, citations, score

7. **Try different filters**
   - Change "Days back" to 30
   - Change "Max results" to 10
   - Re-run search - verify new parameters work

### Test Digest

8. **Run Collector First** (use script below)
   - Wait for collector to finish (~30-60 seconds)

9. **Click "Digest" tab**
   - Papers load automatically
   - Papers sorted by score (highest first)
   - Top papers relevant to your seeds

📋 **Full testing checklist**: [E2E_TESTING_CHECKLIST.md](./E2E_TESTING_CHECKLIST.md)

## Step 3: Test API with Script (5 minutes)

### Get Your Firebase Token

1. **Sign in to the app** (from Step 2)

2. **Open browser console** (F12)

3. **Run this command**:
   ```javascript
   firebase.auth().currentUser.getIdToken().then(token => console.log(token))
   ```

4. **Copy the token** (long string like `eyJhbGciOiJSUzI1NiIs...`)

### Run Automated Test Script

```bash
# Set your token
export FIREBASE_TOKEN="<paste-token-here>"

# Run end-to-end tests
./scripts/test_e2e_auth.sh
```

**Expected output**:
```
✓ Health check passed
✓ User sync successful (UID: ...)
✓ Seeds retrieved (count: 3)
✓ Seeds added successfully (new count: 3)
✓ Search successful: Found 20 papers in 3200ms
✓ Collector ran successfully (Users: 1, Papers: 49)
✓ Digest retrieved successfully: 49 papers
```

## Step 4: Verify Data in Firestore (2 minutes)

```bash
# Check user document
gcloud firestore documents describe "users/<your-uid>" --project=research-watcher

# List seeds
gcloud firestore documents list "users/<your-uid>/seeds" --project=research-watcher

# List papers (should have ~50)
gcloud firestore documents list papers --project=research-watcher --limit=10

# Check digest
gcloud firestore documents list digests --project=research-watcher
```

## Step 5: Verify WAL Events in BigQuery (2 minutes)

```bash
bq query --use_legacy_sql=false \
  "SELECT
    event_type,
    JSON_EXTRACT_SCALAR(event_data, '$.userId') as user_id,
    publishTime
   FROM \`research-watcher.rw_analytics.rw_wal\`
   ORDER BY publishTime DESC
   LIMIT 10"
```

**Expected events**:
- `seed.added`
- `seed.removed`
- `search.executed`
- `digest.generated`

## Common Issues

### "auth/operation-not-allowed"
- **Cause**: Google Sign-In not enabled
- **Fix**: Go to Firebase Console and enable it (Step 1)

### "auth/unauthorized-domain"
- **Cause**: `storage.googleapis.com` not in authorized domains
- **Fix**: Add it in Firebase Console → Authentication → Settings

### "401 Unauthorized" from API
- **Cause**: Token expired (they expire after 1 hour)
- **Fix**: Get new token from browser console

### Papers not loading in Digest
- **Cause**: Collector hasn't run yet
- **Fix**: Run collector manually:
  ```bash
  curl -X POST \
    -H "Authorization: Bearer $FIREBASE_TOKEN" \
    https://rw-api-491582996945.us-central1.run.app/api/collect/run
  ```

### Search returns 0 results
- **Cause**: Query too specific or date range too narrow
- **Fix**: Increase `days_back` to 30, try broader query

## Success Criteria

Phase 3 is complete when you can:

- ✅ Sign in with Google
- ✅ Add and remove research seeds
- ✅ Search papers interactively and get results in < 5s
- ✅ View personalized digest ranked by score
- ✅ All API endpoints work with authentication
- ✅ No critical errors in browser console
- ✅ WAL events landing in BigQuery

## What's Next?

After Phase 3 validation:

- **Phase 4**: Email delivery (SendGrid integration for daily digests)
- **Phase 5**: Scaling & optimization (caching, batching, rate limiting)
- **Phase 6**: Advanced features (export, sharing, saved papers, comments)

## Helpful Commands

```bash
# Re-deploy frontend (if you make changes)
gsutil -m cp public/*.html gs://research-watcher-web/

# Re-deploy API (if you make changes)
gcloud run deploy rw-api \
  --source . \
  --region us-central1 \
  --project research-watcher

# Check API logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=rw-api" \
  --limit 50 --format json --project research-watcher

# Monitor Pub/Sub messages
gcloud pubsub subscriptions pull rw-wal-bigquery-sub \
  --auto-ack --limit=10 --project=research-watcher
```

## Quick Links

- **Landing Page**: https://storage.googleapis.com/research-watcher-web/index.html
- **Firebase Console**: https://console.firebase.google.com/project/research-watcher
- **Cloud Run API**: https://rw-api-491582996945.us-central1.run.app
- **BigQuery**: https://console.cloud.google.com/bigquery?project=research-watcher
- **Firestore**: https://console.firebase.google.com/project/research-watcher/firestore

---

**Ready to test?** Start with Step 1: Enable Firebase Authentication!
