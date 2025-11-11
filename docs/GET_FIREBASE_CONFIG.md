# Get Firebase Web App Configuration

## Problem
The Firebase API key in the code is invalid and needs to be replaced with the correct configuration from your Firebase project.

## Solution: Get Config from Firebase Console

### Step 1: Access Firebase Console
1. Go to: https://console.firebase.google.com/project/research-watcher/settings/general
2. Scroll down to **"Your apps"** section

### Step 2: Check if Web App Exists
- Look for a web app (icon looks like `</>`).
- If you see one, click the **"Config"** radio button to view its configuration
- If no web app exists, continue to Step 3

### Step 3: Create Web App (if needed)
1. Click **"Add app"** button
2. Select the **Web** platform icon (`</>`)
3. Enter app nickname: `Research Watcher Web`
4. **Check** the box: "Also set up Firebase Hosting"
5. Click **"Register app"**

### Step 4: Copy Firebase Configuration
You'll see a code snippet like this:

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

**Copy this entire `firebaseConfig` object.**

### Step 5: Update Frontend Files

Update **TWO files** with the correct configuration:

#### File 1: `public/index.html`

Find lines ~123-130 and replace with your config:

```javascript
// Firebase configuration
const firebaseConfig = {
    apiKey: "YOUR_ACTUAL_API_KEY_HERE",
    authDomain: "research-watcher.firebaseapp.com",
    projectId: "research-watcher",
    storageBucket: "research-watcher.firebasestorage.app",
    messagingSenderId: "491582996945",
    appId: "YOUR_ACTUAL_APP_ID_HERE"
};
```

#### File 2: `public/app.html`

Find lines ~123-130 and replace with the **same config**:

```javascript
// Firebase configuration
const firebaseConfig = {
    apiKey: "YOUR_ACTUAL_API_KEY_HERE",
    authDomain: "research-watcher.firebaseapp.com",
    projectId: "research-watcher",
    storageBucket: "research-watcher.firebasestorage.app",
    messagingSenderId: "491582996945",
    appId: "YOUR_ACTUAL_APP_ID_HERE"
};
```

### Step 6: Deploy Updated Files

```bash
# Deploy updated HTML files to Cloud Storage
gsutil -m cp public/index.html public/app.html gs://research-watcher-web/
```

### Step 7: Test Sign-In

1. Visit: https://storage.googleapis.com/research-watcher-web/index.html
2. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)
3. Click "Get Started"
4. Google Sign-In popup should appear (no errors)

## Alternative: Use Firebase CLI (Advanced)

If you have Firebase CLI installed locally:

```bash
# Install Firebase CLI (if not installed)
npm install -g firebase-tools

# Login to Firebase
firebase login

# Get the config
firebase apps:sdkconfig web
```

This will print the correct Firebase configuration for your web app.

## Why This Happened

The API key `AIzaSyB4YJl0zYqP9LzQxH_3wKZ9X7nX8RLqYxQ` in the code was either:
1. A placeholder/example key
2. From a different Firebase project
3. Revoked or never created

Firebase web app configurations cannot be generated programmatically without proper IAM permissions, so manual retrieval from the console is the standard approach.

## Security Note

Firebase API keys are **safe to include in client-side code**. They identify your Firebase project but do not grant access - that's controlled by Firebase Security Rules and Authentication. See: https://firebase.google.com/docs/projects/api-keys

---

**Once you've updated the config and deployed, the sign-in flow should work correctly!**
