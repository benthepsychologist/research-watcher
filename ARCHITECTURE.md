# Research Watcher Architecture

**Last Updated:** 2025-01-15 (v0.3 - Enhanced Discovery)

## System Overview

Research Watcher is a field-wide discovery platform that helps researchers explore their discipline through topic maps, citation networks, and custom research boundaries.

**Motto:** Stay up to date. Stay engaged. Stay curious.

---

## Three-Layer Data Architecture

### Why Three Layers?

Different use cases require different performance characteristics:
- **Dashboard/metadata**: Needs to be instant (20ms)
- **Browsing papers**: Needs to be fast enough (300ms)
- **Graph exploration**: Needs to be smooth once loaded (0ms after initial download)

### Layer 1: Firestore (Instant - 20ms)

**Purpose:** Network metadata, user data, instant dashboard stats

**What's Stored:**
```javascript
users/{uid}/research_networks/{networkId}
{
  name: "Working Memory Research",
  boundaries: {
    topics: [...],
    seed_papers: [...],
    key_authors: [...],
    excluded_topics: [...],
    excluded_papers: [...],
    excluded_authors: [...]
  },
  current_version: "v7",
  stats: {
    total_papers: 30234,
    papers_this_week: 156,
    top_topics: [...],
    last_updated: timestamp
  },
  exploration_status: "ready",
  exploration_blob_url: "gs://.../net123/v7.json.gz"
}
```

**Use Cases:**
- Dashboard page loads
- Network list in sidebar
- Quick stats display
- Status checks

**Cost:** ~$0.02/month (100 networks)

### Layer 2: BigQuery (Fast Enough - 300ms)

**Purpose:** Paper storage, paginated queries, analytics

**What's Stored:**
```sql
-- papers table (10M+ papers)
CREATE TABLE papers (
  paper_id STRING,
  title STRING,
  authors ARRAY<STRUCT<id STRING, name STRING>>,
  abstract STRING,
  publication_date DATE,
  cited_by_count INT64,
  topics ARRAY<STRUCT<id STRING, name STRING>>,
  references ARRAY<STRING>
)

-- network_papers table (associations)
CREATE TABLE network_papers (
  network_id STRING,
  version_id STRING,
  paper_id STRING,
  added_at TIMESTAMP
)

-- citations table (edges)
CREATE TABLE citations (
  source_paper_id STRING,
  target_paper_id STRING,
  context STRING
)
```

**Use Cases:**
- Paginated paper browsing (50 papers at a time)
- Search queries
- Analytics queries
- Background compute jobs

**Cost:** ~$2-5/month (storage + queries)

### Layer 3: Cloud Storage (Download Once - 3-5s)

**Purpose:** Pre-computed exploration blobs for smooth graph interaction

**What's Stored:**
```
gs://research-watcher-networks/
  net123/
    v7.json.gz (15MB compressed)
    {
      metadata: {
        network_id: "net123",
        version_id: "v7",
        total_papers: 30234,
        total_citations: 156789
      },
      papers: [
        { id, title, authors, year, citations, topics, ... },
        // 30K full paper objects
      ],
      citations: [
        { source: "P1", target: "P2", type: "cites" },
        // 600K citation edges
      ],
      authors: [
        { id, name, papers, collaborators },
        // All authors in network
      ],
      clusters: [
        { id, papers, centroid },
        // Pre-computed topic clusters
      ]
    }
```

**Use Cases:**
- Graph exploration (click, expand, prune)
- Citation network visualization
- Author collaboration graphs
- Full network analysis

**Why blobs instead of BigQuery?**
- 3-10× faster (3-5s vs 10-18s)
- 15× cheaper ($5/mo vs $150/mo)
- CDN cached (global edge locations)
- Browser cached (instant subsequent loads)
- Enables in-memory operations (0ms clicks)

**Cost:** ~$5/month (storage + bandwidth)

---

