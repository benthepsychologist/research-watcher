---
version: "1.0"
tier: A
title: Enhanced Discovery - Feed, Reading Lists & Source Explorer
owner: benthepsychologist
goal: Transform Research Watcher into an Instagram-like research feed with Web of Science source exploration, reading lists, and transparent algorithmic feed
labels: [feature, discovery, feed, ux, personalization]
orchestrator_contract: "standard"
repo:
  working_branch: "feat/enhanced-discovery"
---

# Enhanced Discovery: Feed, Reading Lists & Source Explorer

## Objective

Transform Research Watcher from a simple daily digest viewer into a rich discovery platform with:
1. **Instagram-like Feed**: Infinite-scroll paper feed with personalized ranking
2. **Reading Lists**: Multiple curated collections (To Read, Currently Reading, Favorites, Archive)
3. **Source Explorer**: Web of Science-style navigation through citations, authors, venues, and topics
4. **Transparent Algorithms**: User-configurable feed ranking with explanations
5. **Social Features** (Optional): Follow authors, share papers, collaborative lists

This is a major UX evolution beyond the basic Phase 3 interface, creating a modern research discovery experience.

## Acceptance Criteria

### Core Features
- [ ] Infinite-scroll feed with pagination and lazy loading
- [ ] Multiple reading list types (To Read, Reading, Favorites, Archive)
- [ ] Drag-and-drop paper organization between lists
- [ ] Source explorer with citation graph visualization
- [ ] Configurable feed algorithm (citations vs recency vs novelty)
- [ ] Algorithm transparency UI (why this paper?)
- [ ] Mobile-responsive design (touch gestures, swipe actions)

### Performance
- [ ] Feed loads < 1s (first 20 papers)
- [ ] Pagination fetches < 300ms
- [ ] Smooth 60fps scroll on mobile
- [ ] Optimistic UI updates (instant feedback)

### Data
- [ ] Citation data ingested from Semantic Scholar
- [ ] Author profiles with h-index, affiliation
- [ ] Venue rankings and impact factors
- [ ] Topic clustering (LDA or embeddings-based)

### Testing
- [ ] End-to-end tests for feed pagination
- [ ] Unit tests for ranking algorithms
- [ ] Mobile device testing (iOS Safari, Android Chrome)
- [ ] Accessibility: keyboard navigation, screen readers

## Context

### Background

**Current State (Phase 3):**
- Tab-based interface: Digest | Search | Seeds | Saved
- Single "Saved Papers" list (flat, no organization)
- No feed concept - just static digest + search results
- No exploration beyond individual papers
- No citation network or author profiles
- Basic save/remove actions only

**User Vision:**
> "I want it to be like Instagram for research papers - an infinite feed I can scroll through, save to different reading lists, explore citations and related work, and understand why the algorithm showed me each paper. Like Web of Science but actually nice to use."

**Why This Work is Needed:**
1. **Discovery Fatigue**: Users overwhelmed by daily digest dumps
2. **Organization**: Need to triage papers (to-read vs reading vs favorites)
3. **Serendipity**: Feed enables casual browsing, not just targeted search
4. **Trust**: Transparent algorithms build user confidence
5. **Engagement**: Modern UX patterns (infinite scroll, gestures) keep users coming back
6. **Network Effects**: Citation/author exploration creates deeper engagement

### Constraints

- Cannot break existing Phase 3 functionality (daily digest, search, seeds)
- Must work on mobile (majority of research reading happens on tablets/phones)
- Feed algorithm must be fast (< 100ms per paper score)
- Citation data fetching must respect S2 API rate limits
- Reading lists stored in Firestore subcollections (not separate tables)
- Budget: Stay under $30/month total (including infrastructure costs)

## Plan

### Phase 1: Feed Architecture & Backend

**Goal:** Build feed generation API and pagination infrastructure

**Tasks:**

1. **Feed Generation Endpoint**
   - Endpoint: `GET /api/feed`
   - Query params: `?page=1&limit=20&algorithm=balanced`
   - Algorithm modes:
     - `balanced`: Mix of citations (40%), recency (30%), relevance (30%)
     - `citations`: Sort by citation count (for established work)
     - `recency`: Sort by publication date (for latest research)
     - `novelty`: Favor papers with < 50 citations but high score (hidden gems)
   - Return: `{ papers: [...], nextPage: 2, hasMore: true, algorithm: "balanced" }`
   - Performance: Pre-compute scores, cache in Firestore

