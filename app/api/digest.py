"""
Digest retrieval endpoints.

Handles fetching user's latest research digest.
"""

from flask import Blueprint, request, jsonify, current_app
from app.utils.auth import login_required

bp = Blueprint('digest', __name__)


@bp.route('/digest/latest', methods=['GET'])
@login_required
def get_latest_digest():
    """
    Get user's latest research digest.

    Headers:
        Authorization: Bearer <firebase_id_token>

    Returns:
        200: Latest digest
        404: No digest found
        500: Server error
    """
    uid = request.uid
    db = current_app.db

    try:
        # Get latest digest using composite document ID
        digest_ref = db.collection('digests').document(f"{uid}_latest")
        digest_doc = digest_ref.get()

        if not digest_doc.exists:
            return jsonify({
                'error': 'not_found',
                'message': 'No digest available yet. Wait for the daily collection to run.'
            }), 404

        digest_data = digest_doc.to_dict()

        # Expand paper details from papers collection
        paper_ids = digest_data.get('papers', [])
        papers = []

        for paper_id in paper_ids:
            paper_ref = db.collection('papers').document(paper_id)
            paper_doc = paper_ref.get()

            if paper_doc.exists:
                paper_data = paper_doc.to_dict()
                papers.append(paper_data)

        # Sort by score descending
        papers.sort(key=lambda p: p.get('score', 0), reverse=True)

        # Return digest with expanded papers
        result = {
            'runId': digest_data.get('runId'),
            'createdAt': digest_data.get('createdAt'),
            'paperCount': len(papers),
            'papers': papers
        }

        return jsonify({
            'digest': result
        }), 200

    except Exception as e:
        current_app.logger.error(f'Error fetching digest for {uid}: {str(e)}')
        return jsonify({
            'error': 'fetch_failed',
            'message': 'Failed to fetch digest'
        }), 500
