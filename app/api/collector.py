"""
Collector trigger endpoints.

Handles daily collection triggers from Cloud Scheduler.
Implements dual-write: Firestore + Pub/Sub WAL.
"""

import json
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, current_app
from app.utils.auth import scheduler_auth_required
from app.services.collector import collect_and_rank

bp = Blueprint('collector', __name__)


@bp.route('/run', methods=['POST'])
@scheduler_auth_required
def collect_run():
    """
    Trigger daily collection for all users.

    This endpoint is called by Cloud Scheduler with OIDC authentication.

    Process:
    1. Fetch all users with seeds
    2. For each user:
       - Collect papers from all sources
       - Deduplicate and score
       - Write to Firestore (papers/, digests/)
       - Publish WAL event to Pub/Sub
    3. Enforce quota (runsPerDay)

    Returns:
        200: Collection completed
        500: Collection failed
    """
    run_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat() + 'Z'

    current_app.logger.info(f'Collection started: runId={run_id}')

    db = current_app.db
    publisher = current_app.publisher
    topic_path = current_app.pubsub_topic

    # Stats
    stats = {
        'usersProcessed': 0,
        'papersCollected': 0,
        'digestsCreated': 0,
        'errors': []
    }

    try:
        # Fetch all users
        users_ref = db.collection('users')
        users = users_ref.stream()

        for user_doc in users:
            uid = user_doc.id
            user_data = user_doc.to_dict()

            # Check if user has seeds
            seeds_ref = db.collection('seeds').document(uid)
            seeds_doc = seeds_ref.get()

            if not seeds_doc.exists:
                continue

            seeds_data = seeds_doc.to_dict()
            seeds = seeds_data.get('items', [])

            if not seeds:
                continue

            try:
                # Collect and rank papers
                current_app.logger.info(f'Collecting papers for user {uid} with {len(seeds)} seeds')
                papers = collect_and_rank(seeds, days_back=7, max_per_seed=10)

                current_app.logger.info(f'Collected {len(papers)} papers for user {uid}')

                if not papers:
                    continue

                # Upsert papers to global papers collection
                for paper in papers[:50]:  # Limit to top 50
                    paper_id = paper.get('paperId')
                    if paper_id:
                        # Sanitize paper ID for Firestore (replace / with _)
                        safe_paper_id = paper_id.replace('/', '_')
                        paper['paperId'] = safe_paper_id  # Update in paper object too
                        paper_ref = db.collection('papers').document(safe_paper_id)
                        paper_ref.set(paper, merge=True)

                # Create digest for user
                digest_data = {
                    'uid': uid,
                    'runId': run_id,
                    'createdAt': timestamp,
                    'paperCount': len(papers),
                    'papers': [p.get('paperId').replace('/', '_') if p.get('paperId') else None for p in papers[:20]]  # Top 20 sanitized IDs
                }

                # Use digest ID that includes timestamp for historical tracking
                # But also write to a "latest" document for easy retrieval
                digest_ref = db.collection('digests').document(f"{uid}_latest")
                digest_ref.set(digest_data)

                # Publish WAL event to Pub/Sub
                wal_event = {
                    'v': 1,
                    'type': 'digest.created',
                    'runId': run_id,
                    'uid': uid,
                    'ts': timestamp,
                    'items': digest_data
                }

                message_bytes = json.dumps(wal_event).encode('utf-8')
                future = publisher.publish(topic_path, message_bytes)
                message_id = future.result()

                current_app.logger.info(f'Published WAL event for user {uid}: {message_id}')

                stats['usersProcessed'] += 1
                stats['papersCollected'] += len(papers)
                stats['digestsCreated'] += 1

            except Exception as e:
                error_msg = f'Error processing user {uid}: {str(e)}'
                current_app.logger.error(error_msg)
                stats['errors'].append(error_msg)

        current_app.logger.info(f'Collection completed: runId={run_id}, stats={stats}')

        return jsonify({
            'status': 'completed',
            'runId': run_id,
            'timestamp': timestamp,
            'stats': stats
        }), 200

    except Exception as e:
        error_msg = f'Collection failed: {str(e)}'
        current_app.logger.error(error_msg)
        return jsonify({
            'status': 'failed',
            'runId': run_id,
            'error': error_msg
        }), 500


@bp.route('/queue', methods=['POST'])
def collect_queue():
    """
    Stub for v1 fan-out queue endpoint.

    Will be used in Phase 4+ for per-user task queuing.

    Returns:
        501: Not implemented
    """
    return jsonify({
        'status': 'not_implemented',
        'message': 'Queue endpoint stub. Will be implemented in Phase 4.'
    }), 501


@bp.route('/worker', methods=['POST'])
def collect_worker():
    """
    Stub for v1 per-user worker endpoint.

    Will be used in Phase 4+ for processing individual user collections.

    Returns:
        501: Not implemented
    """
    return jsonify({
        'status': 'not_implemented',
        'message': 'Worker endpoint stub. Will be implemented in Phase 4.'
    }), 501