2. **Feed Data Model**
   - Collection: `feed_cache/{uid}/papers/{paperId}`
   - Fields: `{ ...paper, feedScore, rank, lastUpdated }`
   - Indexes: `(userId, feedScore DESC)`, `(userId, lastUpdated DESC)`
   - TTL: 24 hours (rebuild on daily collector run)
   - Size estimate: 100 users × 50 papers × 2KB = 10MB

3. **Pagination Logic**
   - Cursor-based pagination (not offset-based)
   - Store cursor in response: `nextCursor: "base64(timestamp|score)"`
   - Client sends cursor in next request
   - Firestore query: `startAfter(cursor).limit(20)`
   - Prevents page drift when new papers added

4. **Algorithm Transparency**
   - Each paper includes: `{ ..., rankingReason: "High citations (150) + Recent (2024)" }`
   - Template: `{factor1} ({value1}) + {factor2} ({value2})`
   - Factors: citations, recency, relevance to seeds, OA, venue prestige
   - Show in UI as tooltip or expandable card section

5. **Prefetch Next Page**
   - Client prefetches page N+1 when user scrolls to 75% of page N
   - Use `fetch()` with low priority
   - Store in client-side cache (sessionStorage)
   - Reduces perceived latency

**Deliverables:**
- ✅ `/api/feed` endpoint with pagination
- ✅ Feed cache populated on daily collector run
- ✅ Algorithm modes functional (balanced, citations, recency, novelty)
- ✅ Ranking transparency included in responses
- ✅ Sub-1s initial load, sub-300ms pagination

**Files to Touch:**
- `app/api/feed.py` - NEW (feed blueprint)
- `app/services/feed_ranker.py` - NEW (scoring algorithms)
- `app/services/collector.py` - Update to populate feed cache
- `app/__init__.py` - Register feed blueprint

---

### Phase 2: Reading Lists & Organization

**Goal:** Multi-list paper organization with drag-and-drop

**Tasks:**

1. **Reading List Data Model**
   - Collection: `users/{uid}/lists/`
   - Predefined lists (IDs: `to_read`, `reading`, `favorites`, `archive`)
   - Custom lists: User-created with unique IDs
   - List document: `{ name, emoji, color, paperCount, createdAt, updatedAt }`
   - Papers in list: Subcollection `lists/{listId}/papers/{paperId}`
   - Paper doc: `{ ...paper, addedAt, addedFrom, notes (optional) }`

2. **List Management API**
   - `GET /api/lists` - Get all user lists
   - `POST /api/lists` - Create custom list `{ name, emoji, color }`
   - `PUT /api/lists/{listId}` - Update list metadata
   - `DELETE /api/lists/{listId}` - Delete custom list (not predefined)
   - `GET /api/lists/{listId}/papers` - Get papers in list (paginated)
   - `POST /api/lists/{listId}/papers` - Add paper to list
   - `DELETE /api/lists/{listId}/papers/{paperId}` - Remove from list
   - `POST /api/lists/{listId}/move` - Move paper to different list

3. **Default Lists Creation**
   - On user creation (in `/api/users/sync`):
   - Create 4 predefined lists:
     - 📚 To Read (color: blue)
     - 📖 Currently Reading (color: orange)
     - ⭐ Favorites (color: yellow)
     - 📦 Archive (color: gray)

4. **Quick Actions on Paper Cards**
   - Add to To Read: Single click bookmark icon
   - Add to Favorites: Click star icon
   - Add to Custom List: Dropdown menu (3-dot icon)
   - Move Between Lists: Drag-and-drop (desktop), swipe gesture (mobile)
   - Batch Actions: Select multiple → Add to list

5. **List View UI**
   - Replace current "Saved" tab with "Lists" tab
   - Show all lists in sidebar/carousel
   - Each list: emoji + name + paper count
   - Click list → show papers in that list
   - Grid or list view toggle
   - Sort options: Date added, Title, Score

