"""
User feedback endpoints.

Handles user feedback on papers and recommendations.
"""

from flask import Blueprint, request, jsonify, current_app
from app.utils.auth import login_required
from datetime import datetime

bp = Blueprint('feedback', __name__)


@bp.route('/feedback', methods=['POST'])
@login_required
def submit_feedback():
    """
    Submit user feedback on a paper.

    Headers:
        Authorization: Bearer <firebase_id_token>

    Body:
        {
            "paperId": "string",
            "action": "thumbs_up" | "thumbs_down" | "save" | "dismiss",
            "context": "digest" | "search"
        }

    Returns:
        201: Feedback recorded
        400: Invalid request
        500: Server error
    """
    uid = request.uid
    db = current_app.db

    try:
        data = request.get_json()

        if not data or 'paperId' not in data or 'action' not in data:
            return jsonify({
                'error': 'invalid_request',
                'message': 'Missing paperId or action in request body'
            }), 400

        valid_actions = ['thumbs_up', 'thumbs_down', 'save', 'dismiss']
        if data['action'] not in valid_actions:
            return jsonify({
                'error': 'invalid_action',
                'message': f'Action must be one of: {", ".join(valid_actions)}'
            }), 400

        # Store feedback in events/{uid}/feedback subcollection
        feedback_data = {
            'paperId': data['paperId'],
            'action': data['action'],
            'context': data.get('context', 'unknown'),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        events_ref = db.collection('events').document(uid).collection('feedback')
        events_ref.add(feedback_data)

        return jsonify({
            'status': 'recorded',
            'feedback': feedback_data
        }), 201

    except Exception as e:
        current_app.logger.error(f'Error recording feedback for {uid}: {str(e)}')
        return jsonify({
            'error': 'recording_failed',
            'message': 'Failed to record feedback'
        }), 500
