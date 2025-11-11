"""
Saved papers management endpoints.

Handles user's saved/bookmarked papers.
"""

from flask import Blueprint, request, jsonify, current_app
from app.utils.auth import login_required
from datetime import datetime

bp = Blueprint('saved', __name__)


@bp.route('/saved', methods=['GET'])
@login_required
def get_saved_papers(uid):
    """
    Get user's saved papers.

    Returns:
        200: List of saved papers
        500: Server error
    """
    db = current_app.db

    try:
        saved_ref = db.collection('users').document(uid).collection('saved')
        saved_docs = saved_ref.order_by('savedAt', direction='DESCENDING').stream()

        papers = []
        for doc in saved_docs:
            paper_data = doc.to_dict()
            papers.append(paper_data)

        return jsonify({
            'papers': papers,
            'count': len(papers)
        }), 200

    except Exception as e:
        current_app.logger.error(f'Error fetching saved papers for {uid}: {str(e)}')
        return jsonify({
            'error': 'fetch_failed',
            'message': 'Failed to fetch saved papers'
        }), 500


@bp.route('/saved', methods=['POST'])
@login_required
def save_paper(uid):
    """
    Save a paper to user's reading list.

    Body:
        {
            "paperId": "...",
            "title": "...",
            "authors": [...],
            "abstract": "...",
            "url": "...",
            "year": 2024,
            "citationCount": 100,
            "venue": "...",
            "score": 85
        }

    Returns:
        200: Paper saved
        400: Invalid request
        500: Server error
    """
    db = current_app.db

    try:
        data = request.get_json()
        if not data or 'paperId' not in data:
            return jsonify({
                'error': 'invalid_request',
                'message': 'Missing paperId in request body'
            }), 400

        paper_id = data['paperId']

        # Save paper to user's collection
        saved_ref = db.collection('users').document(uid).collection('saved').document(paper_id)
        saved_ref.set({
            **data,
            'savedAt': datetime.utcnow().isoformat() + 'Z',
            'userId': uid
        })

        return jsonify({
            'message': 'Paper saved successfully',
            'paperId': paper_id
        }), 200

    except Exception as e:
        current_app.logger.error(f'Error saving paper for {uid}: {str(e)}')
        return jsonify({
            'error': 'save_failed',
            'message': 'Failed to save paper'
        }), 500


@bp.route('/saved/<paper_id>', methods=['DELETE'])
@login_required
def unsave_paper(uid, paper_id):
    """
    Remove a paper from user's saved list.

    Returns:
        200: Paper removed
        500: Server error
    """
    db = current_app.db

    try:
        saved_ref = db.collection('users').document(uid).collection('saved').document(paper_id)
        saved_ref.delete()

        return jsonify({
            'message': 'Paper removed successfully',
            'paperId': paper_id
        }), 200

    except Exception as e:
        current_app.logger.error(f'Error removing saved paper for {uid}: {str(e)}')
        return jsonify({
            'error': 'unsave_failed',
            'message': 'Failed to remove saved paper'
        }), 500