6. **Drag-and-Drop Implementation**
   - Desktop: HTML5 Drag-and-Drop API
   - Mobile: Touch events with visual feedback
   - Drop zones: List cards, list view headers
   - Visual cues: Drag handle icon, drop zone highlight
   - Optimistic UI: Move immediately, rollback on error

**Deliverables:**
- ✅ Multi-list backend API functional
- ✅ Default lists auto-created for users
- ✅ Drag-and-drop working (desktop + mobile)
- ✅ Quick actions on paper cards
- ✅ List view UI replaces simple "Saved" tab
- ✅ Notes field for papers (optional annotation)

**Files to Touch:**
- `app/api/lists.py` - NEW (lists management blueprint)
- `app/api/users.py` - Update sync to create default lists
- `app/api/saved.py` - DEPRECATED (migrate to lists API)
- `public/app.html` - Update Lists tab UI
- `public/js/lists.js` - NEW (drag-drop, list management)

---

### Phase 3: Source Explorer & Citation Graph

**Goal:** Web of Science-style exploration through citations, authors, venues

**Tasks:**

1. **Citation Data Enrichment**
   - Fetch citations and references from Semantic Scholar
   - Endpoint: `GET /papers/{paperId}` includes `citations[]` and `references[]`
   - Store in Firestore: `papers/{paperId}` add fields:
     - `citations`: `[{ paperId, title, year, citationCount }]` (top 20)
     - `references`: `[{ paperId, title, year, citationCount }]` (top 20)
     - `influentialCitations`: Subset of citations marked "influential" by S2
   - Batch fetch on daily collector run (rate-limited)

2. **Author Profiles**
   - Fetch author data from Semantic Scholar
   - Collection: `authors/{authorId}`
   - Fields: `{ name, hIndex, citationCount, affiliations, papers[], homepage }`
   - On-demand fetch: When user clicks author name
   - Cache for 30 days

3. **Venue Data**
   - Collection: `venues/{venueId}`
   - Fields: `{ name, type (journal/conference), impactFactor, h5Index, publisher }`
   - Fetch from OpenAlex Venues API
   - Cache indefinitely (rarely changes)

4. **Source Explorer UI**
   - Paper Detail Modal/Page:
     - Tab 1: Abstract & Metadata (current)
     - Tab 2: **Citations** (papers that cite this)
       - List of citing papers (sorted by recency or citations)
       - "Add to Feed" button for each
     - Tab 3: **References** (papers cited by this)
       - List of referenced papers
       - Visual: citation graph (D3.js or vis.js)
     - Tab 4: **Related Work**
       - Papers with similar topics (S2 recommendations API)
       - Papers by same authors
       - Papers in same venue
   - Click any paper → open its detail view (nested exploration)

5. **Author Explorer**
   - Click author name → Author profile page
   - Sections:
     - Bio: Name, affiliation, h-index, total citations
     - Top papers (sorted by citations)
     - Recent papers (last 3 years)
     - Co-authors (network visualization)
     - "Follow Author" button (future: get alerts on new papers)

6. **Venue Explorer**
   - Click venue name → Venue profile page
   - Sections:
     - Metadata: Type, publisher, impact factor
     - Recent papers in this venue
     - Top papers of all time
     - Submission deadlines (if conference)
     - "Follow Venue" button

7. **Citation Graph Visualization**
   - Library: D3.js force-directed graph or vis.js network
   - Nodes: Papers (sized by citation count, colored by year)
   - Edges: Citation links (directed)
   - Interactions:
     - Hover node → show title
     - Click node → open paper detail
     - Drag nodes to rearrange
     - Zoom and pan
   - Limit: Max 50 nodes (performance)

**Deliverables:**
- ✅ Citation data enriched for papers
- ✅ Author and venue profiles functional
- ✅ Source explorer UI with tabs (citations, references, related)
- ✅ Citation graph visualization (interactive)
- ✅ Author and venue pages
- ✅ Nested exploration (click paper → see its citations → recurse)

