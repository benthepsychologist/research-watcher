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
        # Get latest digest from digests/{uid}/latest
        digest_ref = db.collection('digests').document(uid).collection('items').document('latest')
        digest_doc = digest_ref.get()

        if not digest_doc.exists:
            return jsonify({
                'error': 'not_found',
                'message': 'No digest available yet. Wait for the daily collection to run.'
            }), 404

        digest_data = digest_doc.to_dict()
        return jsonify({
            'digest': digest_data
        }), 200

    except Exception as e:
        current_app.logger.error(f'Error fetching digest for {uid}: {str(e)}')
        return jsonify({
            'error': 'fetch_failed',
            'message': 'Failed to fetch digest'
        }), 500
