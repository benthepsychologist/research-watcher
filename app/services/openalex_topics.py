"""
OpenAlex Topics Service

Fetches and caches OpenAlex topics for field-wide discovery.
Uses the OpenAlex Topics API to build a hierarchical topic structure.
"""

import requests
import time
from typing import List, Dict, Optional
from google.cloud import firestore


class OpenAlexTopicsService:
    """Service for fetching and managing OpenAlex topics."""

    BASE_URL = "https://api.openalex.org/topics"
    POLITE_POOL_EMAIL = "noreply@researchwatcher.org"

    def __init__(self, db: firestore.Client):
        """
        Initialize the OpenAlex topics service.

        Args:
            db: Firestore client instance
        """
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"ResearchWatcher/1.0 (mailto:{self.POLITE_POOL_EMAIL})"
        })

    def fetch_psychology_topics(self, max_results: int = 1000) -> List[Dict]:
        """
        Fetch all psychology topics from OpenAlex.

        Psychology is within the Social Sciences domain (domain.id=2).
        We'll fetch all topics in this domain and filter for psychology field.

        Args:
            max_results: Maximum number of topics to fetch (default 1000)

        Returns:
            List of topic dictionaries with hierarchy information
        """
        topics = []
        cursor = "*"
        per_page = 200  # Max allowed by OpenAlex

        # Filter for Social Sciences domain (includes Psychology)
        # Domain ID 2 = Social Sciences
        # https://api.openalex.org/domains/2
        filter_query = "domain.id:2"

        print(f"Fetching topics from OpenAlex (domain: Social Sciences)...")

        while len(topics) < max_results:
            try:
                params = {
                    "filter": filter_query,
                    "per-page": per_page,
                    "cursor": cursor
                }

                response = self.session.get(self.BASE_URL, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                results = data.get("results", [])

                if not results:
                    print("No more results to fetch")
                    break

                # Process and add topics
                for topic in results:
                    processed = self._process_topic(topic)
                    if processed:
                        topics.append(processed)

                print(f"Fetched {len(topics)} topics so far...")

                # Get next cursor
                meta = data.get("meta", {})
                next_cursor = meta.get("next_cursor")

                if not next_cursor or next_cursor == cursor:
                    print("Reached end of results")
                    break

                cursor = next_cursor

                # Be polite to OpenAlex API
                time.sleep(0.1)

            except requests.exceptions.RequestException as e:
                print(f"Error fetching topics: {e}")
                break

        print(f"✅ Fetched {len(topics)} total topics")
        return topics

    def _process_topic(self, raw_topic: Dict) -> Optional[Dict]:
        """
        Process a raw topic from OpenAlex API into our format.

        Args:
            raw_topic: Raw topic dictionary from OpenAlex

        Returns:
            Processed topic dictionary or None if invalid
        """
        try:
            topic_id = raw_topic.get("id", "").split("/")[-1]  # Extract T123 from URL

            if not topic_id:
                return None

            # Extract hierarchy information
            domain = raw_topic.get("domain", {})
            field = raw_topic.get("field", {})
            subfield = raw_topic.get("subfield", {})

            processed = {
                "id": topic_id,
                "openalex_id": raw_topic.get("id", ""),
                "display_name": raw_topic.get("display_name", ""),
                "description": raw_topic.get("description", ""),
                "keywords": raw_topic.get("keywords", []),
                "works_count": raw_topic.get("works_count", 0),
                "cited_by_count": raw_topic.get("cited_by_count", 0),

                # Hierarchy
                "domain": {
                    "id": domain.get("id", "").split("/")[-1] if domain.get("id") else None,
                    "display_name": domain.get("display_name", "")
                } if domain else None,

                "field": {
                    "id": field.get("id", "").split("/")[-1] if field.get("id") else None,
                    "display_name": field.get("display_name", "")
                } if field else None,

                "subfield": {
                    "id": subfield.get("id", "").split("/")[-1] if subfield.get("id") else None,
                    "display_name": subfield.get("display_name", "")
                } if subfield else None,

                # Metadata
                "updated_date": raw_topic.get("updated_date", ""),
                "created_at": firestore.SERVER_TIMESTAMP
            }

            return processed

        except Exception as e:
            print(f"Error processing topic: {e}")
            return None

    def cache_topics_in_firestore(self, topics: List[Dict]) -> int:
        """
        Cache topics in Firestore for fast retrieval.

        Args:
            topics: List of processed topic dictionaries

        Returns:
            Number of topics successfully cached
        """
        cached_count = 0
        batch = self.db.batch()
        batch_size = 0
        max_batch_size = 500  # Firestore limit

        print(f"Caching {len(topics)} topics in Firestore...")

        for topic in topics:
            try:
                topic_id = topic.get("id")
                if not topic_id:
                    continue

                # Reference to topics collection
                topic_ref = self.db.collection("topics").document(topic_id)
                batch.set(topic_ref, topic)
                batch_size += 1
                cached_count += 1

                # Commit batch if we hit the limit
                if batch_size >= max_batch_size:
                    batch.commit()
                    print(f"  Committed batch of {batch_size} topics...")
                    batch = self.db.batch()
                    batch_size = 0
                    time.sleep(0.1)  # Brief pause between batches

            except Exception as e:
                print(f"Error caching topic {topic.get('id')}: {e}")

        # Commit remaining topics
        if batch_size > 0:
            batch.commit()
            print(f"  Committed final batch of {batch_size} topics")

        print(f"✅ Cached {cached_count} topics in Firestore")
        return cached_count

    def get_topic_by_id(self, topic_id: str) -> Optional[Dict]:
        """
        Retrieve a topic from Firestore by ID.

        Args:
            topic_id: Topic ID (e.g., "T123")

        Returns:
            Topic dictionary or None if not found
        """
        try:
            topic_ref = self.db.collection("topics").document(topic_id)
            topic_doc = topic_ref.get()

            if topic_doc.exists:
                return topic_doc.to_dict()
            return None

        except Exception as e:
            print(f"Error retrieving topic {topic_id}: {e}")
            return None

    def get_all_topics(self, field_name: Optional[str] = None) -> List[Dict]:
        """
        Retrieve all topics from Firestore, optionally filtered by field.

        Args:
            field_name: Optional field name to filter by (e.g., "Psychology")

        Returns:
            List of topic dictionaries
        """
        try:
            topics_ref = self.db.collection("topics")

            if field_name:
                # Filter by field display_name
                query = topics_ref.where("field.display_name", "==", field_name)
            else:
                query = topics_ref

            # Order by works_count descending for relevance
            query = query.order_by("works_count", direction=firestore.Query.DESCENDING)

            topics = []
            for doc in query.stream():
                topic = doc.to_dict()
                topic["id"] = doc.id  # Ensure ID is included
                topics.append(topic)

            return topics

        except Exception as e:
            print(f"Error retrieving topics: {e}")
            return []

    def build_topic_hierarchy(self, topics: List[Dict]) -> Dict:
        """
        Build a hierarchical tree structure from flat topic list.

        Returns a nested structure:
        {
          "domains": {
            "domain_id": {
              "display_name": "...",
              "fields": {
                "field_id": {
                  "display_name": "...",
                  "subfields": {
                    "subfield_id": {
                      "display_name": "...",
                      "topics": [...]
                    }
                  }
                }
              }
            }
          }
        }

        Args:
            topics: List of topic dictionaries

        Returns:
            Hierarchical tree structure
        """
        hierarchy = {"domains": {}}

        for topic in topics:
            domain = topic.get("domain")
            field = topic.get("field")
            subfield = topic.get("subfield")

            if not domain or not field:
                continue

            domain_id = domain.get("id")
            field_id = field.get("id")
            subfield_id = subfield.get("id") if subfield else None

            # Initialize domain
            if domain_id not in hierarchy["domains"]:
                hierarchy["domains"][domain_id] = {
                    "id": domain_id,
                    "display_name": domain.get("display_name"),
                    "fields": {}
                }

            # Initialize field
            if field_id not in hierarchy["domains"][domain_id]["fields"]:
                hierarchy["domains"][domain_id]["fields"][field_id] = {
                    "id": field_id,
                    "display_name": field.get("display_name"),
                    "subfields": {}
                }

            # Initialize subfield (if exists)
            if subfield_id:
                if subfield_id not in hierarchy["domains"][domain_id]["fields"][field_id]["subfields"]:
                    hierarchy["domains"][domain_id]["fields"][field_id]["subfields"][subfield_id] = {
                        "id": subfield_id,
                        "display_name": subfield.get("display_name"),
                        "topics": []
                    }

                # Add topic to subfield
                hierarchy["domains"][domain_id]["fields"][field_id]["subfields"][subfield_id]["topics"].append({
                    "id": topic.get("id"),
                    "display_name": topic.get("display_name"),
                    "works_count": topic.get("works_count", 0),
                    "description": topic.get("description", "")
                })
            else:
                # Add topic directly to field if no subfield
                if "topics" not in hierarchy["domains"][domain_id]["fields"][field_id]:
                    hierarchy["domains"][domain_id]["fields"][field_id]["topics"] = []

                hierarchy["domains"][domain_id]["fields"][field_id]["topics"].append({
                    "id": topic.get("id"),
                    "display_name": topic.get("display_name"),
                    "works_count": topic.get("works_count", 0),
                    "description": topic.get("description", "")
                })

        return hierarchy