**Files to Touch:**
- `app/services/semantic_scholar.py` - Add citation/author/venue fetching
- `app/api/papers.py` - NEW (paper detail endpoint with citations)
- `app/api/authors.py` - NEW (author profile endpoint)
- `app/api/venues.py` - NEW (venue profile endpoint)
- `public/paper-detail.html` - NEW (or modal component)
- `public/js/citation-graph.js` - NEW (D3.js visualization)
- `docs/source-explorer.md` - NEW (usage guide)

---

### Phase 4: Feed UI & Infinite Scroll

**Goal:** Instagram-like feed interface with infinite scroll

**Tasks:**

1. **Feed Tab Redesign**
   - Replace "Digest" tab with "Feed" tab (make it the default/home)
   - Layout: Single-column, card-based, infinite scroll
   - Each card: Same paper card component but with:
     - Larger images/thumbnails (if available)
     - Ranking reason badge (e.g., "High citations" or "Related to your seeds")
     - Quick actions: ⭐ Favorite, 📚 To Read, ➕ Add to list, 🔗 Share

2. **Infinite Scroll Implementation**
   - Library: Intersection Observer API (native, no library needed)
   - Sentinel element at bottom of feed
   - When sentinel visible → fetch next page
   - Show loading spinner while fetching
   - Append new papers to DOM
   - Handle edge cases: no more papers, fetch errors

3. **Scroll Performance**
   - Virtual scrolling: Only render visible + 5 cards above/below viewport
   - Library: `react-window` or vanilla JS with IntersectionObserver
   - Remove DOM nodes for cards far above/below viewport
   - Maintain scroll position when toggling virtual scroll

4. **Algorithm Selector**
   - Dropdown at top of feed: "Ranking: Balanced ▼"
   - Options: Balanced, Citations, Recency, Novelty
   - On change: Clear feed, fetch from page 1 with new algorithm
   - Store preference in localStorage
   - Show explanation of current algorithm in dropdown tooltip

5. **Mobile Gestures**
   - Swipe right on card → Add to To Read
   - Swipe left on card → Hide/Skip (add to hidden list)
   - Pull-to-refresh → Reload feed from top
   - Tap card → Expand for full abstract
   - Long-press → Show quick actions menu

6. **Empty States**
   - No papers in feed: "No papers match your seeds. Try adding more topics."
   - All papers seen: "You've reached the end! Check back tomorrow for new papers."
   - Loading first page: Skeleton cards (shimmer effect)

**Deliverables:**
- ✅ Feed tab as default home view
- ✅ Infinite scroll functional (desktop + mobile)
- ✅ Algorithm selector with persistence
- ✅ Mobile gestures (swipe actions, pull-to-refresh)
- ✅ Virtual scrolling for performance (1000+ papers)
- ✅ Empty states and loading skeletons

**Files to Touch:**
- `public/app.html` - Update to make Feed tab default
- `public/js/feed.js` - NEW (infinite scroll, algorithm selector)
- `public/js/gestures.js` - NEW (mobile touch handlers)
- `public/css/feed.css` - NEW (or add to main CSS)

---

### Phase 5: Advanced Features (Optional)

**Goal:** Social features and personalization

**Tasks:**

1. **Follow System**
   - Follow authors: Get notified of new papers
   - Follow venues: Get notified of new issues/proceedings
   - Follow topics: Dynamic seeds (e.g., "show me papers on {topic}")
   - Collection: `users/{uid}/following/{ authors[], venues[], topics[] }`
   - API: `POST /api/follow/{type}/{id}`, `DELETE /api/unfollow/{type}/{id}`

2. **Personalized Ranking**
   - Train simple ML model on user feedback:
     - Features: paper metadata (citations, year, venue, OA, authors)
     - Labels: user actions (favorited=1, to_read=0.7, skipped=-0.5)
     - Model: Logistic regression or lightweight neural network
     - Training: Daily on BigQuery WAL data
   - Serve model: Cloud Run endpoint with TensorFlow Lite
   - Fallback: Rule-based ranking if model unavailable

3. **Collaborative Lists**
   - Share reading lists with other users
   - Public lists: Anyone can view (like Spotify playlists)
   - Collaborative lists: Multiple users can edit
   - Collection: `shared_lists/{listId}` with `owners[]` and `collaborators[]`
   - Discovery: Browse public lists, search by topic

