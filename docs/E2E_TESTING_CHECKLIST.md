# End-to-End Testing Checklist

This document provides a comprehensive checklist for testing the complete Research Watcher user journey after Firebase Auth has been enabled.

## Prerequisites

### 1. Enable Firebase Authentication
Follow the steps in [FIREBASE_AUTH_SETUP.md](./FIREBASE_AUTH_SETUP.md) to:
- ✅ Enable Google Sign-In provider
- ✅ Add authorized domains
- ✅ Set support email

### 2. Verify Deployment
Check that all components are deployed:
- ✅ Frontend: https://storage.googleapis.com/research-watcher-web/index.html
- ✅ API: https://rw-api-491582996945.us-central1.run.app/
- ✅ Firestore: `users/`, `seeds/`, `papers/`, `digests/` collections exist
- ✅ Pub/Sub: `rw-wal` topic exists

## Manual Frontend Testing

### Phase 1: Landing Page & Authentication

1. **Landing Page Load**
   - [ ] Navigate to: https://storage.googleapis.com/research-watcher-web/index.html
   - [ ] Page loads without errors
   - [ ] "Get Started" button is visible
   - [ ] Features list displays correctly
   - [ ] Status shows "Limited Alpha! Phase 2 complete"

2. **Google Sign-In Flow**
   - [ ] Click "Get Started" button
   - [ ] Google Sign-In popup appears
   - [ ] Select Google account
   - [ ] Grant permissions
   - [ ] Popup closes automatically
   - [ ] Redirects to `/app.html`

3. **User Creation Verification**
   - [ ] Open browser console (F12)
   - [ ] Check for Firebase auth state: `firebase.auth().currentUser`
   - [ ] Verify user object has `uid`, `email`, `displayName`
   - [ ] Check Firestore for user document:
     ```bash
     gcloud firestore documents list users --project=research-watcher --limit=10
     ```

### Phase 2: Authenticated App (`/app.html`)

4. **App Page Load**
   - [ ] App page loads successfully
   - [ ] User info displayed in header (email/name)
   - [ ] Four tabs visible: Digest | Search | Seeds | Saved
   - [ ] No authentication errors in console
   - [ ] Sign Out button visible

5. **Seeds Tab (Initial State)**
   - [ ] Click "Seeds" tab
   - [ ] Empty state message: "No seeds yet. Add research interests..."
   - [ ] Input field and "Add Seeds" button visible
   - [ ] Placeholder text: "e.g., machine learning, quantum computing"

6. **Add Seeds**
   - [ ] Enter seeds: "machine learning, transformer models, attention mechanisms"
   - [ ] Click "Add Seeds"
   - [ ] Seeds appear in list instantly (HTMX partial update)
   - [ ] Input field clears
   - [ ] Success message displayed (optional)
   - [ ] Refresh page - seeds persist

7. **Remove Seeds**
   - [ ] Click "×" button next to a seed
   - [ ] Seed removed from list instantly
   - [ ] Firestore updated (verify in console or refresh page)

### Phase 3: Interactive Search

8. **Search Tab**
   - [ ] Click "Search" tab
   - [ ] Search input field visible
   - [ ] Placeholder: "Search for papers..."
   - [ ] Default filters visible: Last 7 days, Top 20 results

9. **Perform Search**
   - [ ] Enter query: "transformer models"
   - [ ] Click "Search" or press Enter
   - [ ] Loading indicator appears
   - [ ] Results load within 3-5 seconds
   - [ ] Paper cards display with:
     - [ ] Title
     - [ ] Authors
     - [ ] Venue/publication
     - [ ] Abstract (truncated)
     - [ ] Citations count
     - [ ] Publication date
     - [ ] Score
     - [ ] "Read Paper" link (opens in new tab)
     - [ ] "Save" button

10. **Search Filters**
    - [ ] Change "Days back" to 30
    - [ ] Change "Max results" to 10
    - [ ] Re-run search
    - [ ] Results reflect new filters

11. **Empty Search**
    - [ ] Search for gibberish: "xyzabc123nonexistent"
    - [ ] Empty state message: "No papers found"
    - [ ] No errors in console

### Phase 4: Digest Tab

12. **Run Collector First**
    - [ ] Use cURL or run collector endpoint:
      ```bash
      export FIREBASE_TOKEN="<your-token>"
      curl -X POST \
        -H "Authorization: Bearer $FIREBASE_TOKEN" \
        https://rw-api-491582996945.us-central1.run.app/api/collect/run
      ```
    - [ ] Wait for collector to finish (~30-60 seconds)
    - [ ] Verify papers collected in response

13. **View Digest**
    - [ ] Click "Digest" tab
    - [ ] Papers load automatically
    - [ ] Papers sorted by score (highest first)
    - [ ] Top papers are relevant to your seeds
    - [ ] Digest updates daily (check `generatedAt` timestamp)

14. **Digest Metadata**
    - [ ] Generation timestamp displayed
    - [ ] Paper count displayed
    - [ ] Source seeds indicated (if shown in UI)

### Phase 5: Save Functionality

15. **Save Papers**
    - [ ] From Search tab, click "Save" on a paper
    - [ ] Button changes state (e.g., "Saved" or checkmark)
    - [ ] Switch to "Saved" tab
    - [ ] Saved paper appears in list
    - [ ] Refresh page - paper still saved

16. **Unsave Papers**
    - [ ] Click "Remove" or "Unsave" button
    - [ ] Paper removed from Saved list
    - [ ] Return to Search - button shows "Save" again

### Phase 6: Session Persistence

17. **Auth State Persistence**
    - [ ] Close browser tab
    - [ ] Reopen: https://storage.googleapis.com/research-watcher-web/index.html
    - [ ] Automatically redirects to `/app.html` (still signed in)
    - [ ] Seeds, saved papers, and digest persist

