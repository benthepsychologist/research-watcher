"""
User management endpoints.

Handles user profile creation and management.
"""

from flask import Blueprint, request, jsonify, current_app
from app.utils.auth import login_required
from datetime import datetime

bp = Blueprint('users', __name__)


@bp.route('/users/sync', methods=['POST'])
@login_required
def sync_user():
    """
    Idempotent user profile creation/sync.

    Creates or updates user profile in Firestore.
    Sets default quota and tier for new users.

    Headers:
        Authorization: Bearer <firebase_id_token>

    Returns:
        200: User synced successfully
        500: Server error
    """
    uid = request.uid
    db = current_app.db

    try:
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()

        now = datetime.utcnow().isoformat() + 'Z'

        if user_doc.exists:
            # Update existing user
            user_ref.update({
                'lastSyncAt': now
            })

            user_data = user_doc.to_dict()
            return jsonify({
                'status': 'synced',
                'user': {
                    'uid': uid,
                    'tier': user_data.get('tier', 'free'),
                    'quota': user_data.get('quota', {}),
                    'createdAt': user_data.get('createdAt'),
                    'lastSyncAt': now
                }
            }), 200

        else:
            # Create new user with defaults
            user_data = {
                'uid': uid,
                'tier': 'free',
                'quota': {
                    'runsPerDay': 1,
                    'maxSeeds': 3
                },
                'createdAt': now,
                'lastSyncAt': now
            }

            user_ref.set(user_data)

            return jsonify({
                'status': 'created',
                'user': user_data
            }), 201

    except Exception as e:
        current_app.logger.error(f'Error syncing user {uid}: {str(e)}')
        return jsonify({
            'error': 'sync_failed',
            'message': 'Failed to sync user profile'
        }), 500


@bp.route('/users/profile', methods=['GET'])
@login_required
def get_profile():
    """
    Get user profile.

    Headers:
        Authorization: Bearer <firebase_id_token>

    Returns:
        200: User profile
        404: User not found
        500: Server error
    """
    uid = request.uid
    db = current_app.db

    try:
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return jsonify({
                'error': 'user_not_found',
                'message': 'User profile not found. Call /api/users/sync first.'
            }), 404

        user_data = user_doc.to_dict()
        return jsonify({
            'user': user_data
        }), 200

    except Exception as e:
        current_app.logger.error(f'Error fetching profile for {uid}: {str(e)}')
        return jsonify({
            'error': 'fetch_failed',
            'message': 'Failed to fetch user profile'
        }), 500
