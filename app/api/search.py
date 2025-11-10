"""
Search API Blueprint - Interactive paper search endpoint

Allows authenticated users to search for papers in real-time using
the same collection and ranking logic as the daily digest collector.
"""

from flask import Blueprint, request, jsonify
from app.utils.auth import login_required
from app.services.collector import collect_and_rank
from google.cloud import firestore
import os
import time
from datetime import datetime

bp = Blueprint('search', __name__, url_prefix='/api/search')
db = firestore.Client()


@bp.route('', methods=['GET'])
@login_required
def search_papers(uid):
    """
    Interactive search endpoint for authenticated users.

    Query Parameters:
        q (str): Search query (required)
        days_back (int): How many days back to search (default: 7)
        max_results (int): Maximum results to return (default: 20)

    Returns:
        JSON: {
            "papers": [...],
            "query": "...",
            "count": N,
            "durationMs": MS
        }

    Tracks search events to Firestore for analytics.
    """
    start_time = time.time()

    # Get query parameters
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    try:
        days_back = int(request.args.get('days_back', 7))
        max_results = int(request.args.get('max_results', 20))
    except ValueError:
        return jsonify({"error": "Invalid numeric parameter"}), 400

    # Validate ranges
    if days_back < 1 or days_back > 30:
        return jsonify({"error": "days_back must be between 1 and 30"}), 400

    if max_results < 1 or max_results > 50:
        return jsonify({"error": "max_results must be between 1 and 50"}), 400

    # Perform search using same logic as collector
    try:
        papers = collect_and_rank(
            seeds=[query],
            days_back=days_back,
            max_per_seed=max_results
        )

        # Limit to requested max_results
        papers = papers[:max_results]

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Track search event for analytics (async, non-blocking)
        try:
            event_ref = db.collection('events').document(uid).collection('searches').document()
            event_ref.set({
                'query': query,
                'resultsCount': len(papers),
                'durationMs': duration_ms,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'daysBack': days_back,
                'maxResults': max_results
            })
        except Exception as track_error:
            # Don't fail the request if tracking fails
            print(f"Warning: Failed to track search event: {track_error}")

        # Return results
        return jsonify({
            "papers": papers,
            "query": query,
            "count": len(papers),
            "durationMs": duration_ms
        }), 200

    except Exception as e:
        print(f"Search error for query '{query}': {e}")
        return jsonify({
            "error": "Search failed",
            "message": str(e)
        }), 500


@bp.route('/history', methods=['GET'])
@login_required
def search_history(uid):
    """
    Get user's search history (last 50 searches).

    Returns:
        JSON: {
            "searches": [
                {
                    "query": "...",
                    "timestamp": "...",
                    "resultsCount": N
                },
                ...
            ],
            "count": N
        }
    """
    try:
        # Fetch last 50 searches, ordered by timestamp descending
        searches_ref = db.collection('events').document(uid).collection('searches')
        searches = searches_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(50).stream()

        history = []
        for search_doc in searches:
            search_data = search_doc.to_dict()
            history.append({
                'query': search_data.get('query'),
                'timestamp': search_data.get('timestamp'),
                'resultsCount': search_data.get('resultsCount', 0),
                'durationMs': search_data.get('durationMs', 0)
            })

        return jsonify({
            "searches": history,
            "count": len(history)
        }), 200

    except Exception as e:
        print(f"Failed to fetch search history for {uid}: {e}")
        return jsonify({
            "error": "Failed to fetch search history",
            "message": str(e)
        }), 500