4. **Social Sharing**
   - Share paper to: Email, Twitter, Slack, clipboard
   - Generate share link: `https://research-watcher.app/papers/{paperId}`
   - Unfurl metadata: Title, abstract, authors (Open Graph tags)
   - Track shares in WAL for trending detection

5. **Notifications (Future)**
   - Email digests: Daily or weekly
   - Push notifications: New papers from followed authors
   - In-app notifications: Papers added to collaborative lists
   - Notification preferences: User can configure frequency and types

**Deliverables:**
- ✅ Follow system for authors/venues/topics
- ✅ Personalized ranking with ML model
- ✅ Collaborative and public lists
- ✅ Social sharing with unfurl metadata
- ✅ Notification system (email or push)

**Files to Touch:**
- `app/api/follow.py` - NEW (follow/unfollow endpoints)
- `app/ml/ranker_model.py` - NEW (personalized ranking model)
- `app/api/share.py` - NEW (sharing endpoints)
- `scripts/train_ranker.py` - NEW (daily model training)
- `public/share-modal.html` - NEW (sharing UI)

## Models & Tools

**Primary Tools:**
- `pytest` - Python testing
- `gcloud` - GCP CLI
- `npm` - Frontend package management (if needed for D3.js/vis.js)
- `bash` - Automation scripts

**Frontend Libraries:**
- `D3.js` or `vis.js` - Citation graph visualization
- `Intersection Observer API` - Infinite scroll (native, no library)
- `HTML5 Drag-and-Drop API` - Drag-drop functionality
- `Tailwind CSS` - Styling (already in use)
- `HTMX` - Dynamic updates (already in use)

**Python Libraries:**
- `google-cloud-firestore` - Firestore client
- `scikit-learn` - ML model training (optional personalization)
- `tensorflow-lite` - Model serving (optional)

**GCP Services:**
- Firestore - Primary database
- Cloud Run - API hosting
- Cloud Storage - Static assets
- BigQuery - Analytics and ML training data (optional)

**Models:**
- `claude-sonnet` - Main implementation
- `claude-haiku` - Quick iterations and refactoring

## Repository

**Branch:** `feat/enhanced-discovery`

**Merge Strategy:** squash

**Working Directory:** `/home/user/research-watcher`

---

## Implementation Notes

### UX Design Principles

1. **Progressive Disclosure**: Don't overwhelm new users
   - Start with simple feed
   - Gradually introduce lists, explorer, customization
   - Onboarding tooltips on first use

2. **Mobile-First**: Design for touch, adapt for mouse
   - All actions accessible via gestures
   - Thumb-friendly tap targets (48px min)
   - Minimize text input (use pickers/dropdowns)

3. **Performance Budget**:
   - Initial load: < 1s
   - Interaction to feedback: < 100ms
   - Page navigation: < 300ms
   - Scroll frame rate: 60fps

4. **Accessibility**:
   - Keyboard navigation for all actions
   - Screen reader labels on all interactive elements
   - High contrast mode support
   - ARIA attributes for dynamic content

### Data Architecture

**Firestore Collections:**
```
users/{uid}
  ├── profile (existing)
  ├── lists/{listId}
  │   ├── metadata (name, emoji, color, count)
  │   └── papers/{paperId} (paper data + notes + addedAt)
  ├── following/
  │   ├── authors/{authorId}
  │   ├── venues/{venueId}
  │   └── topics/{topicId}
  └── preferences (algorithm, theme, notifications)

feed_cache/{uid}/papers/{paperId} (TTL: 24h)

papers/{paperId} (global, shared)
  ├── metadata (title, authors, abstract, etc.)
  ├── citations[] (top 20)
  ├── references[] (top 20)
  └── relatedPapers[] (S2 recommendations)

authors/{authorId}
  ├── profile (name, h-index, affiliations)
  └── papers/{paperId} (author's papers)

venues/{venueId}
  ├── metadata (name, type, impact factor)
  └── papers/{paperId} (venue's papers)
```

**Indexes Needed:**
- `feed_cache/{uid}/papers`: `(userId, feedScore DESC)`
- `users/{uid}/lists/{listId}/papers`: `(listId, addedAt DESC)`
- `papers`: `(citationCount DESC)`, `(year DESC)`