## Background Compute Workflow

### When It Runs
1. User creates new network → Enqueue compute
2. User edits network boundaries → Enqueue compute (new version)
3. Daily refresh → Recompute active networks (Cloud Scheduler)

### What It Does (35-60 seconds)

```python
def compute_exploration_blob(network_id, version_id):
    """
    Creates pre-computed blob for fast graph exploration.
    Runs in background - user never waits.
    """

    # Step 1: Fetch paper IDs (BigQuery: 2-3s)
    paper_ids = bq.query("""
        SELECT paper_id FROM network_papers
        WHERE network_id = @network_id AND version_id = @version_id
    """).result()

    # Step 2: Fetch full paper metadata (BigQuery: 5-8s)
    papers = bq.query("""
        SELECT * FROM papers WHERE paper_id IN UNNEST(@paper_ids)
    """).result()

    # Step 3: Fetch citation edges (BigQuery: 10-20s) ← SLOWEST
    citations = bq.query("""
        SELECT source_paper_id, target_paper_id
        FROM citations
        WHERE source_paper_id IN UNNEST(@paper_ids)
          AND target_paper_id IN UNNEST(@paper_ids)
    """).result()

    # Step 4: Extract authors & collaborations (Python: 3-5s)
    authors = build_author_graph(papers)

    # Step 5: Compute topic clusters (sklearn: 5-10s)
    clusters = compute_clusters(papers)

    # Step 6: Build graph structure (Python: 2-3s)
    graph = {
        'metadata': {...},
        'papers': papers,
        'citations': citations,
        'authors': authors,
        'clusters': clusters
    }

    # Step 7: Serialize + compress (Python: 3-5s)
    json_str = json.dumps(graph)  # 60MB
    compressed = gzip.compress(json_str)  # 15MB

    # Step 8: Upload to Cloud Storage (Network: 2-3s)
    storage.upload('gs://.../net123/v7.json.gz', compressed)

    # Step 9: Update Firestore status (10ms)
    db.collection('users/{uid}/research_networks').document(network_id).update({
        'exploration_status': 'ready',
        'exploration_blob_url': 'gs://.../net123/v7.json.gz',
        'stats': {...}
    })
```

**Time Breakdown:**
- Citation edges query: 10-20s (35%)
- Clustering: 5-10s (15%)
- Paper metadata: 5-8s (15%)
- Everything else: 10-15s (35%)
- **Total: 35-60 seconds**

**User Never Waits:**
- Runs in background via Cloud Tasks
- User can browse papers, edit settings, do other things
- Notification when ready: "Network ready to explore!"

---

## User Workflows

### A. Creating Network

```
[Instant: 30ms]
User: "Create Working Memory Research"
  → Add 3 topics, 2 seed papers, 1 author
  → Click "Save"
  → Network saved to Firestore
  → Appears in sidebar immediately ✅

[Background: 60s]
  → Compute job starts (user doesn't wait)
  → User browses topics, reads papers
  → Job completes, updates status

[1 minute later]
  → Notification: "Working Memory Research ready to explore!"
```

### B. Browsing Papers (List View)

```
[20ms] Dashboard loads from Firestore ✅
  → Shows stats (30,234 papers, 156 new this week)

[300ms] First 50 papers load from BigQuery ✅
  → User scrolls

[300ms per page] Next 50 papers load ✅
  → Infinite scroll, feels fast
```

### C. Exploring Network (Graph View)

```
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

### D. Editing Network

```
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

---

## Key Features

### Enhanced Discovery - Topics (v0.3 - Complete)

**Topic Infrastructure:**
- 1,487 Social Sciences topics cached in Firestore (144 Psychology topics)
- Hierarchical structure: Domain → Field → Subfield → Topic
- Topics API with 6 endpoints for browsing and searching