18. **Sign Out**
    - [ ] Click "Sign Out" button
    - [ ] Redirects to landing page (`/index.html`)
    - [ ] Sign in again - all data still present

## Automated API Testing

### Get Firebase Token
```javascript
// In browser console after signing in
firebase.auth().currentUser.getIdToken().then(token => {
  console.log('Token:', token);
});
```

### Run E2E Test Script
```bash
export FIREBASE_TOKEN="<your-token-from-above>"
./scripts/test_e2e_auth.sh
```

Expected output:
- ✅ All 7 tests pass
- ✅ Health check: healthy
- ✅ User sync: UID returned
- ✅ Seeds: CRUD operations work
- ✅ Search: Papers returned
- ✅ Collector: Papers collected
- ✅ Digest: Papers retrieved

## API Testing with cURL

### 1. User Sync
```bash
curl -X POST \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  https://rw-api-491582996945.us-central1.run.app/api/users/sync
```
Expected: `{"uid": "...", "email": "...", "seeds": []}`

### 2. Get Seeds
```bash
curl -X GET \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  https://rw-api-491582996945.us-central1.run.app/api/seeds
```
Expected: `{"seeds": [...]}`

### 3. Add Seeds
```bash
curl -X POST \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"items":["machine learning","quantum computing"]}' \
  https://rw-api-491582996945.us-central1.run.app/api/seeds
```
Expected: `{"seeds": ["machine learning", "quantum computing", ...]}`

### 4. Interactive Search
```bash
curl -X GET \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  "https://rw-api-491582996945.us-central1.run.app/api/search?q=transformer+models&max_results=5&days_back=7"
```
Expected: `{"papers": [...], "count": 5, "query": "transformer models", "durationMs": ...}`

### 5. Run Collector
```bash
curl -X POST \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  https://rw-api-491582996945.us-central1.run.app/api/collect/run
```
Expected: `{"message": "Collection complete", "stats": {"usersProcessed": 1, "papersCollected": ...}}`

### 6. Get Latest Digest
```bash
curl -X GET \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  https://rw-api-491582996945.us-central1.run.app/api/digest/latest
```
Expected: `{"papers": [...], "generatedAt": "...", "userId": "..."}`

## Verification Checklist

### Data Integrity
- [ ] User document created in `users/{uid}` with correct fields
- [ ] Seeds stored in `users/{uid}/seeds` subcollection
- [ ] Papers stored in `papers/` collection (sanitized IDs)
- [ ] Digest document created: `digests/{uid}_latest`
- [ ] Search events tracked in `events/{uid}/searches/`

### BigQuery WAL Events
```bash
# Check WAL events landed in BigQuery
bq query --use_legacy_sql=false \
  "SELECT * FROM \`research-watcher.rw_analytics.rw_wal\`
   ORDER BY publishTime DESC
   LIMIT 10"
```
Expected events:
- `seed.added`
- `search.executed`
- `digest.generated`
- `feedback.submitted`

### Performance
- [ ] Search completes in < 5 seconds
- [ ] Collector processes 1 user in < 60 seconds
- [ ] Digest loads in < 2 seconds
- [ ] HTMX updates feel instant (< 500ms)

### Error Handling
- [ ] Expired token: Returns 401 with clear message
- [ ] Invalid query: Returns 400 with validation error
- [ ] Network error: UI shows error message, doesn't crash
- [ ] Empty results: Shows empty state, not error

## Known Issues & Limitations

### Current Limitations
- **Semantic Scholar Rate Limiting**: Using own API key during alpha (1 req/sec)
- **No Email Notifications**: Digest is view-only, no email delivery yet
- **No Paper Deduplication UI**: Duplicates may appear across sources
- **No Export Functionality**: Can't export digest to PDF/email

### Browser Compatibility
- Tested on: Chrome, Firefox, Safari (latest versions)
- HTMX requires modern browser with JavaScript enabled
- Popup blockers must allow Google Sign-In popup

## Troubleshooting

### "auth/operation-not-allowed"
**Cause**: Firebase Auth provider not enabled
**Fix**: Follow [FIREBASE_AUTH_SETUP.md](./FIREBASE_AUTH_SETUP.md)

### "auth/unauthorized-domain"
**Cause**: Domain not in authorized list
**Fix**: Add `storage.googleapis.com` to Firebase Console → Authentication → Settings → Authorized domains

### "401 Unauthorized" from API
**Cause**: Token expired or invalid
**Fix**: Get new token from browser console (tokens expire after 1 hour)

### CORS Error
**Cause**: Origin not allowed
**Fix**: Verify Flask CORS config includes your origin in [`app/__init__.py:38-52`](../app/__init__.py#L38-L52)

### Papers Not Loading
**Cause**: Collector hasn't run yet
**Fix**: Run collector manually or wait for scheduled run

### Search Returns 0 Results
**Cause**: Query too specific or days_back too narrow
**Fix**: Increase `days_back` to 30 or 90, try broader query

## Success Criteria

Phase 3 is complete when:
- ✅ User can sign in with Google
- ✅ User can add/remove research seeds
- ✅ User can search papers interactively
- ✅ User can view personalized digest
- ✅ User can save papers for later
- ✅ All API endpoints work with authentication
- ✅ HTMX provides smooth, instant UI updates
- ✅ No critical errors in browser console
- ✅ WAL events landing in BigQuery

## Next Phase Preview

After Phase 3 is validated:
- **Phase 4**: Email delivery (SendGrid integration)
- **Phase 5**: Scaling & optimization (caching, batching)
- **Phase 6**: Advanced features (export, sharing, comments)
