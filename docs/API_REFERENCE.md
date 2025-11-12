# Research Watcher - API Reference

Complete reference for the Research Watcher REST API.

**Last Updated**: 2025-11-12
**API Version**: v0.3
**Base URL**: `https://rw-api-491582996945.us-central1.run.app`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Error Handling](#error-handling)
3. [Topics API](#topics-api)
4. [Users API](#users-api)
5. [Seeds API](#seeds-api)
6. [Digest API](#digest-api)
7. [Search API](#search-api)
8. [Saved Papers API](#saved-papers-api)
9. [Feedback API](#feedback-api)
10. [Collector API](#collector-api)

---

## Authentication

All API endpoints (except health check) require Firebase JWT authentication.

### How Authentication Works

1. User signs in via Firebase Authentication (Google OAuth)
2. Frontend obtains Firebase ID token
3. Token is sent in `Authorization` header with each request
4. Backend validates token and extracts user ID

### Headers

```http
Authorization: Bearer <FIREBASE_ID_TOKEN>
Content-Type: application/json
```

### Getting a Token

**Via Frontend**:
```javascript
const user = firebase.auth().currentUser;
const token = await user.getIdToken();
```

**Example Request**:
```bash
curl -X GET https://rw-api-491582996945.us-central1.run.app/api/topics \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6I..."
```

### Authentication Errors

**401 Unauthorized** - Missing or invalid token:
```json
{
  "error": "unauthorized",
  "message": "Missing Authorization header"
}
```

---

## Error Handling

### Standard Error Response

All errors return JSON with the following structure:

```json
{
  "error": "error_code_or_message",
  "message": "Human-readable error description (optional)"
}
```

### HTTP Status Codes

- `200 OK` - Request succeeded
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required or failed
- `403 Forbidden` - Authenticated but not authorized
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Topics API

Browse and search OpenAlex topics for research discovery.

**Part of**: Enhanced Discovery Phase 1
**Base Path**: `/api/topics`
**Authentication**: Required

### Overview

The Topics API provides access to 1,487 cached OpenAlex topics across 6 fields (primarily Social Sciences). Topics are organized hierarchically and can be filtered, searched, and browsed.

### Endpoints

#### 1. Get All Topics

Get all topics, optionally filtered by field.

**Endpoint**: `GET /api/topics`

**Query Parameters**:
- `field` (string, optional) - Field name to filter by (e.g., "Psychology")
- `format` (string, optional) - Response format: "flat" (default) or "hierarchy"

**Response Format (flat)**:
```json
{
  "format": "flat",
  "count": 1487,
  "topics": [
    {
      "id": "T10312",
      "display_name": "Cognitive Psychology",
      "description": "This topic covers research on...",
      "keywords": ["cognition", "memory", "attention"],
      "works_count": 125000,
      "cited_by_count": 3500000,
      "field": {
        "id": "F1",
        "display_name": "Social Sciences"
      },
      "domain": {
        "id": "D1",
        "display_name": "Social Sciences"
      },
      "subfield": {
        "id": "SF12",
        "display_name": "Psychology"
      }
    },
    // ... more topics
  ]
}
```

**Response Format (hierarchy)**:
```json
{
  "format": "hierarchy",
  "count": 1487,
  "hierarchy": {
    "Social Sciences": [
      {
        "id": "T10312",
        "display_name": "Cognitive Psychology",
        "works_count": 125000,
        "children": [
          // ... nested topics
        ]
      }
    ]
  }
}
```

**Example Requests**:

```bash
# Get all topics (flat)
curl -X GET "https://rw-api-491582996945.us-central1.run.app/api/topics" \
  -H "Authorization: Bearer <TOKEN>"

# Get Psychology topics only
curl -X GET "https://rw-api-491582996945.us-central1.run.app/api/topics?field=Psychology" \
  -H "Authorization: Bearer <TOKEN>"

# Get topics as hierarchy
curl -X GET "https://rw-api-491582996945.us-central1.run.app/api/topics?format=hierarchy" \
  -H "Authorization: Bearer <TOKEN>"
```

**Status Codes**:
- `200 OK` - Topics returned successfully
- `401 Unauthorized` - Missing or invalid token
- `500 Internal Server Error` - Server error

---

#### 2. Get Topic Detail

Get detailed information about a specific topic.

**Endpoint**: `GET /api/topics/<topic_id>`

**Path Parameters**:
- `topic_id` (string, required) - Topic ID (e.g., "T10312")

**Response**:
```json
{
  "id": "T10312",
  "display_name": "Cognitive Psychology",
  "description": "This topic covers research on cognitive processes including memory, attention, perception, decision-making, and problem-solving. Studies investigate how humans acquire, process, store, and retrieve information.",
  "keywords": [
    "cognition",
    "memory",
    "attention",
    "perception",
    "decision-making"
  ],
  "works_count": 125000,
  "cited_by_count": 3500000,
  "field": {
    "id": "F1",
    "display_name": "Social Sciences"
  },
  "domain": {
    "id": "D1",
    "display_name": "Social Sciences"
  },
  "subfield": {
    "id": "SF12",
    "display_name": "Psychology"
  },
  "openalex_url": "https://openalex.org/T10312",
  "wikipedia_url": "https://en.wikipedia.org/wiki/Cognitive_psychology",
  "cached_at": "2025-11-11T15:30:00Z"
}
```

**Example Request**:

```bash
curl -X GET "https://rw-api-491582996945.us-central1.run.app/api/topics/T10312" \
  -H "Authorization: Bearer <TOKEN>"
```

**Status Codes**:
- `200 OK` - Topic found and returned
- `401 Unauthorized` - Missing or invalid token
- `404 Not Found` - Topic not found
- `500 Internal Server Error` - Server error

---

#### 3. Search Topics

Search topics by keyword in display name, description, or keywords.

**Endpoint**: `GET /api/topics/search`

**Query Parameters**:
- `q` (string, required) - Search query
- `field` (string, optional) - Field filter (e.g., "Psychology")
- `limit` (integer, optional) - Maximum results (default 20, max 100)

**Response**:
```json
{
  "query": "memory",
  "count": 15,
  "topics": [
    {
      "id": "T10312",
      "display_name": "Cognitive Psychology",
      "description": "...including memory...",
      "keywords": ["cognition", "memory", "attention"],
      "works_count": 125000,
      "field": {
        "id": "F1",
        "display_name": "Social Sciences"
      }
    },
    // ... more matching topics
  ]
}
```

**Example Requests**:

```bash
# Search all topics for "memory"
curl -X GET "https://rw-api-491582996945.us-central1.run.app/api/topics/search?q=memory" \
  -H "Authorization: Bearer <TOKEN>"

# Search Psychology topics only
curl -X GET "https://rw-api-491582996945.us-central1.run.app/api/topics/search?q=memory&field=Psychology" \
  -H "Authorization: Bearer <TOKEN>"

# Limit to 50 results
curl -X GET "https://rw-api-491582996945.us-central1.run.app/api/topics/search?q=memory&limit=50" \
  -H "Authorization: Bearer <TOKEN>"
```

**Status Codes**:
- `200 OK` - Search completed (even if no results)
- `400 Bad Request` - Missing query parameter 'q'
- `401 Unauthorized` - Missing or invalid token
- `500 Internal Server Error` - Server error

**Notes**:
- Search is case-insensitive
- Searches in: display name, description, and keywords
- Results are returned in the order found (not ranked)
- Maximum 100 results enforced

---

#### 4. Get Fields

Get list of all unique fields for filtering topics.

**Endpoint**: `GET /api/topics/fields`

**Query Parameters**: None

**Response**:
```json
{
  "count": 6,
  "fields": [
    {
      "id": "F1",
      "display_name": "Social Sciences",
      "topic_count": 800
    },
    {
      "id": "F12",
      "display_name": "Psychology",
      "topic_count": 144
    },
    {
      "id": "F5",
      "display_name": "Economics",
      "topic_count": 120
    },
    {
      "id": "F7",
      "display_name": "Education",
      "topic_count": 98
    },
    {
      "id": "F9",
      "display_name": "Sociology",
      "topic_count": 85
    },
    {
      "id": "F11",
      "display_name": "Political Science",
      "topic_count": 240
    }
  ]
}
```

**Example Request**:

```bash
curl -X GET "https://rw-api-491582996945.us-central1.run.app/api/topics/fields" \
  -H "Authorization: Bearer <TOKEN>"
```

**Status Codes**:
- `200 OK` - Fields returned successfully
- `401 Unauthorized` - Missing or invalid token
- `500 Internal Server Error` - Server error

**Notes**:
- Fields are sorted by topic count (descending)
- Use `display_name` values to filter other endpoints

---

#### 5. Get Statistics

Get statistics about the topic collection.

**Endpoint**: `GET /api/topics/stats`

**Query Parameters**: None

**Response**:
```json
{
  "total_topics": 1487,
  "total_works": 45000000,
  "fields": {
    "Social Sciences": {
      "topic_count": 800,
      "works_count": 20000000
    },
    "Psychology": {
      "topic_count": 144,
      "works_count": 5000000
    },
    "Economics": {
      "topic_count": 120,
      "works_count": 4000000
    },
    "Education": {
      "topic_count": 98,
      "works_count": 3500000
    },
    "Sociology": {
      "topic_count": 85,
      "works_count": 3000000
    },
    "Political Science": {
      "topic_count": 240,
      "works_count": 9500000
    }
  },
  "top_topics": [
    {
      "id": "T10312",
      "display_name": "Cognitive Psychology",
      "works_count": 125000,
      "field": "Social Sciences"
    },
    // ... top 10 topics by works count
  ]
}
```

**Example Request**:

```bash
curl -X GET "https://rw-api-491582996945.us-central1.run.app/api/topics/stats" \
  -H "Authorization: Bearer <TOKEN>"
```

**Status Codes**:
- `200 OK` - Statistics returned successfully
- `401 Unauthorized` - Missing or invalid token
- `500 Internal Server Error` - Server error

**Notes**:
- `total_works` is the sum of all works across all topics
- Top 10 topics are sorted by works count (descending)

---

## Users API

Manage user profiles and preferences.

**Base Path**: `/api/users`
**Authentication**: Required

### Endpoints

#### Get User Profile

Get the authenticated user's profile.

**Endpoint**: `GET /api/users/profile`

**Response**:
```json
{
  "uid": "abc123def456",
  "email": "user@example.com",
  "display_name": "John Doe",
  "photo_url": "https://...",
  "created_at": "2025-11-01T10:00:00Z",
  "quota": {
    "searches_remaining": 45,
    "max_seeds": 10
  }
}
```

#### Update User Profile

Update user preferences.

**Endpoint**: `PUT /api/users/profile`

**Request Body**:
```json
{
  "display_name": "Jane Doe",
  "preferences": {
    "email_digest": true,
    "frequency": "daily"
  }
}
```

**Response**: Updated profile object (same structure as GET)

---

## Seeds API

Manage research interest keywords (seeds).

**Base Path**: `/api/seeds`
**Authentication**: Required

### Endpoints

#### Get All Seeds

Get all seeds for the authenticated user.

**Endpoint**: `GET /api/seeds`

**Response**:
```json
{
  "count": 3,
  "seeds": [
    {
      "id": "seed1",
      "keyword": "cognitive psychology",
      "created_at": "2025-11-01T10:00:00Z"
    },
    {
      "id": "seed2",
      "keyword": "memory consolidation",
      "created_at": "2025-11-02T14:30:00Z"
    },
    {
      "id": "seed3",
      "keyword": "machine learning",
      "created_at": "2025-11-05T09:15:00Z"
    }
  ]
}
```

#### Add Seed

Add a new research interest keyword.

**Endpoint**: `POST /api/seeds`

**Request Body**:
```json
{
  "keyword": "neural networks"
}
```

**Response**:
```json
{
  "id": "seed4",
  "keyword": "neural networks",
  "created_at": "2025-11-12T16:00:00Z"
}
```

**Status Codes**:
- `201 Created` - Seed added successfully
- `400 Bad Request` - Invalid keyword or quota exceeded
- `401 Unauthorized` - Not authenticated

#### Delete Seed

Remove a research interest keyword.

**Endpoint**: `DELETE /api/seeds/<seed_id>`

**Response**:
```json
{
  "success": true,
  "message": "Seed deleted"
}
```

---

## Digest API

Retrieve daily paper digests.

**Base Path**: `/api/digest`
**Authentication**: Required

### Endpoints

#### Get Latest Digest

Get the latest digest for the authenticated user.

**Endpoint**: `GET /api/digest/latest`

**Response**:
```json
{
  "uid": "abc123",
  "created_at": "2025-11-12T09:00:00Z",
  "papers_count": 50,
  "papers": [
    {
      "id": "10.1234_example",
      "title": "Example Paper Title",
      "authors": [
        {"name": "Smith, J.", "affiliation": "University X"}
      ],
      "abstract": "This paper presents...",
      "published_date": "2025-11-10",
      "source": "Nature",
      "citations": 15,
      "score": 85.5,
      "doi": "10.1234/example",
      "openalex_id": "W1234567890",
      "url": "https://doi.org/10.1234/example"
    }
    // ... 49 more papers
  ]
}
```

**Notes**:
- Digests are generated daily at 09:00 Buenos Aires time
- Papers are sorted by score (0-100) descending
- Maximum 50 papers per digest

---

## Search API

Search for papers in real-time across multiple sources.

**Base Path**: `/api/search`
**Authentication**: Required

### Endpoints

#### Search Papers

Search for academic papers across OpenAlex, Semantic Scholar, and arXiv.

**Endpoint**: `GET /api/search`

**Query Parameters**:
- `q` (string, required) - Search query
- `limit` (integer, optional) - Maximum results (default 20, max 100)

**Response**:
```json
{
  "query": "machine learning",
  "count": 50,
  "sources": ["openalex", "semantic_scholar", "arxiv"],
  "papers": [
    {
      "id": "10.1234_example",
      "title": "Deep Learning Advances",
      "authors": [{"name": "Jones, A."}],
      "abstract": "Recent advances in...",
      "published_date": "2025-11-01",
      "source": "arXiv",
      "citations": 5,
      "score": 72.3,
      "arxiv_id": "2511.12345",
      "url": "https://arxiv.org/abs/2511.12345"
    }
    // ... more papers
  ]
}
```

**Notes**:
- Results are deduplicated across sources
- Papers are scored based on citations, venue, recency, and open access
- Search is limited to preserve API quotas

---

## Saved Papers API

Manage saved/bookmarked papers.

**Base Path**: `/api/saved`
**Authentication**: Required

### Endpoints

#### Get Saved Papers

Get all saved papers for the authenticated user.

**Endpoint**: `GET /api/saved`

**Response**:
```json
{
  "count": 12,
  "papers": [
    {
      "id": "10.1234_example",
      "title": "Important Paper",
      "saved_at": "2025-11-10T14:30:00Z",
      "notes": "Read for lit review",
      // ... full paper object
    }
    // ... more papers
  ]
}
```

#### Save Paper

Add a paper to saved collection.

**Endpoint**: `POST /api/saved`

**Request Body**:
```json
{
  "paper_id": "10.1234_example",
  "notes": "Read for lit review"
}
```

**Response**: Saved paper object

#### Remove Saved Paper

Remove a paper from saved collection.

**Endpoint**: `DELETE /api/saved/<paper_id>`

**Response**:
```json
{
  "success": true,
  "message": "Paper removed from saved"
}
```

---

## Feedback API

Track user interactions with papers.

**Base Path**: `/api/feedback`
**Authentication**: Required

### Endpoints

#### Submit Feedback

Record user interaction with a paper (click, like, dismiss, etc.).

**Endpoint**: `POST /api/feedback`

**Request Body**:
```json
{
  "paper_id": "10.1234_example",
  "event_type": "click",
  "context": "digest",
  "metadata": {
    "position": 3,
    "score": 85.5
  }
}
```

**Event Types**:
- `click` - User clicked to view paper
- `like` - User marked as interesting
- `dismiss` - User dismissed/not interested
- `save` - User saved paper

**Response**:
```json
{
  "success": true,
  "event_id": "evt123"
}
```

---

## Collector API

Trigger paper collection (admin/scheduled use).

**Base Path**: `/api/collector`
**Authentication**: Required (internal use)

### Endpoints

#### Trigger Collection Run

Manually trigger paper collection for all users.

**Endpoint**: `POST /api/collect/run`

**Response**:
```json
{
  "status": "running",
  "users_processed": 5,
  "papers_collected": 245,
  "digests_created": 5,
  "errors": 0,
  "duration_seconds": 45.2
}
```

**Notes**:
- Typically triggered by Cloud Scheduler (daily at 09:00)
- Can be manually triggered for testing
- Processes all users with seeds

---

## Rate Limits

Current rate limits (Alpha phase):

- **Topics API**: No limit (cached data)
- **Search API**: 50 requests/day per user
- **Other endpoints**: 1000 requests/day per user

Rate limits enforced via Firestore user quota tracking.

**Rate Limit Response**:
```json
{
  "error": "rate_limit_exceeded",
  "message": "Daily search quota exceeded (50/50)",
  "retry_after": "2025-11-13T00:00:00Z"
}
```

---

## CORS Configuration

The API allows requests from the following origins:

- `https://app.researchwatcher.org` (production)
- `https://research-watcher.web.app`
- `https://research-watcher.firebaseapp.com`
- `https://storage.googleapis.com`
- `http://localhost:5000` (development)
- `http://localhost:8080` (development)

**Allowed Methods**: GET, POST, PUT, DELETE, OPTIONS
**Allowed Headers**: Content-Type, Authorization
**Supports Credentials**: Yes

---

## Pagination

Currently, pagination is not implemented. Endpoints return all results or enforce a limit:

- Topics: All topics returned (1,487 cached)
- Search: Max 100 results
- Digest: Max 50 papers
- Seeds: All seeds returned (max 10 per user)

Future versions will implement cursor-based pagination for large result sets.

---

## Webhooks

Webhooks are not yet implemented. Future versions will support:

- Digest completion notifications
- New paper alerts
- Collection status updates

---

## API Versioning

Current version: **v0.3** (Enhanced Discovery)

The API is currently in alpha and may change. Breaking changes will be announced and versioned appropriately before public release.

**Version History**:
- v0.3 (2025-11-12): Added Topics API (Enhanced Discovery Phase 1-2)
- v0.2 (2025-11-08): Added Collector + WAL pipeline
- v0.1 (2025-11-06): Initial backend core API

---

## Support

For API issues or questions:

1. Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
2. Review [DEPLOYMENT.md](./DEPLOYMENT.md) for infrastructure setup
3. Check Cloud Run logs: `gcloud logs read --service=rw-api`
4. Create a GitHub issue with API endpoint, request, and error details

---

**Last Updated**: 2025-11-12
**Maintainer**: Development Team