**Topics Browser:**
- Interactive tab in frontend for field-wide discovery
- Search topics by keyword with real-time results
- Filter by field (Psychology, Economics, Arts, etc.)
- Topic detail panels with hierarchy, stats, and keywords
- Deployed at: https://research-watcher.web.app

**Purpose:**
- Discover "ALL of it" - see what's happening across the field
- Explore subdisciplines without keyword filtering
- Foundation for Research Networks (Phase 3)

### Research Networks (Killer Feature - Phase 3)

**Flexible Composition:**
- Put whatever you want in the "bucket"
- Topics + papers + authors + citations
- All boundary fields optional
- System computes union of all matching papers

**Example Networks:**
- **Topic-only**: Track 3 topics
- **Citation-only**: Track 5 papers with 2-hop citations
- **Author-only**: Track 3 authors
- **Mixed**: 2 topics + 1 paper (3-hop) + 1 author

**Pruning & Exclusions:**
- Programmatic: "Disinclude this lab"
- Visual: Click graph → "Cut this link"
- Exclusions stored in boundaries

**Version Control (Git-style):**
- Every change creates new version
- Infinite branching
- Scrollback through history
- Compare versions (diff view)
- Restore any version

### Resource Limits (Transparent Tiers)

**Alpha (Free):**
- 3 networks max
- 10K papers per network
- 2-hop citation depth
- Weekly digests

**Beta ($10/mo):**
- Unlimited networks
- 50K papers per network
- 5-hop citation depth
- Daily digests

**Pro (Future):**
- Unlimited everything
- Export full graphs
- API access

---

## Technology Choices

### Why HTMX?
- Server-rendered (minimal JS)
- Easy polling for background jobs
- Instant CRUD operations
- Works great with Flask

### Why Flask?
- Simple, lightweight
- Easy to understand
- Fast development
- Great for APIs

### Why GCP?
- Firestore: Fast, scalable NoSQL
- BigQuery: Cheap, fast analytics
- Cloud Storage: CDN-backed blobs
- Cloud Tasks: Reliable background jobs
- All integrated ecosystem

### Why OpenAlex?
- Free API (250M papers)
- Topic taxonomy (~4,500 topics)
- Comprehensive metadata
- No rate limits (polite pool)

---

## Cost Analysis

### Current (Alpha - 20 users)
- Firestore: $0.02/mo
- BigQuery: $2/mo
- Cloud Storage: $5/mo
- Cloud Tasks: $0.50/mo
- **Total: ~$7.50/month**

### Beta (100 users, 30% paid)
- 70 free users × $3.70 = $260/mo cost
- 30 paid users × $10 = $300/mo revenue
- **Net: +$40/month** (sustainable)

### Growth (1,000 users, 50% paid)
- 500 free users × $3.70 = $1,850/mo cost
- 500 paid users × $10 = $5,000/mo revenue
- **Net: +$3,150/month** (profitable)

---

## Future Optimizations

### Phase 1 (Alpha)
- Accept 60s compute time
- Simple architecture
- Focus on getting it working

### Phase 2 (Beta)
- Citation index (reduce to 20-30s)
- Incremental updates (8-12s for edits)
- Better clustering algorithms

### Phase 3 (Scale)
- Distributed compute (multiple workers)
- Caching strategies
- Query optimization

---

## For LLM Agents

**Key Points:**
- Three layers: Firestore (instant), BigQuery (fast), Cloud Storage (download once)
- Background compute: 60s to create blob, user never waits
- User workflows: Create (instant), Browse (300ms), Explore (3-5s)
- Research Networks: Flexible composition, versioning, pruning
- Resource limits: Transparent tiers with upgrade prompts

**Current Focus:**
- Phase 1: OpenAlex topic infrastructure
- Phase 2: Topic browsing UI
- Phase 3: Research Networks (CRUD + versioning)

**Architecture Philosophy:**
- Simple over clever
- Fast where it matters
- Cheap where possible
- User never waits for background jobs
