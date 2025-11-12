# Research Watcher - Deployment Guide

Complete guide for deploying Research Watcher to production.

**Last Updated**: 2025-11-12

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Backend Deployment (Cloud Run)](#backend-deployment-cloud-run)
4. [Frontend Deployment (Firebase Hosting)](#frontend-deployment-firebase-hosting)
5. [Custom Domain Setup](#custom-domain-setup)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Rollback Procedures](#rollback-procedures)
8. [Troubleshooting](#troubleshooting)

---

## Overview

Research Watcher uses a two-tier deployment architecture:

- **Backend API**: Python Flask on Google Cloud Run
- **Frontend**: Static HTML/JS on Firebase Hosting (via Cloud Storage)

**Production URLs:**
- Frontend: https://app.researchwatcher.org
- Backend API: https://rw-api-491582996945.us-central1.run.app

---

## Prerequisites

### Required Tools

```bash
# Google Cloud SDK
gcloud --version  # Should be installed

# Firebase CLI (optional - for `firebase deploy`)
npx firebase-tools --version

# gsutil (part of gcloud)
gsutil version

# Git
git --version
```

### Required Permissions

Your GCP account needs these IAM roles:
- Cloud Run Admin
- Service Account User
- Storage Admin
- Cloud Build Editor

Verify:
```bash
gcloud auth list
# Should show: ben@getmensio.com (ACTIVE)
```

### Environment Setup

```bash
# Set project
gcloud config set project research-watcher

# Verify project
gcloud config get-value project
# Should output: research-watcher
```

---

## Backend Deployment (Cloud Run)

### Step 1: Make Code Changes

Edit files in `app/` directory:
- `app/__init__.py` - Main app factory
- `app/api/*.py` - API blueprints
- `app/services/*.py` - Business logic

### Step 2: Test Locally (Recommended)

```bash
# Activate virtual environment
source .venv/bin/activate

# Run dev server
python3 -m flask run --debug --port=5000

# Test endpoints
curl http://localhost:5000/api/topics
```

### Step 3: Build Docker Image

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/research-watcher/rw-api
```

**Expected output:**
```
DONE
----------------------------------------------------------------
ID                                    CREATE_TIME                DURATION  SOURCE
cc7a1ef0-c88d-4b90-bf36-b58ed2a6799f  2025-11-12T20:35:14+00:00  2M30S     gs://...

SUCCESS
```

**What this does:**
- Reads `Dockerfile` from current directory
- Builds Docker image with all dependencies
- Pushes to `gcr.io/research-watcher/rw-api`
- Takes ~2-3 minutes

### Step 4: Deploy to Cloud Run

```bash
# Deploy the new image
gcloud run deploy rw-api \
  --image gcr.io/research-watcher/rw-api \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated
```

**Expected output:**
```
Deploying container to Cloud Run service [rw-api] in project [research-watcher] region [us-central1]
✓ Deploying... Done.
  ✓ Creating Revision...
  ✓ Routing traffic...
Done.
Service [rw-api] revision [rw-api-00014-f6b] has been deployed and is serving 100 percent of traffic.
Service URL: https://rw-api-491582996945.us-central1.run.app
```

**What this does:**
- Creates new Cloud Run revision
- Routes 100% traffic to new revision
- Old revisions kept for rollback
- Takes ~30-60 seconds

### Step 5: Verify Backend Deployment

```bash
# Test health check
curl https://rw-api-491582996945.us-central1.run.app/

# Test authenticated endpoint (should fail with 401)
curl https://rw-api-491582996945.us-central1.run.app/api/users/profile

# Test topics API
curl https://rw-api-491582996945.us-central1.run.app/api/topics/fields
```

**Expected responses:**
- Health check: 200 OK
- Authenticated without token: 401 Unauthorized (correct!)
- Topics fields: 200 OK with JSON data

### Backend Deployment Checklist

- [ ] Code changes tested locally
- [ ] Docker image built successfully
- [ ] Cloud Run deployment succeeded
- [ ] Health check returns 200
- [ ] API endpoints responding
- [ ] No errors in Cloud Run logs

**Check logs:**
```bash
gcloud logs read --limit=20 --service=rw-api
```

---

## Frontend Deployment (Firebase Hosting)

Frontend files are deployed to a Google Cloud Storage bucket that serves Firebase Hosting.

### Step 1: Make Frontend Changes

Edit files in `public/` directory:
- `public/index.html` - Landing page
- `public/app.html` - Main application
- `public/signout.html` - Sign out page

### Step 2: Test Locally

```bash
# Serve locally
cd public
python3 -m http.server 8080

# Open in browser
open http://localhost:8080/index.html
```

Test:
- Authentication flow
- All tabs working
- API calls succeeding
- No console errors

### Step 3: Deploy to Firebase Hosting

**Method 1: Using gsutil (Recommended - Faster)**

```bash
# Deploy with no-cache headers (forces browser refresh)
gsutil -h "Cache-Control:no-cache, no-store, must-revalidate" \
  -h "Content-Type:text/html; charset=utf-8" \
  cp public/index.html gs://research-watcher-web/index.html

gsutil -h "Cache-Control:no-cache, no-store, must-revalidate" \
  -h "Content-Type:text/html; charset=utf-8" \
  cp public/app.html gs://research-watcher-web/app.html

gsutil -h "Cache-Control:no-cache, no-store, must-revalidate" \
  -h "Content-Type:text/html; charset=utf-8" \
  cp public/signout.html gs://research-watcher-web/signout.html
```

**Method 2: Using Firebase CLI (Alternative)**

```bash
# Deploy all hosting files
firebase deploy --only hosting
```

**Note:** Firebase CLI requires authentication which may not work in all environments. gsutil is more reliable.

### Step 4: Verify Frontend Deployment

```bash
# Check files in bucket
gsutil ls -lh gs://research-watcher-web/

# Check deployed file content
gsutil cat gs://research-watcher-web/app.html | head -50

# Test live site
curl https://app.researchwatcher.org/index.html | head -50
```

### Step 5: Clear CDN Cache (If Needed)

Changes may take 1-5 minutes to propagate through Cloudflare CDN.

**Force cache bypass:**
```bash
# Add cache-busting query param
curl "https://app.researchwatcher.org/app.html?v=$(date +%s)" | head -50
```

**Ask users to hard refresh:**
- Chrome/Firefox: Ctrl+Shift+R (Cmd+Shift+R on Mac)
- Or open in incognito/private window

### Frontend Deployment Checklist

- [ ] Frontend changes tested locally
- [ ] Files uploaded to gs://research-watcher-web/
- [ ] Live site shows new changes (may need hard refresh)
- [ ] Authentication still works
- [ ] All tabs functional
- [ ] No console errors in browser DevTools
- [ ] Mobile responsive design intact

---

## Custom Domain Setup

Custom domain `app.researchwatcher.org` is already configured. This section documents how it was set up.

### DNS Configuration (Already Done)

DNS records at Namecheap:
```
Type  Name    Value                       TTL
A     app     researchwatcher.org         Automatic
A     app     research-watcher.web.app    Automatic
```

### Firebase Hosting Setup (Already Done)

1. Added custom domain in Firebase Console
2. Verified domain ownership
3. SSL certificate auto-provisioned (Let's Encrypt)

### Firebase Authentication Setup

**Required for OAuth to work on custom domain:**

1. **API Key Restrictions** (gcloud):
   ```bash
   gcloud services api-keys update <KEY_ID> \
     --allowed-referrers="https://app.researchwatcher.org/*,..."
   ```

2. **Authorized Domains** (Firebase Console):
   - Go to: Authentication → Settings → Authorized domains
   - Add: `app.researchwatcher.org`

3. **authDomain Configuration** (Frontend Code):
   ```javascript
   const firebaseConfig = {
       authDomain: "app.researchwatcher.org",  // Use custom domain
       // ... other config
   };
   ```

4. **CORS Configuration** (Backend):
   ```python
   CORS(app, resources={
       r"/api/*": {
           "origins": [
               "https://app.researchwatcher.org",  # Add custom domain
               # ... other origins
           ]
       }
   })
   ```

**Verification:**
```bash
# Check SSL certificate
curl -I https://app.researchwatcher.org | grep -i "strict-transport"

# Test authentication
# 1. Go to https://app.researchwatcher.org
# 2. Sign in with Google
# 3. Should stay on app.researchwatcher.org throughout flow
```

---

## Post-Deployment Verification

### Automated Checks

```bash
# Run this script after deployment
cat > /tmp/verify_deployment.sh << 'EOF'
#!/bin/bash
set -e

echo "=== Backend Health Check ==="
curl -s https://rw-api-491582996945.us-central1.run.app/ | grep -q "Research Watcher API"
echo "✓ Backend responding"

echo ""
echo "=== Topics API Check ==="
curl -s https://rw-api-491582996945.us-central1.run.app/api/topics/fields | jq -r '.[0].display_name'
echo "✓ Topics API working"

echo ""
echo "=== Frontend Check ==="
curl -s https://app.researchwatcher.org/index.html | grep -q "Research Watcher"
echo "✓ Frontend loading"

echo ""
echo "=== App HTML Check ==="
curl -s https://app.researchwatcher.org/app.html | grep -q "📚 Topics"
echo "✓ Topics tab present"

echo ""
echo "=== All checks passed! ✓ ==="
EOF

chmod +x /tmp/verify_deployment.sh
/tmp/verify_deployment.sh
```

### Manual Testing

1. **Authentication Flow:**
   - Go to https://app.researchwatcher.org
   - Sign in with Google
   - Verify redirect stays on custom domain
   - Check user profile loads

2. **Core Features:**
   - Daily Digest tab loads papers
   - Search tab works
   - Seeds tab allows adding/removing seeds
   - Saved papers tab shows saved items
   - **Topics tab displays topic browser**

3. **API Integration:**
   - Open browser DevTools (F12)
   - Go to Network tab
   - Navigate between tabs
   - Verify API calls succeed (200 status)
   - Check no CORS errors in console

4. **Responsive Design:**
   - Test on mobile device or resize browser
   - Verify all 5 tabs visible
   - Check Topics tab scrolls/wraps properly

### Performance Verification

```bash
# Check response headers
curl -I https://app.researchwatcher.org/app.html

# Should see:
# cache-control: max-age=3600  (or similar)
# strict-transport-security: max-age=31556926
```

**Using browser:**
1. Open DevTools → Network tab
2. Disable cache
3. Reload page
4. Check:
   - Load time < 2 seconds
   - Preconnect hints in waterfall
   - Resources loading in parallel

---

## Rollback Procedures

### Rollback Backend

Cloud Run keeps previous revisions. To rollback:

**Step 1: List revisions**
```bash
gcloud run revisions list --service=rw-api --region=us-central1
```

**Step 2: Route traffic to previous revision**
```bash
# Route 100% traffic to specific revision
gcloud run services update-traffic rw-api \
  --to-revisions=rw-api-00013-abc=100 \
  --region=us-central1
```

**Step 3: Verify rollback**
```bash
curl https://rw-api-491582996945.us-central1.run.app/
# Check logs to confirm old revision responding
```

### Rollback Frontend

**Method 1: Re-upload previous version**

```bash
# Checkout previous commit
git checkout <PREVIOUS_COMMIT>

# Re-deploy old files
gsutil -h "Cache-Control:no-cache" cp public/app.html gs://research-watcher-web/app.html

# Return to latest
git checkout main
```

**Method 2: Use git to find old version**

```bash
# Show file from previous commit
git show HEAD~1:public/app.html > /tmp/app.html.old

# Upload old version
gsutil -h "Cache-Control:no-cache" cp /tmp/app.html.old gs://research-watcher-web/app.html
```

---

## Troubleshooting

### Deployment Issues

**Issue: Docker build fails**

```bash
# Check Dockerfile syntax
docker build -t test-image .

# Check requirements.txt
pip install -r requirements.txt
```

**Issue: Cloud Run deployment fails**

```bash
# Check logs
gcloud logs read --limit=20 --service=rw-api

# Common causes:
# - Missing environment variables
# - Port not exposed (should be 8080)
# - Startup timeout (increase timeout in Cloud Run)
```

**Issue: Frontend not updating**

```bash
# Verify upload succeeded
gsutil ls -lh gs://research-watcher-web/app.html

# Check file modification time (should be recent)

# Clear cache with no-cache header
gsutil -h "Cache-Control:no-cache" cp public/app.html gs://research-watcher-web/app.html

# Wait 2-3 minutes for CDN propagation
```

### For more issues, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

---

## Deployment Checklist (Full Release)

Use this checklist for major releases:

### Pre-Deployment
- [ ] Code reviewed and approved
- [ ] All tests passing locally
- [ ] MILESTONES.md updated
- [ ] CHANGELOG.md updated (if exists)
- [ ] Git commit created with clear message

### Backend Deployment
- [ ] Docker image built
- [ ] Cloud Run deployment successful
- [ ] Backend health check passes
- [ ] API endpoints tested
- [ ] No errors in logs

### Frontend Deployment
- [ ] Files uploaded to Cloud Storage
- [ ] Live site shows changes (hard refresh)
- [ ] Authentication works
- [ ] All features functional
- [ ] No console errors

### Post-Deployment
- [ ] Automated checks pass
- [ ] Manual testing complete
- [ ] Performance acceptable
- [ ] Monitoring shows no issues
- [ ] Team notified of deployment

### Documentation
- [ ] Changes documented in MILESTONES.md
- [ ] Troubleshooting guide updated if needed
- [ ] API docs updated if endpoints changed
- [ ] Git tagged if major release

---

## Quick Reference

### Common Commands

```bash
# Build & deploy backend
gcloud builds submit --tag gcr.io/research-watcher/rw-api && \
gcloud run deploy rw-api --image gcr.io/research-watcher/rw-api --region us-central1

# Deploy frontend (no cache)
for file in index.html app.html signout.html; do
  gsutil -h "Cache-Control:no-cache" cp public/$file gs://research-watcher-web/$file
done

# Check deployment status
gcloud run services describe rw-api --region=us-central1
gsutil ls -lh gs://research-watcher-web/

# View logs
gcloud logs read --limit=50 --service=rw-api

# Test endpoints
curl https://rw-api-491582996945.us-central1.run.app/api/topics/fields
curl https://app.researchwatcher.org/
```

### Key URLs

- **Frontend**: https://app.researchwatcher.org
- **Backend API**: https://rw-api-491582996945.us-central1.run.app
- **Firebase Console**: https://console.firebase.google.com/project/research-watcher
- **Cloud Run Console**: https://console.cloud.google.com/run?project=research-watcher
- **Cloud Storage**: gs://research-watcher-web/

---

## Emergency Contacts

If deployment fails in production:

1. Check logs: `gcloud logs read --service=rw-api`
2. Rollback if needed (see [Rollback Procedures](#rollback-procedures))
3. Create GitHub issue with logs and error details
4. Notify team in communication channel

---

**Last Updated**: 2025-11-12
**Maintainer**: Development Team
