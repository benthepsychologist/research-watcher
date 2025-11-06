"""
Collector trigger endpoints.

Handles daily collection triggers from Cloud Scheduler.
Phase 1: Stubs only. Full implementation in Phase 2.
"""

from flask import Blueprint, jsonify, current_app
from app.utils.auth import scheduler_auth_required

bp = Blueprint('collector', __name__)


@bp.route('/run', methods=['POST'])
@scheduler_auth_required
def collect_run():
    """
    Trigger daily collection for all users.

    This endpoint is called by Cloud Scheduler with OIDC authentication.
    Phase 1: Returns stub response.
    Phase 2: Will implement full collection logic.

    Returns:
        200: Collection started
    """
    current_app.logger.info('Collection triggered by Cloud Scheduler')

    return jsonify({
        'status': 'stub',
        'message': 'Collection endpoint ready. Full implementation in Phase 2.',
        'phase': 1
    }), 200


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
