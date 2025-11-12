# Research Watcher - Troubleshooting Guide

This guide documents common issues and their solutions.

**Last Updated**: 2025-11-12

---

## Table of Contents

1. [Authentication Issues](#authentication-issues)
2. [Performance Issues](#performance-issues)
3. [UI/Display Issues](#uidisplay-issues)
4. [Deployment Issues](#deployment-issues)
5. [API Issues](#api-issues)

---

## Authentication Issues

### Issue: Firebase Authentication Blocked on Custom Domain

**Date Encountered**: 2025-11-12

**Symptoms**:
```
Firebase: Error (auth/requests-from-referer-https://app.researchwatcher.org-are-blocked.)
```
- Users cannot sign in via Google OAuth
- Error appears immediately when trying to authenticate
- Works on other domains (firebaseapp.com, web.app) but not custom domain

**Root Cause**:
Custom domain `app.researchwatcher.org` was not authorized for Firebase operations in three places:
1. Firebase API key HTTP referrer restrictions
2. Backend CORS configuration
3. Firebase authorized domains list

**Solution**:

**Step 1: Update Firebase API Key Restrictions**

```bash
# List API keys
gcloud services api-keys list --project=research-watcher

# Update the Firebase Browser key
gcloud services api-keys update <KEY_ID> \
  --allowed-referrers="https://app.researchwatcher.org/*,https://storage.googleapis.com/*,https://research-watcher.firebaseapp.com/*,https://research-watcher.web.app/*,http://localhost:*,http://127.0.0.1:*"
```

**Step 2: Update Backend CORS Configuration**

In `app/__init__.py`, add custom domain to allowed origins:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://app.researchwatcher.org",  # ADD THIS
            "https://research-watcher.firebaseapp.com",
            "https://research-watcher.web.app",
            # ... other origins
        ],
        # ... other config
    }
})
```

Deploy updated backend:
```bash
gcloud builds submit --tag gcr.io/research-watcher/rw-api
gcloud run deploy rw-api --image gcr.io/research-watcher/rw-api --region us-central1
```

**Step 3: Add to Firebase Authorized Domains**

1. Go to [Firebase Console → Authentication → Settings](https://console.firebase.google.com/project/research-watcher/authentication/settings)
2. Scroll to "Authorized domains"
3. Click "Add domain"
4. Enter: `app.researchwatcher.org`
5. Click "Add"

**Verification**:
```bash
# Test authentication
curl -X POST https://app.researchwatcher.org/api/users/profile \
  -H "Authorization: Bearer <FIREBASE_TOKEN>"
```

**Git Commit**: `84a4fc6`

---

### Issue: Auth Redirect to Wrong Domain After Login

**Date Encountered**: 2025-11-12

**Symptoms**:
- After successful Google sign-in, user is redirected to `research-watcher.firebaseapp.com` or `googleapis.com` instead of staying on `app.researchwatcher.org`
- Authentication works, but UX is confusing

**Root Cause**:
Firebase `authDomain` configuration in frontend code pointed to old Firebase Hosting domain instead of custom domain.

**Solution**:

Update `authDomain` in both frontend files:

**File**: `public/index.html` and `public/app.html`

```javascript
const firebaseConfig = {
    apiKey: "AIzaSyAvDgfpoQQkOpCF2XpLTVshRBJeLGXztOU",
    authDomain: "app.researchwatcher.org",  // Changed from research-watcher.firebaseapp.com
    projectId: "research-watcher",
    // ... rest of config
};
```

Deploy:
```bash
gsutil -h "Cache-Control:no-cache, no-store, must-revalidate" \
  cp public/index.html gs://research-watcher-web/index.html

gsutil -h "Cache-Control:no-cache, no-store, must-revalidate" \
  cp public/app.html gs://research-watcher-web/app.html
```

**Verification**:
1. Sign out completely
2. Clear browser cache
3. Go to https://app.researchwatcher.org
4. Sign in with Google
5. Verify you stay on app.researchwatcher.org throughout the flow

**Git Commit**: `bcede62`

---

## Performance Issues

### Issue: Slow Page Load Times (2-3 seconds)

**Date Encountered**: 2025-11-12

**Symptoms**:
- Initial page load takes 2-3 seconds
- White screen during loading
- External resources (Tailwind, HTMX, Firebase) load slowly
- Poor perceived performance on mobile

**Root Cause**:
Multiple performance issues:
1. No DNS/TLS preconnect hints for external CDNs
2. All scripts loaded synchronously (blocking HTML parsing)
3. Poor caching headers (only 1 hour cache)
4. No resource optimization

**Solution**:

**Fix 1: Add Preconnect Hints**

In `public/app.html` `<head>`:

```html
<!-- Preconnect to external resources -->
<link rel="preconnect" href="https://cdn.tailwindcss.com">
<link rel="preconnect" href="https://unpkg.com">
<link rel="preconnect" href="https://www.gstatic.com">
<link rel="preconnect" href="https://rw-api-491582996945.us-central1.run.app">
```

**Fix 2: Defer Non-Critical Scripts**

```html
<!-- HTMX (deferred - not critical for initial render) -->
<script defer src="https://unpkg.com/htmx.org@1.9.10"></script>

<!-- Firebase SDK (critical for auth - not deferred) -->
<script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.7.1/firebase-auth-compat.js"></script>
```

**Fix 3: Aggressive Caching Headers**

In `firebase.json`:

```json
{
  "hosting": {
    "headers": [
      {
        "source": "**/*.@(js|css)",
        "headers": [{
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }]
      },
      {
        "source": "**/*.@(jpg|jpeg|gif|png|webp|svg|ico)",
        "headers": [{
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }]
      },
      {
        "source": "**/*.html",
        "headers": [{
          "key": "Cache-Control",
          "value": "public, max-age=300, must-revalidate"
        }]
      }
    ]
  }
}
```

**Results**:
- Load time improved from 2-3s → 1-1.5s (40-50% improvement)
- Subsequent loads much faster due to caching
- Better perceived performance with preconnect

**Verification**:
```bash
# Check response headers
curl -I https://app.researchwatcher.org/app.html | grep -i cache-control

# Test with browser DevTools
# Open Network tab, disable cache, reload
# Should see preconnect in waterfall
```

**Git Commit**: `84a4fc6`

**Future Improvements**:
- Extract inline JS to separate files (enable better caching)
- Build Tailwind CSS locally (reduce from 500KB to ~10KB)
- Add service worker for offline support
- Implement code splitting (lazy load tabs)

---

## UI/Display Issues

### Issue: Topics Tab Not Visible on Navigation Bar

**Date Encountered**: 2025-11-12

**Symptoms**:
- Only 4 tabs visible (Digest, Search, Seeds, Saved)
- Topics tab (📚 Topics) missing from navigation
- Issue occurs on smaller screens or when browser window is narrow
- Tab exists in HTML but not displayed

**Root Cause**:
Tab navigation container used `flex space-x-8` without wrapping. On screens where 5 tabs don't fit horizontally, the 5th tab was pushed outside the visible area with no way to scroll or wrap.

**Solution**:

In `public/app.html`, update tab navigation container:

```html
<!-- Before -->
<div class="flex space-x-8" role="tablist">

<!-- After -->
<div class="flex flex-wrap space-x-4 sm:space-x-8 -mb-px overflow-x-auto" role="tablist">
```

**Changes**:
- `flex-wrap`: Allows tabs to wrap to next line if needed
- `overflow-x-auto`: Enables horizontal scrolling if tabs overflow
- `space-x-4 sm:space-x-8`: Responsive spacing (smaller on mobile, larger on desktop)
- `-mb-px`: Fixes border alignment when tabs wrap

**Verification**:
1. Resize browser window to various widths
2. Check on mobile devices
3. All 5 tabs should be visible (scroll horizontally if needed)
4. Click Topics tab to verify functionality

**Git Commit**: `84a4fc6`

---

## Deployment Issues

### Issue: Changes Not Visible After Deployment

**Symptoms**:
- Code deployed but users see old version
- Hard refresh doesn't help
- Incognito mode shows new version

**Likely Causes**:
1. **CDN/Browser caching**: Old files cached by Cloudflare or browser
2. **Wrong cache headers**: Files cached too aggressively
3. **Deployment to wrong location**: Files uploaded but not to active bucket

**Solutions**:

**For HTML files (should not be cached long):**
```bash
# Deploy with no-cache headers to force refresh
gsutil -h "Cache-Control:no-cache, no-store, must-revalidate" \
  cp public/app.html gs://research-watcher-web/app.html
```

**For JS/CSS files (can be cached long with versioning):**
```bash
# Use versioned filenames
# app.js → app.v2.js
gsutil -h "Cache-Control:public, max-age=31536000, immutable" \
  cp public/app.v2.js gs://research-watcher-web/app.v2.js
```

**Verify deployment:**
```bash
# Check file timestamp in bucket
gsutil ls -lh gs://research-watcher-web/app.html

# Check live site (bypass cache)
curl -H "Cache-Control: no-cache" https://app.researchwatcher.org/app.html | head -50

# Check cache headers
curl -I https://app.researchwatcher.org/app.html | grep -i cache
```

**Wait for CDN propagation:**
- Cloudflare CDN may take 1-5 minutes to update
- Users may need to wait or hard refresh (Ctrl+Shift+R)

---

## API Issues

### Issue: CORS Errors When Calling API

**Symptoms**:
```
Access to fetch at 'https://rw-api-xxx.run.app/api/...' from origin 'https://app.researchwatcher.org'
has been blocked by CORS policy
```

**Root Cause**:
Origin not in backend CORS allowed origins list.

**Solution**:

Update `app/__init__.py`:

```python
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://app.researchwatcher.org",  # Add missing origin
            # ... other origins
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})
```

Redeploy backend:
```bash
gcloud builds submit --tag gcr.io/research-watcher/rw-api
gcloud run deploy rw-api --image gcr.io/research-watcher/rw-api --region us-central1
```

**Verification**:
```bash
# Check CORS headers
curl -H "Origin: https://app.researchwatcher.org" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     https://rw-api-491582996945.us-central1.run.app/api/topics

