# Specifications Directory

This directory contains the specifications for Research Watcher features and architecture.

## Active Specifications

### Enhanced Discovery (v0.3) - **CURRENT FOCUS**
**File:** `specs/enhanced-discovery-spec.md`

**Status:** In progress (Phase 1 planning)

**Summary:**
Field-wide discovery platform with topic maps, research networks, and citation graphs.

**Key Features:**
- OpenAlex topic infrastructure (~500 psychology topics)
- Topic browsing UI (tree view, detail panels)
- **Research Networks** with CRUD boundaries (killer feature)
  - Flexible composition (topics + papers + authors + citations)
  - Git-style versioning with infinite branching
  - Visual pruning with exclusion lists
  - Transparent resource limits (Alpha/Beta/Pro tiers)
- Citation & author networks (graph exploration)
- Contextual search (scoped by topic/network/author)

**Architecture:**
- Three-layer data (Firestore + BigQuery + Cloud Storage)
- Background compute (60s to create blobs, user never waits)
- Pre-computed exploration blobs (3-5s download, then instant)

**Timeline:** 8-10 weeks (core phases)

---

### Infrastructure Upgrade (v1.0) - **FUTURE**
**File:** `specs/infra-upgrade-events-spec.md`

**Status:** Planned (after Enhanced Discovery)

**Summary:**
Event-sourced architecture evolution with WAL verification, fan-out processing, and agent bridge.

**Phases:**
- Phase 4: Event Ledger & Consumer Stub
- Phase 5: Fan-Out Architecture
- Phase 6: Agent Bridge API

**Timeline:** 4-6 weeks (after Enhanced Discovery complete)

---

## Specification Format

All specifications follow the Specwright format:

```yaml
---
version: "X.Y"
tier: A|B|C
title: Feature Name
owner: benthepsychologist
goal: High-level objective
labels: [tags]
orchestrator_contract: "standard"
repo:
  working_branch: "feat/branch-name"
---
```

## Reading Order for New Contributors

1. **Start here:** [Enhanced Discovery Spec](./specs/enhanced-discovery-spec.md)
   - Read "Objective" and "Architecture Overview" sections first
   - Understand the three-layer architecture
   - Review user workflows (Section 10)

2. **Understand the foundation:** [Original Spec](../docs/spec.md)
   - See how we got here (seed-based digests)
   - Understand existing data models

3. **Implementation details:** [Agent Implementation Plan](../docs/AIP.md)
   - See Phases 0-3 (already complete)

4. **Future direction:** [Infrastructure Upgrade Spec](./specs/infra-upgrade-events-spec.md)
   - See where we're going (event-sourced architecture)

## For LLM Agents

**Quick Context:**
- Current work: Enhanced Discovery (v0.3)
- Next phase: OpenAlex topic infrastructure (Phase 1)
- Killer feature: Research Networks with versioning + pruning
- Architecture: Firestore (20ms) + BigQuery (300ms) + Cloud Storage (3-5s)
- User never waits: Background compute (60s) runs async

**Key Files:**
- [Enhanced Discovery Spec](./specs/enhanced-discovery-spec.md) ← Read this first
- [Architecture Overview](../ARCHITECTURE.md) ← Quick reference
- [README](../README.md) ← Project overview

**Design Principles:**
- Simple over clever
- Fast where it matters (dashboard instant, browse fast, explore smooth)
- Cheap where possible ($7-10/mo for alpha)
- Transparent resource limits (upgrade prompts, no hidden costs)
- User never waits (background jobs)
