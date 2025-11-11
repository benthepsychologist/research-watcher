---
version: "0.3"
tier: A
title: Enhanced Discovery - Topic Map, Citation Networks & Field Exploration
owner: benthepsychologist
goal: Transform Research Watcher into a field-wide discovery platform with topic organization, citation/author networks, and scoped contextual search
labels: [feature, discovery, topics, citations, authors, search, field-mapping, modularity]
orchestrator_contract: "standard"
repo:
  working_branch: "feat/enhanced-discovery"
---

# Enhanced Discovery: Topic Map, Citation Networks & Field Exploration

**Stay up to date. Stay engaged. Stay curious.**

## Objective

Transform Research Watcher from a seed-centric digest tool into a **field-wide discovery platform** with multiple exploration modes:

1. **OpenAlex Topic Foundation**: Use OpenAlex's ~4,500 pre-built topics as the structural foundation
2. **Field-Wide Scope**: Show "ALL papers" in psychology (not just keyword-filtered results)
3. **Citation & Author Networks**: Discover papers through citation graphs and collaboration networks (ResearchRabbit-style)
4. **Contextual Search**: OpenAlex-style search scoped by context (topic, author, citation network)
5. **User-Defined Topic Groups**: Allow users to create custom collections of topics
6. **Topic Map Visualization**: Visual map of subdisciplines and their relationships
7. **Modular Design**: Keep features independent and optional

**Core Philosophy**: Build a **MAP of the entire field**, not a filtered feed. Enable exploration through **multiple discovery modes**: topic browsing, citation networks, author connections, and contextual search. "See what is happening in different parts of the discipline."

**Kill entirely**: Keyword seeds as primary mechanism (replaced by paper seeds for network discovery)

## Acceptance Criteria

### Core Features - Topics
- [ ] Fetch and cache all OpenAlex psychology topics (~500 topics)
- [ ] Topic browsing UI with hierarchy (Domain → Field → Subfield → Topic)
- [ ] "What came out this week" per topic (time-filtered paper counts)
- [ ] Topic detail view: papers within a topic (sorted by recency/citations)
- [ ] User-defined topic groups (custom collections of topics)
- [ ] Visual topic map (force-directed graph or similar)

### Core Features - Citations & Authors
- [ ] Citation network visualization (forward/backward citations)
- [ ] Author profile pages (papers, collaborators, topics)
- [ ] Co-author network graphs
- [ ] "Related papers" via citation + semantic similarity
- [ ] Paper-to-paper navigation (click paper → see network)
- [ ] Save papers as "seeds" for network exploration

