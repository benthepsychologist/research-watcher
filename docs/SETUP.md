# Research Watcher - GCP/Firebase Setup Guide

This guide walks through all the infrastructure setup needed for Research Watcher Phase 0.

---

## Prerequisites

- Google Cloud Platform account with billing enabled
- `gcloud` CLI installed and authenticated
- `firebase` CLI installed (install with: `npm install -g firebase-tools`)
- Repository cloned locally

---

## Step 1: Create Firebase Project

### 1.1 Via Firebase Console

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project"
3. Enter project name: `research-watcher` (or your preferred name)
4. (Optional) Enable Google Analytics
5. Wait for project creation

### 1.2 Via CLI (Alternative)

```bash
# Login to Firebase
firebase login

# Initialize Firebase in this directory
firebase init

# Select:
# - Firestore
# - Hosting
# - Use existing project or create new one
```

---

## Step 2: Enable Firebase Services

### 2.1 Enable Firestore

1. In Firebase Console, go to **Firestore Database**
2. Click "Create database"
3. Choose **Production mode** (we have security rules)
4. Select location: `us-central1` (or your preferred region)
5. Click "Enable"

### 2.2 Enable Firebase Authentication

1. Go to **Authentication** → **Sign-in method**
2. Enable **Google** provider
   - Add authorized domain if needed
3. Enable **Email/Password** provider
4. Save changes

---

## Step 3: Enable Google Cloud APIs

Set your project ID and enable required APIs:

```bash
# Set project ID
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  pubsub.googleapis.com \
  bigquery.googleapis.com \
  cloudscheduler.googleapis.com \
  firestore.googleapis.com \
  cloudbuild.googleapis.com
```

---

## Step 4: Create Pub/Sub Topic for WAL

```bash
# Create topic for Write-Ahead Log events
gcloud pubsub topics create rw-wal

# Verify creation
gcloud pubsub topics list
```

---

## Step 5: Create BigQuery Dataset and Table

### 5.1 Create Dataset

```bash
# Create dataset
bq mk --dataset \
  --location=us-central1 \
  --description="Research Watcher event ledger" \
  ${PROJECT_ID}:research_wal
```

### 5.2 Create Events Table

**IMPORTANT**: The Pub/Sub → BigQuery subscription (created in Step 6) will auto-create the table with the required schema. However, you can pre-create it if needed:

```bash
# The Pub/Sub subscription expects this schema:
# data:JSON,subscription_name:STRING,message_id:STRING,publish_time:TIMESTAMP,attributes:JSON

# Pre-create table (optional - subscription will create it automatically)
bq mk --table \
  --time_partitioning_field=publish_time \
  --time_partitioning_type=DAY \
  --description="WAL events from Pub/Sub" \
  ${PROJECT_ID}:research_wal.events \
  data:JSON,subscription_name:STRING,message_id:STRING,publish_time:TIMESTAMP,attributes:JSON
```

**Note**: The WAL event structure (v, type, runId, uid, ts, items) will be stored inside the `data` field as JSON.

### 5.3 Verify Table

```bash
bq show research_wal.events
```

---

## Step 6: Create Pub/Sub → BigQuery Sink

### 6.1 Create Subscription with BigQuery Sink

```bash
# Create subscription that writes directly to BigQuery
# Note: The --write-metadata flag includes subscription_name, message_id, publish_time, and attributes
gcloud pubsub subscriptions create rw-wal-to-bq \
  --topic=rw-wal \
  --bigquery-table=${PROJECT_ID}:research_wal.events \
  --write-metadata
```

**Important**: The subscription will auto-create the BigQuery table if it doesn't exist, or use the existing table schema. The `data` field will contain the JSON message payload.

### 6.2 Verify Subscription

```bash
gcloud pubsub subscriptions list
```

---

## Step 7: Create Service Accounts

### 7.1 Cloud Scheduler Service Account

This account will trigger the daily collection job:

```bash
# Create service account
gcloud iam service-accounts create scheduler-invoker \
  --display-name="Cloud Scheduler Invoker for Research Watcher"

# Store the email
export SCHEDULER_SA="scheduler-invoker@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant Cloud Run Invoker role (will be used later)
# We'll do this after Cloud Run service is deployed
```

### 7.2 Cloud Run Service Account

```bash
# Create service account for Cloud Run
gcloud iam service-accounts create rw-api \
  --display-name="Research Watcher API Service Account"

# Store the email
export API_SA="rw-api@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant necessary permissions
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${API_SA}" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${API_SA}" \
  --role="roles/pubsub.publisher"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${API_SA}" \
  --role="roles/cloudtasks.enqueuer"
```

---

## Step 8: Create Local Service Account Key (Dev Only)

For local development, you need a service account key:

```bash
# Create key file
gcloud iam service-accounts keys create serviceAccountKey.json \
  --iam-account=${API_SA}

# Verify it was created
ls -la serviceAccountKey.json

# IMPORTANT: This file is git-ignored. Never commit it!
```

---

## Step 9: Configure Local Environment

### 9.1 Create `.env` file

```bash
# Copy the example
cp .env.example .env

# Edit .env with your values
nano .env
```

Update these values in `.env`:

```bash
GOOGLE_APPLICATION_CREDENTIALS=./serviceAccountKey.json
GOOGLE_CLOUD_PROJECT=your-actual-project-id
OPENALEX_EMAIL=your-email@example.com
CROSSREF_MAILTO=your-email@example.com
```

