# Firebase Auth Setup Guide

## Enable Firebase Authentication

To enable Google Sign-In for Research Watcher, follow these steps:

### 1. Go to Firebase Console
Visit: https://console.firebase.google.com/project/research-watcher/authentication/providers

### 2. Enable Google Provider
1. Click on **"Authentication"** in the left sidebar
2. Click on **"Sign-in method"** tab
3. Click on **"Google"** provider
4. Toggle **"Enable"** to ON
5. Set **Project support email** to: `ben@getmensio.com`
6. Click **"Save"**

### 3. Add Authorized Domains
In the **"Settings"** tab under Authentication:
1. Add to **Authorized domains**:
   - `research-watcher.firebaseapp.com`
   - `research-watcher.web.app`
   - `storage.googleapis.com`
   - `localhost` (for development)

### 4. Optional: Enable Email/Password
1. Click on **"Email/Password"** provider
2. Toggle **"Enable"** to ON
3. Click **"Save"**

## Testing Authentication

### Manual Test (Browser)
1. Navigate to: https://storage.googleapis.com/research-watcher-web/index.html
2. Click **"Get Started"** button
3. Should see Google Sign-In popup
4. Sign in with your Google account
5. Should redirect to `/app.html` after successful sign-in

### Check User Creation
After signing in, verify user was created in Firestore:

```bash
# Check if user document exists
gcloud firestore collections documents list users --project=research-watcher --limit=10
```

### Get Firebase ID Token (for API testing)
Use browser console after signing in:

```javascript
firebase.auth().currentUser.getIdToken().then(token => {
  console.log('Token:', token);
  // Copy this token for API testing
});
```

### Test API Endpoints with Auth

```bash
# Set your Firebase ID token
export FIREBASE_TOKEN="<your-token-here>"

# Test user sync
curl -X POST \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  https://rw-api-491582996945.us-central1.run.app/api/users/sync

# Test seeds endpoint
curl -X GET \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  https://rw-api-491582996945.us-central1.run.app/api/seeds

# Test search endpoint
curl -X GET \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  "https://rw-api-491582996945.us-central1.run.app/api/search?q=machine+learning&max_results=5"
```

## Troubleshooting

### Error: "auth/operation-not-allowed"
- Firebase Auth provider not enabled. Follow steps above to enable Google provider.

### Error: "auth/unauthorized-domain"
- Domain not authorized. Add domain to Authorized domains list in Firebase Console.

### Error: "401 Unauthorized" from API
- Token expired or invalid
- Get new token from browser console
- Make sure Authorization header format is: `Bearer <token>`

### CORS Error
- Check that origin is in allowed CORS list in Flask app
- Currently allowed:
  - `https://storage.googleapis.com`
  - `https://research-watcher-491582996945.web.app`
  - `http://localhost:5000`

## Current Deployment URLs

- **Landing Page**: https://storage.googleapis.com/research-watcher-web/index.html
- **App**: https://storage.googleapis.com/research-watcher-web/app.html
- **API**: https://rw-api-491582996945.us-central1.run.app
- **Firebase Console**: https://console.firebase.google.com/project/research-watcher

## Next Steps After Auth is Enabled

1. Test sign-in flow manually
2. Add first research seeds via UI
3. Trigger collector to generate digest
4. Test search functionality
5. Verify all CRUD operations work

## Security Notes

- Firebase ID tokens expire after 1 hour
- Backend validates tokens using Firebase Admin SDK
- All API endpoints (except health check) require authentication
- Service account has restricted permissions (Firestore, Pub/Sub only)