### Core Features - Search
- [ ] Global search (all psychology papers)
- [ ] Topic-scoped search (within selected topic)
- [ ] Topic group-scoped search (within user's topic collection)
- [ ] Author-scoped search (within author's network)
- [ ] Citation network-scoped search (within citation graph)
- [ ] Search results with same paper card format
- [ ] Search context badge ("Searching in: Cognitive Psychology")

### Performance
- [ ] Topic tree loads < 1s (all psychology topics)
- [ ] Topic detail view loads < 500ms (papers for a topic)
- [ ] Map visualization renders < 2s (up to 500 nodes)
- [ ] Responsive on mobile (touch-friendly)

### Data
- [ ] OpenAlex topics cached in Firestore/BigQuery
- [ ] Topic hierarchy preserved (parent-child relationships)
- [ ] Paper-topic associations indexed
- [ ] Weekly/monthly paper counts per topic

### Testing
- [ ] Unit tests for OpenAlex API integration
- [ ] Integration tests for topic group CRUD
- [ ] E2E tests for topic browsing and filtering
- [ ] Performance tests for map visualization

## Context

### Background

**Current State (Phase 3):**
- Seed-based collection: Users provide keywords → API searches → ~50 papers
- Daily digest shows papers matching user's seeds only
- Users see <5% of their field (only papers matching their keywords)
- No way to discover "what's happening" in adjacent subdisciplines
- Seeds are currently "a shittier version of topics" (user quote)

**User Vision:**
> "I think I want a better mapping function for the entire field. Like the starting set is everything that has come out in the last 5 years, we map ALL of it. What came out this week. ALL of it."

> "Honestly, a MAP of various subdisciplines is what we want to build the most."

**Why This Work is Needed:**
1. **Discovery Blindness**: Current approach "forces you to subset the field or build outward from papers"
2. **Field Awareness**: Researchers need to know "what is happening in different parts of their discipline"
3. **Serendipity**: Miss 95% of field because it doesn't match narrow seed keywords
4. **Structure Over Filter**: Topics provide the structure of the field, seeds are personal relevance filters
5. **Comprehensive Coverage**: OpenAlex has ~250M papers with comprehensive topic classification

### Constraints

- Must keep existing seed-based digest functional (backward compatibility)
- Cannot break Phase 3 functionality (search, saved papers)
- Must be modular: topic features are optional, not required
- OpenAlex topics used as-is initially (no custom clustering yet)
- Budget: Stay under $30/month total
- Mobile-friendly design (touch gestures for map)

## Plan

### Phase 1: OpenAlex Topic Infrastructure

**Goal:** Fetch, cache, and expose OpenAlex topics via API

**Tasks:**

1. **OpenAlex Topics API Integration**
   - Endpoint: `https://api.openalex.org/topics`
   - Filters: `filter=domain.id:https://openalex.org/domains/2` (Social Sciences)
   - Further filter: `field.id` for Psychology specifically
   - Fetch all topics with hierarchy: `{ id, display_name, description, domain, field, subfield, works_count }`
   - Pagination: Handle `per-page=200` and `cursor` for full fetch
   - Script: `scripts/fetch_openalex_topics.py`
   - Cache in: Firestore `topics/` collection OR BigQuery `openalex_topics` table

2. **Topic Data Model**
   - **Firestore Option:**
     ```
     topics/{topicId}
       ├── display_name: "Working Memory and Cognitive Load"
       ├── description: "Research on working memory capacity..."
       ├── domain: { id, display_name }
       ├── field: { id, display_name }
       ├── subfield: { id, display_name }
       ├── works_count: 12453
       ├── works_count_this_week: 23
       ├── works_count_this_month: 178
       └── updated_at: timestamp
     ```
   - **BigQuery Option:**
     - Table: `research_watcher.openalex_topics`
     - Schema: Same as above, optimized for analytics queries
     - Update: Weekly refresh via scheduled query

3. **Topic Hierarchy API**
   - Endpoint: `GET /api/topics` (authenticated)
   - Query params: `?domain=social-sciences&field=psychology`
   - Response: Tree structure with nested topics
   - Fields: `{ id, name, description, level (domain/field/subfield/topic), children[], works_count }`
   - Cached: 24 hours (topics change slowly)

4. **Topic Detail API**
   - Endpoint: `GET /api/topics/{topicId}` (authenticated)
   - Response: Full topic metadata + recent papers
   - Include: `{ ...topic, papers_this_week[], papers_this_month[], papers_all_time[] }`
   - Papers: Fetch from OpenAlex `works` API filtered by `topics.id={topicId}`
   - Sort options: recency (default), citations, OA status
   - Pagination: 20 papers per page

5. **Paper-Topic Association**
   - When collecting papers (existing collector):
     - OpenAlex API returns `topics[]` array for each paper
     - Store in `papers/{paperId}` document: `topics: [{ id, display_name, score }]`
   - Indexing: Create Firestore index on `papers.topics.id`
   - Purpose: Enable reverse lookup (papers → topics)

6. **Weekly/Monthly Stats**
   - Script: `scripts/update_topic_stats.py` (run weekly via Cloud Scheduler)
   - For each psychology topic:
     - Query OpenAlex: `works?filter=topics.id:{topicId},publication_date:>7days`
     - Count papers this week, this month, this year
     - Update `topics/{topicId}` document
   - Cost: ~500 API calls per week (within OpenAlex polite pool)

**Deliverables:**
- ✅ OpenAlex topics fetched and cached (~500 psychology topics)
- ✅ Topic hierarchy API functional
- ✅ Topic detail API with recent papers
- ✅ Paper-topic associations stored
- ✅ Weekly/monthly stats updated automatically
- ✅ All topics browsable via API

**Files to Touch:**
- `app/services/openalex_topics.py` - NEW (topic fetching and caching)
- `app/api/topics.py` - NEW (topics API blueprint)
- `scripts/fetch_openalex_topics.py` - NEW (initial topic fetch)
- `scripts/update_topic_stats.py` - NEW (weekly stats update)
- `app/services/openalex_api.py` - Extend with topic-specific methods
- `app/__init__.py` - Register topics blueprint

---

### Phase 2: Topic Browsing UI

**Goal:** Build user interface for exploring topics and viewing papers per topic

**Tasks:**

1. **Topic Explorer Tab**
   - New tab in `app.html`: "Topics" (add after "Seeds" tab)
   - Layout: Two-panel design
     - Left panel: Topic tree (collapsible hierarchy)
     - Right panel: Topic detail (papers in selected topic)
   - Mobile: Single panel with back button navigation

2. **Topic Tree View**
   - Hierarchical tree component (use `<details>` + `<summary>` for native collapse)
   - Structure:
     ```
     Psychology (Field)
       ├─ Cognitive Psychology (Subfield)
       │   ├─ Working Memory and Cognitive Load (12,453 papers)
       │   ├─ Attention and Perception (8,921 papers)
       │   └─ ...
       ├─ Social Psychology (Subfield)
       │   ├─ Social Cognition (15,234 papers)
       │   └─ ...
       └─ ...
     ```
   - Show: Topic name + total paper count
   - Badges: "23 this week" (pill badge, blue)
   - Click topic → load papers in right panel
   - Search box: Filter topics by name (client-side)

3. **Topic Detail Panel**
   - Header: Topic name + description (expandable)
   - Metadata: Total papers, papers this week/month/year
   - Time filter dropdown: "This week" | "This month" | "This year" | "All time"
   - Sort dropdown: "Recent" | "Most cited" | "Open Access"
   - Paper cards: Same format as current digest (reuse component)
   - Pagination: Infinite scroll or "Load more" button
   - Quick actions: Save paper, add to reading list (if implemented)

4. **Topic Search**
   - Input: "Search topics..." (top of left panel)
   - Search: Client-side fuzzy search through topic names
   - Highlight: Matching topics in tree
   - Reset: Clear search shows all topics

5. **Empty States**
   - No topic selected: "Select a topic to see papers"
   - No papers this week: "No new papers this week. Try 'This month' or 'All time'"
   - Loading: Skeleton loaders for tree and papers

6. **Responsive Design**
   - Desktop (>1024px): Side-by-side panels
   - Tablet (768-1023px): Panels stack vertically
   - Mobile (<768px): Single panel with slide-in detail view

**Deliverables:**
- ✅ Topic explorer tab functional
- ✅ Topic tree with hierarchy and paper counts
- ✅ Topic detail panel with time filters
- ✅ Paper cards rendered per topic
- ✅ Search and filtering working
- ✅ Responsive design for all devices

**Files to Touch:**
- `public/app.html` - Add Topics tab
- `public/js/topics.js` - NEW (topic tree, detail panel, interactions)
- `public/css/topics.css` - NEW (styling for tree and panels)
- `public/js/components/paper-card.js` - Extract reusable component

---

### Phase 3: Research Networks (CRUD Boundaries)

**Goal:** Allow users to define, save, and track custom research network boundaries

**Architecture Overview:**

```
┌─────────────────────────────────────────────────────────┐
│ THREE-LAYER DATA ARCHITECTURE                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  FIRESTORE (20ms) ──────► Dashboard, Stats, Status     │
│    └─ Network metadata, boundaries, stats              │
│    └─ User sees: "30K papers, 156 new this week"      │
│                                                         │
│  BIGQUERY (300ms) ───────► Paginated Paper Browsing    │
│    └─ 10M papers, network associations                │
│    └─ User scrolls: 50 papers at a time               │
│                                                         │
│  CLOUD STORAGE (3-5s) ───► Graph Exploration           │
│    └─ Pre-computed 15MB blobs (papers + citations)    │
│    └─ Download once → All exploration instant          │
│                                                         │
└─────────────────────────────────────────────────────────┘

USER WORKFLOWS:

Create Network     → 30ms (Firestore) → Background compute (60s)
Browse Papers      → 300ms/page (BigQuery pagination)
Explore Graph      → 3-5s download → 0ms in-memory operations
Edit Network       → 30ms (Firestore) → Background recompute (60s)

WHY THIS ARCHITECTURE?
• 15× cheaper than pure BigQuery ($10/mo vs $150/mo)
• 3-5× faster for exploration (3-5s vs 10-18s)
• Browser caching (subsequent loads instant)
• CDN caching (global edge locations)
```

**Design Philosophy:**
Research Networks are **flexible containers** with powerful pruning and versioning:

**Flexible Composition:**
- Put whatever you want in the "bucket": topics, papers, authors, citations
- All boundary fields are **optional** - create networks however you want
- System computes the union of all papers matching any boundary criteria

**Pruning & Exclusions:**
- Programmatic exclusions: "Disinclude this lab", "Exclude this author"
- Visual pruning: Click network graph → "Cut this link", "Exclude this node"
- Exclusions stored in network boundaries and applied during paper computation

**Version Control (Git-style):**
- Every change creates a new version with parent pointer
- **Infinite branching**: Explore different network configurations from any version
- **Scrollback**: Navigate version history, see papers at each point in time
- **Compare versions**: Diff view showing boundary changes and paper count deltas
- **Restore any version**: Make historical version the current one
- Use cases: "Try 5-hop citations", "Branch: focus on cognitive load only"

**Tasks:**

1. **Research Networks Data Model**
   - Collection: `users/{uid}/research_networks/{networkId}`
   - Fields:
     ```
     {
       name: "Working Memory & Attention Research",
       emoji: "🧠",
       color: "blue",
       current_version: "v7",        // Pointer to active version
       created_at: timestamp,

       versions: {
         "v1": {
           version_id: "v1",
           parent_version: null,     // Root version
           created_at: timestamp,
           change_summary: "Initial network creation",
           snapshot: {               // Full snapshot at this version
             boundaries: {
               topics: [              // OPTIONAL - can be empty []
                 { id: "T123", display_name: "Working Memory" },
                 { id: "T456", display_name: "Cognitive Load" }
               ],
               seed_papers: [         // OPTIONAL - can be empty []
                 { id: "P789", title: "...", authors: "..." }
               ],
               key_authors: [         // OPTIONAL - can be empty []
                 { id: "A345", display_name: "Jane Smith" }
               ],
               citation_depth: 2,     // Only applies if seed_papers exist

               // NEW: Exclusion lists for pruning
               excluded_topics: [],
               excluded_papers: [],
               excluded_authors: [],
               excluded_institutions: [  // "Disinclude this lab"
                 { id: "I789", display_name: "Johns Hopkins Lab", reason: "out of scope" }
               ]
             },
             tracking: {
               notify_new_papers: true,
               notify_new_authors: false,
               digest_frequency: "weekly"  // daily, weekly, off
             },
             stats: {
               total_papers: 234,
               papers_this_week: 12,
               total_authors: 45,
               last_updated: timestamp
             }
           }
         },

         "v2": {
           version_id: "v2",
           parent_version: "v1",
           created_at: timestamp,
           change_summary: "Added Baddeley as key author",
           snapshot: { ... }
         },

         "v3-branch-5hop": {
           version_id: "v3-branch-5hop",
           parent_version: "v2",      // Branched from v2
           created_at: timestamp,
           change_summary: "Branch: Exploring 5-hop citation depth",
           snapshot: { ... }
         }
       }
     }
     ```
   - No limits: Unlimited networks, versions, topics, papers, authors per network

2. **Research Networks API (Full CRUD + Versioning + Pruning)**
   - `GET /api/networks` - Get all user's research networks
   - `POST /api/networks` - Create new network (creates v1)
   - `GET /api/networks/{networkId}` - Get network details + stats (current version)
   - `PUT /api/networks/{networkId}` - Update network (creates new version)
   - `DELETE /api/networks/{networkId}` - Delete network (all versions)
   - `GET /api/networks/{networkId}/papers` - Get papers (current version, with exclusions applied)
   - `GET /api/networks/{networkId}/authors` - Get authors (current version, with exclusions)

   **Versioning Endpoints:**
   - `GET /api/networks/{networkId}/versions` - List all versions (tree structure)
   - `GET /api/networks/{networkId}/versions/{versionId}` - Get specific version snapshot
   - `POST /api/networks/{networkId}/versions` - Create new version `{ parent_version, change_summary, snapshot }`
   - `POST /api/networks/{networkId}/branch` - Branch from version `{ from_version, branch_name }`
   - `POST /api/networks/{networkId}/restore/{versionId}` - Make version current
   - `GET /api/networks/{networkId}/diff?from={v1}&to={v2}` - Compare two versions

   **Pruning Endpoints:**
   - `POST /api/networks/{networkId}/exclude` - Add exclusion `{ type: "paper"|"author"|"institution", id, reason }`
   - `DELETE /api/networks/{networkId}/exclude/{type}/{id}` - Remove exclusion
   - `GET /api/networks/{networkId}/exclusions` - List all exclusions (current version)

   - No validation limits - unlimited networks, versions, exclusions

3. **Research Network UI**
   - Section: "My Research Networks" (top of left panel, above topic tree)
   - Display: List of networks (emoji + name + "12 new this week" badge)
   - Click network → show network dashboard
   - Create button: "+ New Research Network"

4. **Network Dashboard**
   - Header: Network name, emoji, edit/delete buttons
   - Stats cards:
     - Total papers: 234
     - New this week: 12
     - Total authors: 45
     - Topics covered: 8
   - Tabs:
     - Papers: Feed of all papers in network boundaries
     - Authors: List of all authors in network
     - Activity: Timeline of new papers/authors over time
     - Settings: Edit boundaries and tracking preferences

5. **Create/Edit Network Modal**
   - Form:
     - Name: Text input (required)
     - Emoji: Emoji picker (optional, default 🔬)
     - Color: Color picker (8 preset colors)
     - **Boundaries** (multi-step):
       - Topics: Multi-select from tree (unlimited)
       - Seed papers: Search and add papers (unlimited)
       - Key authors: Search and add authors (unlimited)
       - Citation depth: Slider (0-5 hops)
     - **Tracking**:
       - Notify new papers: Checkbox
       - Notify new authors: Checkbox
       - Digest frequency: Dropdown (daily/weekly/off)
   - Actions: Save, Cancel
   - No validation limits

6. **Add to Network (Quick Actions)**
   - From topic tree: "Add topic to network →" (submenu with networks)
   - From paper card: "Add to network" button
   - From author profile: "Track in network" button
   - Creates network if none exist (prompt for name)
   - Instant feedback: "Added to {network name}"

7. **Network Paper Feed**
   - Endpoint: `GET /api/networks/{networkId}/papers`
   - Logic (union of all boundary criteria):
     ```python
     papers = set()

     # Add papers from topics (if any)
     if network.boundaries.topics:
         for topic in network.boundaries.topics:
             papers.update(get_papers_in_topic(topic.id))

     # Add citation network papers (if any seed papers)
     if network.boundaries.seed_papers:
         for seed_paper in network.boundaries.seed_papers:
             papers.update(expand_citations(
                 seed_paper.id,
                 depth=network.boundaries.citation_depth
             ))

     # Add papers by key authors (if any)
     if network.boundaries.key_authors:
         for author in network.boundaries.key_authors:
             papers.update(get_papers_by_author(author.id))

     return deduplicate_and_rank(papers)
     ```
   - Ranking: By relevance to network, citations, recency
   - Time filter: This week, this month, this year, all time
   - Pagination: Infinite scroll
   - Export: "Export as BibTeX" button

   **Example Network Compositions:**
   - **Topic-only network**: `{ topics: [T1, T2, T3], seed_papers: [], key_authors: [] }`
     → Returns all papers in those 3 topics
   - **Citation-only network**: `{ topics: [], seed_papers: [P1, P2], key_authors: [], citation_depth: 2 }`
     → Returns papers citing P1/P2 + papers cited by P1/P2 (2 hops)
   - **Author-only network**: `{ topics: [], seed_papers: [], key_authors: [A1, A2, A3] }`
     → Returns all papers by those 3 authors
   - **Mixed network**: `{ topics: [T1], seed_papers: [P1], key_authors: [A1], citation_depth: 3 }`
     → Returns union of: topic T1 papers + P1 citation network + A1's papers

8. **Network Data Architecture: Three Storage Layers**

   **Why Three Layers?**
   - **Firestore**: Instant metadata (20ms) - network stats, status
   - **BigQuery**: Paper storage & queries (300ms) - paginated browsing
   - **Cloud Storage**: Pre-computed exploration blobs (3-5s download) - smooth graph exploration

   **Layer 1: Firestore (Instant Dashboard)**
   ```javascript
   users/{uid}/research_networks/{networkId}
   {
     name: "Working Memory Research",
     boundaries: {...},
     current_version: "v7",

     // Pre-computed stats (updated by background job)
     stats: {
       total_papers: 30234,
       papers_this_week: 156,
       top_topics: [...],
       last_updated: timestamp
     },

     // Exploration blob status
     exploration_status: "ready",  // or "computing"
     exploration_blob_url: "gs://.../net123/v7.json.gz"
   }
   ```
   - **Use case**: Dashboard, network list
   - **Latency**: 20ms (instant)
   - **Cost**: $0.02/month

   **Layer 2: BigQuery (Paper Queries)**
   ```sql
   -- papers table (10M+ papers)
   SELECT * FROM papers WHERE paper_id IN (...)

   -- network_papers table (associations)
   SELECT paper_id FROM network_papers
   WHERE network_id = 'net123' AND version_id = 'v7'
   ```
   - **Use case**: Paginated paper browsing (50 papers at a time)
   - **Latency**: 300ms per page (fast enough)
   - **Cost**: $2-5/month

   **Layer 3: Cloud Storage (Exploration Blobs)**
   ```
   gs://research-watcher-networks/
     net123/
       v7.json.gz (15MB compressed blob)
         {
           papers: [30K full objects],
           citations: [600K edges],
           authors: [...],
           clusters: [...]
         }
   ```
   - **Use case**: Graph exploration (click around, expand, prune)
   - **Latency**: 3-5s download (once), then 0ms (in-memory)
   - **Cost**: $5/month
   - **Why blob?** 3-10× faster than BigQuery, CDN cached, browser cached

9. **Background Compute Workflow (Creates Exploration Blob)**

   **When It Runs:**
   - User creates new network → Enqueue compute
   - User edits network boundaries → Enqueue compute (new version)
   - Daily refresh → Recompute active networks

   **What It Does (35-60 seconds):**
   ```python
   def compute_exploration_blob(network_id, version_id):
       # 1. Fetch paper IDs (BigQuery: 2-3s)
       paper_ids = bq.query("SELECT paper_id FROM network_papers...").result()

       # 2. Fetch full paper metadata (BigQuery: 5-8s)
       papers = bq.query("SELECT * FROM papers WHERE id IN (...)").result()

       # 3. Fetch citation edges (BigQuery: 10-20s) ← SLOWEST
       citations = bq.query("SELECT source, target FROM citations...").result()

       # 4. Extract authors & collaborations (Python: 3-5s)
       authors = build_author_graph(papers)

       # 5. Compute topic clusters (sklearn: 5-10s)
       clusters = compute_clusters(papers)

       # 6. Build graph structure (Python: 2-3s)
       graph = {'papers': papers, 'citations': citations, ...}

       # 7. Serialize + compress (Python: 3-5s)
       json_str = json.dumps(graph)  # 60MB
       compressed = gzip.compress(json_str)  # 15MB

       # 8. Upload to Cloud Storage (Network: 2-3s)
       storage.upload('gs://.../net123/v7.json.gz', compressed)

       # 9. Update Firestore status (10ms)
       db.collection('users/{uid}/research_networks').document(network_id).update({
           'exploration_status': 'ready',
           'exploration_blob_url': 'gs://.../net123/v7.json.gz',
           'stats': { total_papers: len(papers), ... }
       })
   ```

   **Time Breakdown:**
   - Citation edges query: 10-20s (35% of time)
   - Clustering: 5-10s (15%)
   - Paper metadata: 5-8s (15%)
   - Everything else: 10-15s (35%)
   - **Total: 35-60 seconds**

   **User Never Waits:**
   - Compute runs in background (Cloud Tasks)
   - User can browse papers, edit settings, do other things
   - Exploration button shows "Preparing..." until ready

10. **User Workflows (Clear Timelines)**

    **A. Creating Network:**
    ```
    User: "Create Working Memory Research"
      → Add 3 topics, 2 seed papers, 1 author
      → Click "Save"

    [Instant: 30ms]
      → Network saved to Firestore
      → Appears in sidebar immediately ✅

    [Background: 60s]
      → Compute job starts (user doesn't wait)
      → User browses topics, reads papers
      → Job completes, updates status

    [1 minute later]
      → Notification: "Working Memory Research ready to explore!"
    ```

    **B. Browsing Papers (List View):**
    ```
    User: Clicks network in sidebar

    [20ms] Dashboard loads from Firestore ✅
      → Shows stats (30,234 papers, 156 new this week)

    [300ms] First 50 papers load from BigQuery ✅
      → User scrolls

    [300ms per page] Next 50 papers load ✅
      → Infinite scroll, feels fast
    ```

    **C. Exploring Network (Graph View):**
    ```
    User: Clicks "Explore" button

    [10ms] Check Firestore status ✅
      → Status: "ready"
      → Blob URL: gs://.../v7.json.gz

    [3-5s] Download blob from Cloud Storage ✅
      → 15MB download with progress bar
      → "Downloading network data... 60%"

    [1-2s] Decompress + load into memory ✅
      → Parse JSON, build data structures

    [0ms] All exploration instant ✅
      → Click paper → See citations (instant)
      → Expand node → Show neighborhood (instant)
      → Prune edge → Update graph (instant)
      → Everything in browser memory

    [Subsequent opens: 0.1s] Browser cache ✅
      → Same version = instant from cache
    ```

    **D. Editing Network:**
    ```
    User: Adds 1 topic to network

    [30ms] Update Firestore, create v8 ✅
      → New version appears immediately
      → Can browse papers right away (BigQuery)

    [Background: 60s]
      → Recompute exploration blob for v8
      → Exploration button shows "Preparing..."
      → User continues working

    [1 minute later]
      → v8 blob ready, exploration enabled
    ```

11. **Why This Architecture?**

    **Speed Comparison:**
    | Operation | Firestore | BigQuery | Cloud Storage Blob |
    |-----------|-----------|----------|-------------------|
    | Dashboard stats | 20ms ✅ | 300ms | N/A |
    | Paginated papers | N/A | 300ms ✅ | N/A |
    | Full graph exploration | N/A | 10-18s ❌ | 3-5s ✅ |
    | In-memory exploration | N/A | N/A | 0ms ✅ |

    **Cost Comparison (100 users, 30 days):**
    - Firestore (metadata only): $0.02/month
    - BigQuery (paper queries): $2-5/month
    - Cloud Storage (blobs): $5/month
    - **Total: ~$7-10/month** ✅ Cheap

    **vs Pure BigQuery:**
    - BigQuery for everything: $150/month (10-18s per explore)
    - Hybrid architecture: $10/month (3-5s per explore)
    - **15× cheaper, 3-5× faster** ✅

12. **Network Digest Generation**
    - Endpoint: `GET /api/networks/{networkId}/digest`
    - Schedule: Based on digest_frequency setting
    - Email: Send digest with new papers/authors
    - In-app: Notification badge showing unread digests
    - Format: Same as current digest but scoped to network

13. **Resource Limits & Enforcement**
   - **Tier Detection**: Check user's tier on every network operation
   - **Enforcement Points**:
     ```python
     # Network creation
     if len(user.networks) >= tier_limits[user.tier]['max_networks']:
         return error_with_upgrade_prompt('max_networks')

     # Adding topics/papers/authors
     if len(network.boundaries.topics) >= tier_limits[user.tier]['max_topics_per_network']:
         return error_with_upgrade_prompt('max_topics')

     # Citation depth validation
     if depth > tier_limits[user.tier]['max_citation_depth']:
         return error_with_upgrade_prompt('citation_depth')

     # Background compute (check paper count after computation)
     if len(computed_papers) > tier_limits[user.tier]['max_papers_per_network']:
         return warning_with_upgrade_prompt('papers_exceeded')
     ```
   - **Resource Dashboard**: `/settings/resources`
     - Show current usage vs. limits
     - Charts: Networks used, papers cached, version history used
     - Upgrade CTA: "Unlock higher limits with Beta tier"
   - **Graceful Degradation**: When user exceeds limits, offer options:
     - Remove items to stay under limit
     - Split into multiple networks
     - Upgrade to higher tier

**Deliverables:**
- ✅ Research networks CRUD API functional
- ✅ User can create/edit/delete networks with boundaries
- ✅ Network dashboard with stats and tabs
- ✅ Network paper feed shows all papers within boundaries
- ✅ Quick actions to add entities to networks
- ✅ Network digest generation and notifications
- ✅ Version control (Git-style branching and scrollback)
- ✅ Exclusion lists (pruning support)
- ✅ Background compute + caching architecture
- ✅ Resource limits enforced per tier
- ✅ Transparent resource usage dashboard

**Files to Touch:**
- `app/api/networks.py` - NEW (research networks API blueprint)
- `app/services/network_boundaries.py` - NEW (boundary computation logic)
- `app/services/network_cache.py` - NEW (background compute + caching)
- `app/services/resource_limits.py` - NEW (tier enforcement)
- `public/js/networks.js` - NEW (network management UI)
- `public/network-modal.html` - NEW (create/edit modal)
- `public/network-dashboard.html` - NEW (dashboard view)
- `public/version-history.html` - NEW (version tree UI)
- `public/resource-dashboard.html` - NEW (usage dashboard)
- `app/__init__.py` - Register networks blueprint

---

### Phase 4: Citation & Author Networks

**Goal:** Enable paper-to-paper and author-based discovery through citation graphs and collaboration networks

**Tasks:**

1. **Citation Data Enrichment**
   - Extend paper model with citation data:
     ```
     papers/{paperId}
       ├── ... (existing fields)
       ├── cited_by_count: 123
       ├── references: [{ id, title, year, authors }] (backward citations)
       ├── cited_by: [{ id, title, year, authors }] (forward citations)
       ├── related_papers: [{ id, title, score, reason }] (S2 recommendations)
       └── citation_fetched_at: timestamp
     ```
   - Source: OpenAlex API `works/{workId}` includes:
     - `cited_by_count`
     - `referenced_works[]` (backward citations)
     - Can query `filter=cites:{workId}` for forward citations
   - Semantic Scholar API for semantic similarity:
     - Endpoint: `/paper/{paperId}/recommendations`
     - Returns related papers via embeddings + citations

2. **Citation Network API**
   - Endpoint: `GET /api/papers/{paperId}/network` (authenticated)
   - Query params: `?depth=1&max_nodes=50`
   - Response:
     ```json
     {
       center: { id, title, year, authors, cited_by_count },
       references: [{ id, title, year, authors, cited_by_count }],
       citations: [{ id, title, year, authors, cited_by_count }],
       related: [{ id, title, score, reason: "semantic/citation/co-citation" }],
       total_references: 45,
       total_citations: 123
     }
     ```
   - Pagination: Return top N by citation count, support offset
   - Caching: 7 days (citations change slowly)

3. **Author Profile API**
   - Endpoint: `GET /api/authors/{authorId}` (authenticated)
   - Source: OpenAlex `/authors/{authorId}` endpoint
   - Response:
     ```json
     {
       id: "A12345",
       display_name: "Jane Smith",
       orcid: "0000-0001-2345-6789",
       works_count: 87,
       cited_by_count: 3452,
       h_index: 23,
       topics: [{ id, display_name, count }],
       affiliations: [{ institution, years }],
       co_authors: [{ id, display_name, collaboration_count }],
       recent_papers: [{ id, title, year, cited_by_count }]
     }
     ```
   - Co-authors: From OpenAlex author data (top 20 by collaboration count)
   - Topics: Most frequent topics in author's papers

4. **Citation Network UI**
   - Location: Paper detail view (modal or dedicated page)
   - Trigger: Click paper card → "View network" button
   - Layout: Three-column view:
     - Left: References (papers this cites)
     - Center: Current paper (highlighted)
     - Right: Citations (papers citing this)
   - Paper cards: Same format as digest, show citation count badge
   - Actions per card:
     - Click → Navigate to that paper's network
     - Save → Add to reading list
     - "Expand network" → Include this paper's citations
   - Stats header: "Cited by 123 | References 45 | Related 30"
   - Pagination: "Show 20 more references/citations"

5. **Author Profile Page**
   - URL: `/authors/{authorId}` (client-side route in app.html)
   - Header:
     - Name, affiliation, ORCID
     - Stats: Papers, citations, h-index
     - Photo/avatar (if available from ORCID)
   - Sections:
     - Recent papers (last 2 years, sorted by citations)
     - Top topics (pie chart or tag cloud)
     - Co-authors network (list with collaboration counts)
     - Timeline (papers per year chart)
   - Actions:
     - "Follow author" → Get alerts for new papers (future)
     - "Search within author" → Scoped search (Phase 5)
     - Click co-author → Navigate to their profile

6. **Co-Author Network Visualization**
   - Location: Author profile page, "Network" tab
   - Library: vis.js or D3.js force-directed graph
   - Nodes: Author + co-authors (up to 50)
   - Node size: Based on collaboration count
   - Edges: Thickness = collaboration count
   - Interactions:
     - Hover → Show collaboration count
     - Click → Navigate to that author's profile
     - Filter → Show co-authors in specific topic

7. **Related Papers Widget**
   - Location: Paper detail view, sidebar
   - Title: "Related papers"
   - Sources:
     - Citation-based: Papers citing same references (co-citations)
     - Semantic: Semantic Scholar recommendations
     - Topic-based: Papers in same topics
   - Ranking: Combine all sources, deduplicate, rank by:
     - Score from S2 (if available)
     - Citation count
     - Recency
   - Display: Top 10, show reason badge ("Co-cited" | "Similar" | "Same topic")
   - Actions: Click → Navigate to paper, Save → Reading list

8. **Paper Seeds for Network Discovery**
   - Replace keyword seeds with paper seeds
   - Collection: `users/{uid}/seed_papers/{paperId}`
   - Fields:
     ```
     {
       paper: { id, title, authors, year },
       added_at: timestamp,
       reason: "manual" | "suggested" | "from_saved"
     }
     ```
   - Actions:
     - "Add as seed" button on any paper card
     - Auto-suggest: Papers from saved papers
     - No limits - unlimited seed papers via networks
   - Use case: Build networks outward from seeds

9. **Network-Based Digest**
   - Endpoint: `GET /api/digest/network` (authenticated)
   - Logic:
     - Start from user's seed papers
     - Fetch recent papers (last 7 days) that:
       - Cite any seed papers (forward citations)
       - Are cited by seed papers (if seed is recent)
       - Are semantically similar to seeds (S2 embeddings)
     - Rank by: relevance to seeds, citation count, recency
   - Return: Top 50 papers with provenance (which seed they connect to)
   - Display: New "Network Digest" section in Digest tab

**Deliverables:**
- ✅ Citation data enriched for all papers
- ✅ Citation network API functional
- ✅ Author profile API and pages
- ✅ Citation network UI with three-column view
- ✅ Co-author network visualization
- ✅ Related papers widget
- ✅ Paper seeds replace keyword seeds
- ✅ Network-based digest functional

**Files to Touch:**
- `app/services/citations.py` - NEW (citation data fetching)
- `app/services/authors.py` - NEW (author profile fetching)
- `app/api/papers.py` - Extend with `/network` endpoint
- `app/api/authors.py` - NEW (author API blueprint)
- `app/api/digest.py` - Add `/network` endpoint
- `public/paper-detail.html` - NEW (paper detail modal)
- `public/author-profile.html` - NEW (author profile page)
- `public/js/citation-network.js` - NEW (network visualization)
- `public/js/author-network.js` - NEW (co-author graph)
- `app/__init__.py` - Register authors blueprint

---

### Phase 5: Contextual Search

**Goal:** OpenAlex-style search scoped by current context (topic, author, citation network)

**Tasks:**

1. **Search Context Manager**
   - Client-side state: Current search scope
   - Scopes:
     - `global`: All psychology papers
     - `topic:{topicId}`: Papers within a topic
     - `topic-group:{groupId}`: Papers within user's topic group
     - `author:{authorId}`: Papers by author + co-authors
     - `network:{paperId}`: Papers in citation network of a paper
   - Persist scope in URL: `/search?q=working+memory&scope=topic:T123`
   - UI: Search bar shows current scope with badge

2. **Search API Extensions**
   - Extend: `GET /api/search` (existing endpoint)
   - New params:
     - `scope`: One of `global | topic | topic-group | author | network`
     - `scope_id`: ID of the scope entity (topicId, groupId, authorId, paperId)
   - Logic per scope:
     - `global`: Query OpenAlex for all psychology papers
     - `topic`: Filter OpenAlex `filter=topics.id:{topicId}`
     - `topic-group`: Fetch user's group topics, query with `filter=topics.id:{t1}|{t2}|...`
     - `author`: Query OpenAlex `filter=author.id:{authorId}` + co-authors
     - `network`: Fetch paper's citation network, search within those paper IDs
   - Response: Same paper list format, add `scope_info` field

3. **Search UI Enhancements**
   - Search bar (top of app.html, always visible):
     - Input: Query text
     - Scope badge: "Searching in: Cognitive Psychology" (click to change)
     - Results dropdown: Show results as you type (debounced 300ms)
   - Scope selector modal:
     - Options: Global, Current topic, Topic group (dropdown), Author (input), Network (current paper)
     - Quick switches: "Search everywhere" button
   - Results view:
     - Same paper card format
     - Breadcrumb: "Search results: 'working memory' in Cognitive Psychology"
     - Count: "Found 234 papers"
     - Filters: Time range, sort by (recency/citations)

4. **Context-Aware Search Bar**
   - Behavior: Search scope automatically set by current view
   - Examples:
     - User viewing topic "Cognitive Psychology" → Scope = `topic:T123`
     - User on author profile "Jane Smith" → Scope = `author:A456`
     - User in citation network of paper → Scope = `network:P789`
     - User on Digest tab → Scope = `global`
   - Override: User can manually change scope via scope selector

5. **Search History & Suggestions**
   - Store: `users/{uid}/search_history` (last 20 queries)
   - Fields: `{ query, scope, scope_id, ts, results_count }`
   - Dropdown: Show recent searches when search bar focused
   - Click recent search → Execute search with same scope
   - Suggestions: "Try searching in: [Related topic]" if results < 10

6. **Search Analytics in WAL**
   - Extend search event: `search.executed`
   - Add fields: `{ scope, scope_id, results_count, clicked_results[] }`
   - Purpose: Track which scopes are most useful
   - Agent use: Suggest popular scopes to users

**Deliverables:**
- ✅ Search context manager functional
- ✅ Search API supports all scopes
- ✅ Search UI with scope badge and selector
- ✅ Context-aware automatic scoping
- ✅ Search history and suggestions
- ✅ Search analytics events in WAL

**Files to Touch:**
- `app/api/search.py` - Extend with scope support
- `public/js/search.js` - Rewrite with context manager
- `public/search-scope-modal.html` - NEW (scope selector)
- `app/services/collector.py` - Update search event schema
- `public/components/search-bar.js` - NEW (reusable search component)

---

### Phase 6: Topic Map Visualization

**Goal:** Visual map of topics and their relationships (force-directed graph)

**Scale Reality:** Citation networks can have 30K-100K papers with 600K+ edges. Browser can't render this interactively.

**Strategy:** Multiple zoom levels + progressive loading + export for full graph

**Tasks:**

1. **Map Data API (Multi-Level)**
   - **Level 1: Overview** - `GET /api/topics/map-data?field=psychology&level=overview&max_nodes=500`
     - Shows topic clusters or top-cited papers
     - User sees forest, not trees
     - Fast to render (500 nodes, ~2K edges)

   - **Level 2: Subgraph** - `GET /api/networks/{id}/graph?level=cluster&cluster_id=X&max_nodes=2000`
     - User clicks cluster → Zoom into that area
     - Shows papers within cluster + immediate connections
     - Still manageable (2K nodes, ~10K edges)

   - **Level 3: Export** - `GET /api/networks/{id}/graph?level=export&format=gexf`
     - Full graph export for desktop tools (Gephi, Cytoscape)
     - GEXF format includes all 30K nodes + 600K edges
     - User downloads and visualizes locally

   - **Topic Map Response** (Level 1):
     ```json
     {
       nodes: [
         { id: "T123", name: "Working Memory", works_count: 12453, level: "topic", subfield_id: "S45" },
         { id: "S45", name: "Cognitive Psychology", works_count: 45000, level: "subfield" }
       ],
       edges: [
         { source: "T123", target: "S45", type: "parent_child" },
         { source: "T123", target: "T124", type: "related", weight: 0.75 }
       ]
     }
     ```
   - Node sizing: Based on `works_count` (log scale)
   - Edge types: `parent_child` (hierarchy), `related` (semantic similarity from OpenAlex)
   - Limit: Max 200 nodes for performance

2. **Map Visualization Library**
   - Library: D3.js force-directed graph OR vis.js network
   - Layout: Force-directed with collision detection
   - Node styling:
     - Size: Based on paper count (log scale)
     - Color: By subfield (categorical color scheme)
     - Label: Topic name (visible on hover or zoom)
   - Edge styling:
     - Width: Based on relationship strength
     - Opacity: 0.3 (avoid visual clutter)

3. **Map Interactions**
   - Hover node → Show tooltip (topic name, paper count, "23 this week")
   - Click node → Open topic detail panel (right side)
   - Drag node → Rearrange graph (free positioning)
   - Zoom/Pan → Mouse wheel or pinch gestures
   - Filter by subfield → Show/hide nodes (dropdown)
   - Search → Highlight nodes matching query

4. **Map Tab**
   - New tab: "Map" (add after "Topics" tab)
   - Layout: Full-width visualization (no left panel)
   - Controls (top bar):
     - Field selector: Psychology (future: other fields)
     - Subfield filter: Multi-select dropdown
     - Time filter: "Show topics with papers this week"
     - Search: "Find topic..."
     - Reset: "Reset view" (re-center and re-layout)
   - Detail panel: Slides in from right when node clicked

5. **Performance Optimization**
   - Canvas rendering: Use D3 canvas mode (not SVG) for >100 nodes
   - WebGL option: Consider vis.js WebGL renderer if needed
   - Lazy loading: Load full graph data on tab open (not on page load)
   - Throttling: Debounce zoom/pan events

6. **Mobile Map Experience**
   - Touch gestures: Pinch to zoom, two-finger pan
   - Simplified view: Show only subfields by default (drill down to topics)
   - Tap node → Open topic detail in full-screen modal
   - Performance: Limit to 100 nodes on mobile

**Deliverables:**
- ✅ Topic map visualization functional
- ✅ Interactive node selection and detail view
- ✅ Filtering and search working
- ✅ Smooth performance (60fps) up to 200 nodes
- ✅ Mobile-friendly with touch gestures
- ✅ Map tab integrated into app

**Files to Touch:**
- `public/js/topic-map.js` - NEW (D3.js/vis.js visualization)
- `public/css/topic-map.css` - NEW (map styling)
- `public/app.html` - Add Map tab
- `app/api/topics.py` - Add `/map-data` endpoint

---

### Phase 7: Reading Lists Integration (Optional)

**Goal:** Integrate reading lists from original spec (modular, optional)

**Note:** This phase is independent and can be implemented in parallel or later.

**Reference:** See original Enhanced Discovery spec v1.0 Phase 2 for full details.

**Summary:**
- Multi-list paper organization (To Read, Currently Reading, Favorites, Archive)
- Drag-and-drop between lists
- Quick actions on paper cards
- Migrate existing "Saved" papers to "Favorites" list

**Deliverables:**
- ✅ Reading lists backend and UI functional
- ✅ Drag-and-drop working
- ✅ Integration with topic-based discovery

---

### Phase 8: Venue & Institution Profiles (Optional)

**Goal:** Explore papers by venue (journals/conferences) and institution

**Note:** This phase is independent and can be implemented later. Most functionality already covered in Phase 4 (Authors).

**Tasks:**
1. **Venue Profile Page**
   - Source: OpenAlex `/venues/{venueId}` or `/sources/{sourceId}`
   - Display: Journal/conference name, impact metrics, recent papers
   - Search: "Search within venue"

2. **Institution Profile Page**
   - Source: OpenAlex `/institutions/{institutionId}`
   - Display: Affiliated authors, research areas, output metrics
   - Search: "Search within institution"

**Deliverables:**
- ✅ Venue profile pages
- ✅ Institution profile pages
- ✅ Scoped search for venues/institutions

---

## Models & Tools

**Primary Tools:**
- `pytest` - Python testing
- `gcloud` - GCP CLI
- `bash` - Automation scripts

**Frontend Libraries:**
- `D3.js` or `vis.js` - Topic map visualization (force-directed graph)
- `HTMX` - Dynamic updates (already in use)
- `Tailwind CSS` - Styling (already in use)

**Python Libraries:**
- `google-cloud-firestore` - Firestore client
- `requests` - OpenAlex API calls

**GCP Services:**
- Firestore - Primary database (topics, topic groups, papers)
- Cloud Run - API hosting
- Cloud Storage - Static assets
- BigQuery - Optional (topic analytics, trending queries)
- Cloud Scheduler - Weekly topic stats updates

**External APIs:**
- OpenAlex - Topic taxonomy, paper metadata, works API

**Models:**
- `claude-sonnet` - Main implementation
- `claude-haiku` - Quick iterations

## Repository

**Branch:** `feat/enhanced-discovery`

**Merge Strategy:** squash

**Working Directory:** `/home/user/research-watcher`

---

## Implementation Notes

### Design Principles

1. **Field-Wide Scope**: Show the entire research landscape, not just filtered subsets
2. **Modular Features**: Each phase is independent and optional
3. **Topics First, Networks Later**: Topics provide structure, networks add tracking/personalization
4. **Comprehensive Coverage**: OpenAlex provides ~250M papers with topic classification
5. **Progressive Enhancement**: Start simple (topic tree), add richness (map, networks, citations)

### Topics vs. Research Networks

**Topics** (Phases 1-2):
- **What**: OpenAlex pre-built taxonomy (~500 psychology topics)
- **Purpose**: Field structure and discovery
- **Use cases**:
  - Browse entire field hierarchy
  - See "what came out this week" per topic
  - Search within a topic
  - Understand subdisciplines and relationships

**Research Networks** (Phase 3):
- **What**: User-defined CRUD boundaries with flexible composition
- **Purpose**: Tracking and personalized digests
- **Use cases**:
  - Track specific topic areas over time
  - Follow citations from seminal papers
  - Monitor specific authors and collaborators
  - Get weekly digests of activity within boundaries
  - Mix and match: topics + papers + authors + citations

**Relationship**:
- **Semi-separate**: You can use topics without networks, or networks without topics
- **Composable**: A network can contain topics (optional), papers (optional), authors (optional)
- **Flexible**: A network could be just 1 topic, or 10 topics, or 0 topics + 5 papers + 3 authors
- **Search scopes**: Can search within a topic (no network needed) OR within a network (which may include topics)

**Examples**:
1. **Just browsing**: User explores topic tree, clicks "Cognitive Load", reads papers → No network needed
2. **Simple tracking**: User creates network with 3 topics → Gets weekly digest of those topics
3. **Complex tracking**: User creates network: "Baddeley's Legacy" = 2 topics + 1 seminal paper (3-hop citations) + key author
4. **Citation-only**: User creates network with 0 topics, 5 seminal papers, 2-hop citation depth → Tracks citation network evolution

### Data Architecture

**Firestore Collections:**
```
topics/{topicId}
  ├── display_name: "Working Memory and Cognitive Load"
  ├── description: "Research on working memory..."
  ├── domain: { id, display_name }
  ├── field: { id, display_name }
  ├── subfield: { id, display_name }
  ├── works_count: 12453
  ├── works_count_this_week: 23
  ├── works_count_this_month: 178
  └── updated_at: timestamp

users/{uid}
  ├── profile (existing)
  ├── research_networks/{networkId}
  │   ├── name: "Working Memory Research"
  │   ├── emoji: "🧠"
  │   ├── color: "blue"
  │   ├── boundaries: {
  │   │     topics: [{ id, display_name }],      // OPTIONAL
  │   │     seed_papers: [{ id, title, ... }],   // OPTIONAL
  │   │     key_authors: [{ id, display_name }], // OPTIONAL
  │   │     citation_depth: 2                    // Only if seed_papers exist
  │   │   }
  │   ├── tracking: { notify_new_papers, digest_frequency }
  │   ├── stats: { total_papers, papers_this_week, ... }
  │   └── created_at: timestamp
  └── preferences (existing)

papers/{paperId} (existing, extended)
  ├── metadata (title, authors, abstract, etc.)
  └── topics: [{ id: "T123", display_name: "Working Memory", score: 0.85 }]
```

**Indexes Needed:**
- `topics`: `(field.id, works_count DESC)`, `(subfield.id, display_name ASC)`
- `papers`: `(topics.id, publication_date DESC)`, `(topics.id, cited_by_count DESC)`
- `users/{uid}/topic_groups`: `(created_at DESC)`

### Cost Estimates & Resource Limits

**Resource Realities:**

Research Networks can scale to **30K-100K papers per network** with **600K+ citation edges**. This is powerful but resource-intensive.

**Strategy: Transparent resource limits with pay-to-upgrade**

#### Alpha Tier (Free, Limited Resources)

**Limits per user:**
- 3 research networks max
- 10K papers per network max
- 5 topics per network max
- 2-hop citation depth max
- 10 network versions (history)
- Weekly digest frequency only

**Cost to provide:**
- Firestore: $2/month per user (cache papers)
- BigQuery: $0.50/month per user (queries)
- Cloud Run: $1/month per user (compute)
- Cloud Tasks: $0.20/month per user (background jobs)
- **Total: ~$3.70/user/month**
- For 20 alpha users: **~$75/month**

#### Beta Tier (Paid, Higher Limits)

**Limits per user:**
- Unlimited research networks
- 50K papers per network max
- Unlimited topics, papers, authors per network
- 5-hop citation depth max
- Unlimited version history
- Daily digest frequency

**Pricing:** $10/user/month

**Cost to provide:**
- Firestore: $6/month per user
- BigQuery: $2/month per user
- Cloud Run: $3/month per user
- Cloud Tasks: $0.50/month per user
- **Total: ~$11.50/user/month**
- Margin: Break-even to slight loss (acceptable for beta)

#### Pro Tier (Future, No Limits)

**Limits per user:**
- Unlimited everything
- Export full graphs (GEXF format for Gephi)
- API access for automation
- Priority compute (faster background jobs)

**Pricing:** $25-50/user/month

**Cost to provide:**
- Scales with usage (~$20-30/user/month)
- Profitable at scale

#### Resource Transparency

**When user hits limit:**
```
⚠️ Network size limit reached (10,000 papers)

Your "Working Memory Research" network has reached the Alpha tier limit.

Current: 10,234 papers
Limit: 10,000 papers (Alpha tier)

Options:
• Remove topics/papers to stay under limit
• Upgrade to Beta tier ($10/month) → 50K papers per network
• Split into multiple networks (stay on Alpha)

[View resource usage] [Upgrade to Beta]
```

**Resource usage dashboard:**
```
Your Resource Usage (Alpha Tier)

Networks: 3/3 (at limit)
Papers cached: 27K/30K (90%)
Version history: 8/10 per network
Citation depth: 2 hops (max)

[Upgrade to Beta] [View pricing]
```

#### Updated Cost Estimates

**Alpha phase (20 users, free tier):**
- Infrastructure: ~$75/month
- Acceptable for bootstrapping

**Beta phase (100 users, 30% paid):**
- 70 free users × $3.70 = $260/month cost
- 30 paid users × $10 = $300/month revenue
- Net: +$40/month (sustainable) ✅

**Growth phase (1,000 users, 50% paid):**
- 500 free users × $3.70 = $1,850/month cost
- 500 paid users × $10 = $5,000/month revenue
- Net: +$3,150/month (profitable) ✅

### Testing Strategy

**Phase 1 (Infrastructure):**
- Unit tests: OpenAlex API integration, topic caching
- Integration tests: Topic hierarchy API, topic detail API
- Data validation: Topic count, hierarchy integrity

**Phase 2 (Browsing UI):**
- E2E tests: Topic tree navigation, topic detail panel
- Unit tests: Topic search, filtering
- Mobile tests: Responsive design, touch interactions

**Phase 3 (Topic Groups):**
- Unit tests: Topic group CRUD operations
- Integration tests: Group paper feed
- E2E tests: Create group, add topics, view papers

**Phase 4 (Map Visualization):**
- Visual tests: Map rendering, layout algorithm
- Performance tests: 200 nodes at 60fps
- Interaction tests: Click, drag, zoom, search
- Mobile tests: Touch gestures, simplified view

**Phase 5 (Seeds Layer):**
- Unit tests: Seed-topic matching algorithm
- Integration tests: Highlighted topics, filtered views
- E2E tests: Seed-based feed with topics

### Migration Plan

**Backward Compatibility:**
- Keep all existing Phase 3 functionality (Digest, Search, Seeds, Saved)
- Topics feature is additive (new tab, no changes to existing tabs)
- Seeds continue to work as before (Phase 5 enhances, doesn't replace)

**Phased Rollout:**
1. Week 1-2: Phase 1 infrastructure (topics cached, API functional)
2. Week 3-4: Phase 2 UI (topic tree, detail panel)
3. Week 5: Phase 3 topic groups (user testing)
4. Week 6-7: Phase 4 map visualization
5. Week 8+: Phase 5 seeds layer (optional), Phases 6-7 (optional)

**Feature Flag:**
- `ENABLE_TOPIC_DISCOVERY=true` (default: true after launch)
- Rollback: Hide Topics and Map tabs, revert to Phase 3 UI

### Success Metrics

**Engagement:**
- % users who open Topics tab > 60%
- % users who create topic groups > 30%
- % users who use Map view > 20%
- Session duration increase > 40% (exploring vs. just reading digest)

**Discovery:**
- Papers viewed per session increase > 100% (vs. seed-only digest)
- Topics explored per session > 10
- Papers saved from topics > 50% of all saves

**Retention:**
- Week 1 retention increase > 15% (vs. seed-only baseline)
- Month 1 retention increase > 10%

**Validation:**
- User feedback: "I can see my entire field now, not just my narrow interests"
- Feature adoption: Topic groups created by >30% of active users

### Future Enhancements

**v2 Features:**
- Custom topic refinement: Users can cluster papers within a topic
- Semantic clustering: Use S2 embeddings to sub-cluster OpenAlex topics
- Topic following: Get alerts when new papers appear in a topic
- Trending topics: Show topics with unusual activity this week

**v3 Features:**
- Cross-field exploration: Browse topics across multiple fields
- Collaborative topic groups: Share topic groups with colleagues
- Topic recommendations: "Based on your groups, you might like..."
- Citation-based topic relationships: Show topics connected by citations

**Integration with Other Specs:**
- Phase 6-7 (Reading Lists, Source Explorer) from original Enhanced Discovery spec
- Infrastructure Upgrade Spec (Phases 4-6): WAL events for topic interactions
- Agent-based topic summarization: AI summaries of trending topics

---

## Summary

This spec transforms Research Watcher from a **keyword-seed tool** into a **field-wide discovery and tracking platform**:

**Core Value Proposition:**
1. **Discovery FIRST**: Browse the entire field (topics + papers), understand the landscape
2. **Network Tracking**: Define custom research network boundaries, track activity within them
3. **Comprehensive Lit Review LATER**: Full ResearchRabbit-style exploration (future phase)

**Core Changes from v2.0:**
- ❌ Keyword seeds as primary → ✅ **Research Networks** with CRUD boundaries
- ✅ Topic-based field map (kept from v2.0) → ✅ Enhanced with network tracking
- ✅ Citation & author networks → ✅ **NEW: Network boundary exploration**
- ✅ Contextual scoped search → ✅ **NEW: Search within network boundaries**
- ❌ ALL monetization gates → ✅ **Unlimited everything** (networks, topics, papers, authors)

**Discovery Modes (Priority Order):**
1. **Topic Browsing** (Phase 1-2): Explore field structure via OpenAlex ~250M papers
2. **Research Networks** (Phase 3): CRUD boundaries → track specific areas ← **CORE VALUE**
3. **Citation Networks** (Phase 4): Paper-to-paper connections within boundaries
4. **Contextual Search** (Phase 5): Search scoped by network/topic/author ← **CORE VALUE**
5. **Topic Map** (Phase 6): Visual map of subdisciplines (optional)
6. **Reading Lists** (Phase 7, optional): Multi-list organization
7. **Venues/Institutions** (Phase 8, optional): Explore by journal or institution

**Future: Comprehensive Lit Review (Post-v1)**
- Full citation graph exploration (ResearchRabbit-style)
- AI-powered literature synthesis
- Comprehensive reference management
- Export integrations (Zotero, Mendeley, etc.)

**What's Killed:**
- ❌ Keyword seeds as primary mechanism
- ❌ Seeds as topic highlighting layer

**Resource Model:**
- ✅ **Alpha tier (free):** Limited resources (3 networks, 10K papers/network, 2-hop citations)
- ✅ **Beta tier ($10/mo):** Higher limits (unlimited networks, 50K papers/network, 5-hop citations)
- ✅ **Pro tier (future):** Unlimited everything + exports + API access
- ✅ **Transparent limits:** Users see resource usage dashboard and can upgrade when needed
- ✅ **Sustainable economics:** Free tier costs ~$3.70/user/month, paid tier profitable

**What's Preserved:**
- ✅ Backward compatibility (existing features remain functional)
- ✅ Modularity (each phase is independent)
- ✅ Mobile-first design
- ✅ Cost-conscious architecture with transparent resource limits

**Estimated Timeline:** 8-10 weeks (core phases)
- Weeks 1-2: Phase 1 (Topic infrastructure)
- Weeks 3-4: Phase 2 (Topic UI)
- Week 5: **Phase 3 (Research Networks with boundaries + versioning + pruning)** ← **KILLER FEATURE**
- Weeks 6-7: Phase 4 (Citations & authors within networks)
- Week 8: Phase 5 (Contextual search within networks)
- Weeks 9-10: Phase 6 (Map visualization, optional)
- Weeks 11+: Phases 7-8 (optional)

**Economics:**
- Alpha phase (20 users, free): ~$75/month cost
- Beta phase (100 users, 30% paid): +$40/month net (sustainable)
- Growth phase (1,000 users, 50% paid): +$3,150/month net (profitable)
- See detailed cost breakdown in "Cost Estimates & Resource Limits" section

**Risk Level:** Medium-High
- New: Network boundary computation, real-time tracking, unlimited usage at scale
- Complex: Multi-scope search, citation graph expansion, notification system
- Mitigation: Phased rollout, feature flags, caching strategies, extensive testing

**Dependencies:** None (can start immediately after Phase 3)

**Why OpenAlex?**
- ~250M papers with DOIs - basically everything that exists
- Free API with generous rate limits (polite pool)
- Comprehensive metadata (citations, authors, topics, affiliations)
- Active maintenance and data updates
- Enables "discovery FIRST" model without hitting paywalls