### 9.2 Install Python Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 10: Deploy Firestore Rules and Indexes

```bash
# Deploy security rules
firebase deploy --only firestore:rules

# Deploy indexes
firebase deploy --only firestore:indexes
```

---

## Step 11: Deploy Initial Cloud Run Service

### 11.1 Build and Deploy

```bash
# Set region
export REGION="us-central1"

# Build and deploy
gcloud run deploy rw-api \
  --source . \
  --platform managed \
  --region ${REGION} \
  --service-account ${API_SA} \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=${PROJECT_ID} \
  --max-instances 10 \
  --memory 512Mi \
  --timeout 300
```

### 11.2 Get Service URL

```bash
# Get the service URL
gcloud run services describe rw-api \
  --region ${REGION} \
  --format 'value(status.url)'

# Store it for later
export CLOUD_RUN_URL=$(gcloud run services describe rw-api --region ${REGION} --format 'value(status.url)')
```

---

## Step 12: Grant Scheduler Permission to Invoke Cloud Run

```bash
# Grant the scheduler service account permission to invoke the Cloud Run service
gcloud run services add-iam-policy-binding rw-api \
  --region ${REGION} \
  --member="serviceAccount:${SCHEDULER_SA}" \
  --role="roles/run.invoker"
```

---

## Step 13: Create Cloud Scheduler Job

```bash
# Create daily job at 09:00 Buenos Aires time
gcloud scheduler jobs create http collect-daily \
  --schedule="0 9 * * *" \
  --time-zone="America/Argentina/Buenos_Aires" \
  --uri="${CLOUD_RUN_URL}/api/collect/run" \
  --http-method=POST \
  --oidc-service-account-email=${SCHEDULER_SA} \
  --oidc-token-audience=${CLOUD_RUN_URL} \
  --location=${REGION}
```

### Verify Job

```bash
gcloud scheduler jobs list --location=${REGION}
```

### Test Job Manually (Optional)

```bash
gcloud scheduler jobs run collect-daily --location=${REGION}
```

---

## Step 14: Deploy Firebase Hosting

### 14.1 Update `firebase.json`

Make sure the `serviceId` in `firebase.json` matches your Cloud Run service name (`rw-api`).

### 14.2 Deploy Hosting

```bash
firebase deploy --only hosting
```

### 14.3 Get Hosting URL

```bash
firebase hosting:channel:open
```

---

## Step 15: Verify Everything Works

### 15.1 Check Cloud Run

```bash
# Should return "Hello World!" (or your current response)
curl ${CLOUD_RUN_URL}/
```

### 15.2 Check Firestore Rules

1. Go to Firebase Console → Firestore Database
2. Try to read/write from Rules Playground
3. Verify rules are enforced

### 15.3 Check BigQuery

```bash
# Verify table exists
bq show research_wal.events

# Check for any test events (will be empty initially)
bq query "SELECT COUNT(*) FROM research_wal.events"
```

### 15.4 Check Authentication

1. Go to your Firebase Hosting URL
2. Try signing in with Google
3. Verify Firebase Auth console shows the user

---

## Phase 0 Complete! 🎉

You should now have:

- ✅ Firebase project with Firestore and Auth enabled
- ✅ GCP APIs enabled (Cloud Run, Pub/Sub, BigQuery, Scheduler)
- ✅ Pub/Sub topic `rw-wal` created
- ✅ BigQuery dataset `research_wal` with `events` table
- ✅ Pub/Sub → BigQuery sink configured
- ✅ Service accounts created and configured
- ✅ Local development environment ready
- ✅ Firestore rules deployed
- ✅ Cloud Run service deployed
- ✅ Cloud Scheduler job created
- ✅ Firebase Hosting deployed

---

## Next Steps

Proceed to **Phase 1: Backend Core (API Skeleton)** in [MILESTONES.md](../MILESTONES.md).

---

## Troubleshooting

### Issue: "Permission Denied" errors

**Solution**: Verify service account has correct IAM roles:

```bash
gcloud projects get-iam-policy ${PROJECT_ID} \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:${API_SA}"
```

### Issue: BigQuery sink not receiving events

**Solution**: Check subscription:

```bash
gcloud pubsub subscriptions describe rw-wal-to-bq
```

Verify the table schema matches the subscription requirements.

### Issue: Cloud Scheduler job fails

**Solution**: Check logs:

```bash
gcloud scheduler jobs describe collect-daily --location=${REGION}
gcloud logging read "resource.type=cloud_scheduler_job" --limit 10
```

### Issue: Firestore rules deployment fails

**Solution**: Validate rules syntax:

```bash
firebase deploy --only firestore:rules --debug
```

---

## Cost Estimates (v0 @ 100 users)

- **Firestore**: ~$2/month (reads/writes)
- **Cloud Run**: ~$5/month (daily runs)
- **BigQuery**: ~$1/month (storage + queries)
- **Pub/Sub**: <$1/month (messages)
- **Cloud Scheduler**: <$1/month (jobs)
- **Firebase Hosting**: Free tier

**Total**: ~$10-20/month for 100 active users

---

## Security Checklist

Before going to production:

- [ ] Service account keys are NOT in source control
- [ ] `.env` is git-ignored
- [ ] Firestore rules deployed and tested
- [ ] Cloud Run has proper IAM restrictions
- [ ] Cloud Scheduler uses OIDC authentication
- [ ] No hardcoded secrets in code
- [ ] All external API keys stored in environment variables
- [ ] Billing alerts configured

---

**Last Updated**: 2025-11-06
