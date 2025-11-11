#!/usr/bin/env python3
"""
Fetch OpenAlex Topics and Cache in Firestore

This script fetches all psychology-related topics from OpenAlex
and caches them in Firestore for the Enhanced Discovery feature.

Usage:
    python scripts/fetch_openalex_topics.py [--max-results 1000] [--field Psychology]
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import firebase_admin
from firebase_admin import credentials, firestore
from app.services.openalex_topics import OpenAlexTopicsService


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Fetch OpenAlex topics and cache in Firestore"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=1000,
        help="Maximum number of topics to fetch (default: 1000)"
    )
    parser.add_argument(
        "--field",
        type=str,
        default=None,
        help="Filter by field name (e.g., 'Psychology')"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch topics but don't cache in Firestore"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("OpenAlex Topics Fetcher")
    print("=" * 60)
    print(f"Max results: {args.max_results}")
    print(f"Field filter: {args.field or 'None (all Social Sciences)'}")
    print(f"Dry run: {args.dry_run}")
    print("=" * 60)
    print()

    # Initialize Firebase Admin SDK
    print("Initializing Firebase...")
    try:
        # Check if already initialized
        firebase_admin.get_app()
        print("Firebase already initialized")
    except ValueError:
        # Not initialized, initialize now
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./serviceAccountKey.json")
        if not os.path.exists(cred_path):
            print(f"❌ Error: Service account key not found at {cred_path}")
            print("Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
            sys.exit(1)

        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized")

    # Get Firestore client
    db = firestore.client()

    # Initialize topics service
    topics_service = OpenAlexTopicsService(db)

    # Fetch topics from OpenAlex
    print("\n" + "=" * 60)
    print("STEP 1: Fetching topics from OpenAlex API")
    print("=" * 60)
    topics = topics_service.fetch_psychology_topics(max_results=args.max_results)

    if not topics:
        print("❌ No topics fetched. Exiting.")
        sys.exit(1)

    print(f"\n✅ Successfully fetched {len(topics)} topics")

    # Filter by field if specified
    if args.field:
        print(f"\nFiltering topics by field: {args.field}")
        topics = [
            t for t in topics
            if t.get("field", {}).get("display_name", "") == args.field
        ]
        print(f"Filtered to {len(topics)} topics in {args.field}")

    # Display sample topics
    print("\n" + "=" * 60)
    print("Sample Topics")
    print("=" * 60)
    for i, topic in enumerate(topics[:5]):
        print(f"\n{i+1}. {topic.get('display_name')}")
        print(f"   ID: {topic.get('id')}")
        print(f"   Field: {topic.get('field', {}).get('display_name')}")
        print(f"   Subfield: {topic.get('subfield', {}).get('display_name')}")
        print(f"   Works: {topic.get('works_count'):,}")
        print(f"   Description: {topic.get('description', 'N/A')[:100]}...")

    # Cache in Firestore
    if not args.dry_run:
        print("\n" + "=" * 60)
        print("STEP 2: Caching topics in Firestore")
        print("=" * 60)
        cached_count = topics_service.cache_topics_in_firestore(topics)

        print(f"\n✅ Successfully cached {cached_count} topics in Firestore")
    else:
        print("\n⏭️  Dry run mode - skipping Firestore caching")

    # Build and display hierarchy
    print("\n" + "=" * 60)
    print("STEP 3: Building topic hierarchy")
    print("=" * 60)
    hierarchy = topics_service.build_topic_hierarchy(topics)

    # Display hierarchy summary
    domains = hierarchy.get("domains", {})
    print(f"\nHierarchy Summary:")
    print(f"  Domains: {len(domains)}")

    for domain_id, domain in domains.items():
        print(f"\n  📁 {domain.get('display_name')} ({domain_id})")
        fields = domain.get("fields", {})
        print(f"     Fields: {len(fields)}")

        for field_id, field in fields.items():
            subfields = field.get("subfields", {})
            field_topics = field.get("topics", [])
            total_topics = len(field_topics) + sum(
                len(sf.get("topics", [])) for sf in subfields.values()
            )
            print(f"     └─ {field.get('display_name')}: {total_topics} topics")

    # Final summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✅ Fetched: {len(topics)} topics")
    if not args.dry_run:
        print(f"✅ Cached: {cached_count} topics in Firestore")
    print(f"✅ Domains: {len(domains)}")
    print("\nTopics are now ready for the Enhanced Discovery API!")
    print("\nNext steps:")
    print("  1. Deploy the topics API endpoints")
    print("  2. Build the frontend topic browser")
    print("  3. Test the hierarchy navigation")


if __name__ == "__main__":
    main()
