"""
Research seeds management endpoints.

Handles CRUD operations for user research seeds.
"""

from flask import Blueprint, request, jsonify, current_app
from app.utils.auth import login_required
from google.cloud import firestore

bp = Blueprint('seeds', __name__)


@bp.route('/seeds', methods=['GET'])
@login_required
def get_seeds():
    """
    Get user's research seeds.

    Headers:
        Authorization: Bearer <firebase_id_token>

    Returns:
        200: List of seeds
        500: Server error
    """
    uid = request.uid
    db = current_app.db

    try:
        seeds_ref = db.collection('seeds').document(uid)
        seeds_doc = seeds_ref.get()

        if not seeds_doc.exists:
            return jsonify({
                'seeds': []
            }), 200

        seeds_data = seeds_doc.to_dict()
        return jsonify({
            'seeds': seeds_data.get('items', [])
        }), 200

    except Exception as e:
        current_app.logger.error(f'Error fetching seeds for {uid}: {str(e)}')
        return jsonify({
            'error': 'fetch_failed',
            'message': 'Failed to fetch research seeds'
        }), 500


@bp.route('/seeds', methods=['POST'])
@login_required
def update_seeds():
    """
    Update user's research seeds.

    Enforces maxSeeds quota.

    Headers:
        Authorization: Bearer <firebase_id_token>

    Body:
        {
            "seeds": ["keyword1", "keyword2", ...]
        }

    Returns:
        200: Seeds updated
        400: Invalid request or quota exceeded
        500: Server error
    """
    uid = request.uid
    db = current_app.db

    try:
        data = request.get_json()
        if not data or 'seeds' not in data:
            return jsonify({
                'error': 'invalid_request',
                'message': 'Missing seeds array in request body'
            }), 400

        seeds = data['seeds']

        if not isinstance(seeds, list):
            return jsonify({
                'error': 'invalid_request',
                'message': 'seeds must be an array'
            }), 400

        # Check user quota
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return jsonify({
                'error': 'user_not_found',
                'message': 'User profile not found. Call /api/users/sync first.'
            }), 404

        user_data = user_doc.to_dict()
        max_seeds = user_data.get('quota', {}).get('maxSeeds', 3)

        if len(seeds) > max_seeds:
            return jsonify({
                'error': 'quota_exceeded',
                'message': f'Maximum {max_seeds} seeds allowed for your tier'
            }), 400

        # Update seeds
        seeds_ref = db.collection('seeds').document(uid)
        seeds_ref.set({
            'items': seeds,
            'updatedAt': firestore.SERVER_TIMESTAMP
        })

        return jsonify({
            'status': 'updated',
            'seeds': seeds
        }), 200

    except Exception as e:
        current_app.logger.error(f'Error updating seeds for {uid}: {str(e)}')
        return jsonify({
            'error': 'update_failed',
            'message': 'Failed to update research seeds'
        }), 500
