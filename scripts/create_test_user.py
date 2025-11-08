#!/usr/bin/env python3
"""
Create a test user in Firestore for Phase 2 acceptance testing.

This script creates a test user with seeds so we can trigger
the collector and verify the full pipeline works.
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin
cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', './serviceAccountKey.json')
if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Test user ID
TEST_UID = "test-user-phase2"

def create_test_user():
    """Create test user profile"""
    print(f"\n Creating test user: {TEST_UID}")

    user_data = {
        'uid': TEST_UID,
        'tier': 'free',
        'quota': {
            'runsPerDay': 1,
            'maxSeeds': 3
        },
        'createdAt': datetime.utcnow().isoformat() + 'Z',
        'lastSyncAt': datetime.utcnow().isoformat() + 'Z'
    }

    user_ref = db.collection('users').document(TEST_UID)
    user_ref.set(user_data)

    print(f"✓ Created user profile")
    return user_data

def create_test_seeds():
    """Create test research seeds"""
    print(f"\n Creating research seeds for {TEST_UID}")

    # Use diverse seeds to test different APIs
    seeds = [
        "large language models",  # Should hit all sources
        "quantum computing",      # Should hit arXiv especially
        "CRISPR gene editing"     # Should hit OpenAlex/S2
    ]

    seeds_data = {
        'items': seeds,
        'updatedAt': datetime.utcnow().isoformat() + 'Z'
    }

    seeds_ref = db.collection('seeds').document(TEST_UID)
    seeds_ref.set(seeds_data)

    print(f"✓ Created {len(seeds)} seeds:")
    for seed in seeds:
        print(f"  - {seed}")

    return seeds_data

def verify_user_created():
    """Verify user and seeds exist in Firestore"""
    print("\n Verifying user creation...")

    # Check user
    user_ref = db.collection('users').document(TEST_UID)
    user_doc = user_ref.get()

    if not user_doc.exists:
        print("❌ User not found!")
        return False

    print(f"✓ User exists")

    # Check seeds
    seeds_ref = db.collection('seeds').document(TEST_UID)
    seeds_doc = seeds_ref.get()

    if not seeds_doc.exists:
        print("❌ Seeds not found!")
        return False

    seeds_data = seeds_doc.to_dict()
    print(f"✓ Seeds exist ({len(seeds_data.get('items', []))} seeds)")

    return True

if __name__ == "__main__":
    print("="*60)
    print("CREATING TEST USER FOR PHASE 2 ACCEPTANCE")
    print("="*60)

    try:
        user_data = create_test_user()
        seeds_data = create_test_seeds()

        if verify_user_created():
            print("\n" + "="*60)
            print("✅ TEST USER CREATED SUCCESSFULLY")
            print("="*60)
            print(f"\nTest UID: {TEST_UID}")
            print(f"Seeds: {', '.join(seeds_data['items'])}")
            print(f"\nNext steps:")
            print(f"1. Trigger collector: curl -X POST https://rw-api-491582996945.us-central1.run.app/api/collect/run")
            print(f"2. Check logs for papers collected")
            print(f"3. Query digest (need Firebase auth token)")
            print(f"4. Verify WAL events in BigQuery")
            sys.exit(0)
        else:
            print("\n❌ VERIFICATION FAILED")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