### Cost Estimates

**Current (Phase 3):** ~$8/month

**After Enhanced Discovery:**
- Firestore reads: ~$5/month (increased for feed pagination)
- Firestore writes: ~$3/month (lists, feed cache updates)
- Cloud Run: ~$10/month (more endpoints, citation fetching)
- Cloud Storage: ~$1/month (D3.js/vis.js assets if self-hosted)
- BigQuery: ~$5/month (optional ML training)
- External APIs:
  - Semantic Scholar: Free (own API key during alpha)
  - OpenAlex: Free

**Total:** ~$24/month (within $30 budget) ✅

### Testing Strategy

**Phase 1 (Feed Backend):**
- Unit tests: Feed ranker algorithms (4 modes)
- Integration tests: Feed API pagination
- Load tests: 100 concurrent users fetching feed
- Performance: Feed generation < 100ms

**Phase 2 (Lists):**
- Unit tests: List CRUD operations
- Integration tests: Move paper between lists
- E2E tests: Drag-and-drop on desktop
- Mobile tests: Swipe gestures on iOS/Android

**Phase 3 (Source Explorer):**
- Unit tests: Citation data normalization
- Integration tests: Author/venue fetching
- Visual tests: Citation graph rendering
- E2E tests: Nested exploration (paper → citations → recurse)

**Phase 4 (Feed UI):**
- E2E tests: Infinite scroll load all pages
- Performance tests: Virtual scrolling with 1000 papers
- Mobile tests: Swipe actions, pull-to-refresh
- A/B tests: Algorithm preference distribution

**Phase 5 (Advanced):**
- Unit tests: ML model predictions
- Integration tests: Follow system
- E2E tests: Collaborative lists
- Security tests: Share link access control

### Migration Plan

**Backward Compatibility:**
- Keep existing "Digest" and "Search" tabs during rollout
- "Feed" tab added as new default
- Users can switch between old/new UX via settings
- "Saved" papers migrated to "Favorites" list automatically

**Phased Rollout:**
1. Week 1: Feed backend live, UI hidden behind feature flag
2. Week 2: Feed UI enabled for 10% of users (A/B test)
3. Week 3: Lists enabled for feed users
4. Week 4: Source explorer enabled
5. Week 5: Full rollout if metrics positive (engagement, retention)

**Rollback Plan:**
- Feature flag: `ENABLE_ENHANCED_DISCOVERY=false`
- Revert: Hide Feed/Lists tabs, show Digest/Saved
- Data: All data persists (no deletion), just UI toggle

### Success Metrics

**Engagement:**
- Daily active users (DAU) increase > 20%
- Session duration increase > 30%
- Papers saved per session increase > 50%

**Discovery:**
- Citation exploration clicks > 10% of users
- Author/venue profile views > 5% of users
- Papers added from citations > 15% of saved papers

**Retention:**
- Week 1 retention increase > 10%
- Month 1 retention increase > 5%

**Performance:**
- Feed load time < 1s (p95)
- Infinite scroll pagination < 300ms (p95)
- Mobile scroll frame rate > 55fps (p50)

### Future Enhancements

**v2 Features:**
- PDF reader integration (read in-app)
- Annotation and highlighting
- Export to Zotero, Mendeley, EndNote
- Chrome extension for one-click saves
- Slack/Discord bots for team sharing

**v3 Features:**
- Real-time collaborative reading sessions
- Video/audio summaries (TTS)
- Multilingual paper translation
- AR citation graph (experimental)

---

## Summary

This spec transforms Research Watcher from a simple daily digest tool into a **rich discovery platform** with:
- Instagram-like feed with infinite scroll
- Multi-list organization (To Read, Reading, Favorites, Archive)
- Web of Science-style source explorer (citations, authors, venues)
- Transparent, configurable algorithms
- Mobile-first UX with gestures

**Estimated Timeline:** 8-10 weeks (5 phases)

**Estimated Cost:** $24/month (within $30 budget)

**Risk Level:** Medium (complex UX, many moving parts)

**Dependencies:** Infrastructure Upgrade Spec (Phases 4-6) should be completed first for WAL analytics