# Should see:
# Access-Control-Allow-Origin: https://app.researchwatcher.org
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
```

---

## API Issues

### Issue: 401 Unauthorized When Calling API

**Symptoms**:
```json
{"error": "unauthorized", "message": "Missing Authorization header"}
```

**Causes**:
1. Missing Authorization header
2. Invalid/expired Firebase token
3. Token audience mismatch

**Solutions**:

**Check if token is being sent:**
```javascript
// In browser DevTools console
console.log(localStorage.getItem('token'));

// Should see a long JWT string starting with "eyJ..."
```

**Refresh token:**
```javascript
// Force token refresh
firebase.auth().currentUser.getIdToken(true)
  .then(token => {
    localStorage.setItem('token', token);
    console.log('Token refreshed');
  });
```

**Verify token is valid:**
```bash
# Decode JWT (using jwt.io or jwt-cli)
echo "<TOKEN>" | jwt decode
```

**Check token audience:**
- Token `aud` field should match `projectId` in Firebase config
- Our project: `aud` should be `"research-watcher"` (NOT `"research-watcher-491582996945"`)

---

## Getting Help

If you encounter an issue not covered here:

1. **Check logs:**
   ```bash
   # Backend logs
   gcloud logs read --limit=50 --service=rw-api

   # Browser console (F12)
   # Look for errors in Console and Network tabs
   ```

2. **Verify configuration:**
   - Firebase config in frontend matches project
   - CORS origins include your domain
   - API key restrictions allow your domain

3. **Test in isolation:**
   - Use curl to test API directly
   - Check auth in incognito mode
   - Test on different device/network

4. **Create GitHub issue** with:
   - Symptoms (what's happening)
   - Expected behavior (what should happen)
   - Steps to reproduce
   - Relevant logs/screenshots
   - Browser/environment info

---

## Quick Reference

### Common Commands

```bash
# Deploy backend
gcloud builds submit --tag gcr.io/research-watcher/rw-api
gcloud run deploy rw-api --image gcr.io/research-watcher/rw-api --region us-central1

# Deploy frontend (no cache)
gsutil -h "Cache-Control:no-cache, no-store, must-revalidate" \
  cp public/app.html gs://research-watcher-web/app.html

# Check API key restrictions
gcloud services api-keys list --project=research-watcher

# View backend logs
gcloud logs read --limit=50 --service=rw-api --project=research-watcher

# Test API endpoint
curl -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  https://rw-api-491582996945.us-central1.run.app/api/topics
```

### Useful Links

- [Firebase Console](https://console.firebase.google.com/project/research-watcher)
- [Cloud Run Console](https://console.cloud.google.com/run?project=research-watcher)
- [API Keys Console](https://console.cloud.google.com/apis/credentials?project=research-watcher)
- [Custom Domain: app.researchwatcher.org](https://app.researchwatcher.org)
- [Backend API: rw-api-491582996945.us-central1.run.app](https://rw-api-491582996945.us-central1.run.app)
