"""
Topics API Blueprint

Provides REST endpoints for browsing and searching OpenAlex topics.
Part of the Enhanced Discovery feature (Phase 1).
"""

from flask import Blueprint, jsonify, request
from google.cloud import firestore
from app.utils.auth import login_required
from app.services.openalex_topics import OpenAlexTopicsService


bp = Blueprint("topics", __name__, url_prefix="/api/topics")


@bp.route("", methods=["GET"])
@login_required
def get_topics():
    """
    Get all topics, optionally filtered by field.

    Query Parameters:
        field: Optional field name to filter by (e.g., "Psychology")
        format: Response format - "flat" (default) or "hierarchy"

    Returns:
        JSON response with topics list or hierarchy
    """
    try:
        db = firestore.client()
        topics_service = OpenAlexTopicsService(db)

        # Get query parameters
        field_name = request.args.get("field")
        response_format = request.args.get("format", "flat")

        # Fetch topics
        topics = topics_service.get_all_topics(field_name=field_name)

        if response_format == "hierarchy":
            # Build hierarchical structure
            hierarchy = topics_service.build_topic_hierarchy(topics)
            return jsonify({
                "format": "hierarchy",
                "count": len(topics),
                "hierarchy": hierarchy
            }), 200
        else:
            # Return flat list
            return jsonify({
                "format": "flat",
                "count": len(topics),
                "topics": topics
            }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/<topic_id>", methods=["GET"])
@login_required
def get_topic_detail(topic_id):
    """
    Get detailed information about a specific topic.

    Path Parameters:
        topic_id: Topic ID (e.g., "T123")

    Returns:
        JSON response with topic details
    """
    try:
        db = firestore.client()
        topics_service = OpenAlexTopicsService(db)

        # Fetch topic
        topic = topics_service.get_topic_by_id(topic_id)

        if not topic:
            return jsonify({"error": "Topic not found"}), 404

        return jsonify(topic), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/search", methods=["GET"])
@login_required
def search_topics():
    """
    Search topics by keyword in display name or description.

    Query Parameters:
        q: Search query
        field: Optional field filter
        limit: Maximum results (default 20, max 100)

    Returns:
        JSON response with matching topics
    """
    try:
        query = request.args.get("q", "").strip().lower()
        if not query:
            return jsonify({"error": "Query parameter 'q' is required"}), 400

        field_name = request.args.get("field")
        limit = min(int(request.args.get("limit", 20)), 100)

        db = firestore.client()
        topics_service = OpenAlexTopicsService(db)

        # Get all topics (with optional field filter)
        all_topics = topics_service.get_all_topics(field_name=field_name)

        # Filter by search query (simple text search)
        matching_topics = []
        for topic in all_topics:
            display_name = topic.get("display_name", "").lower()
            description = topic.get("description", "").lower()
            keywords = [kw.lower() for kw in topic.get("keywords", [])]

            if (query in display_name or
                query in description or
                any(query in kw for kw in keywords)):
                matching_topics.append(topic)

            if len(matching_topics) >= limit:
                break

        return jsonify({
            "query": query,
            "count": len(matching_topics),
            "topics": matching_topics
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/fields", methods=["GET"])
@login_required
def get_fields():
    """
    Get list of all unique fields (for filtering).

    Returns:
        JSON response with list of fields
    """
    try:
        db = firestore.client()
        topics_service = OpenAlexTopicsService(db)

        # Get all topics
        all_topics = topics_service.get_all_topics()

        # Extract unique fields
        fields = {}
        for topic in all_topics:
            field = topic.get("field")
            if field and field.get("id"):
                field_id = field.get("id")
                if field_id not in fields:
                    fields[field_id] = {
                        "id": field_id,
                        "display_name": field.get("display_name"),
                        "topic_count": 0
                    }
                fields[field_id]["topic_count"] += 1

        # Convert to list and sort by topic count
        fields_list = sorted(
            fields.values(),
            key=lambda x: x["topic_count"],
            reverse=True
        )

        return jsonify({
            "count": len(fields_list),
            "fields": fields_list
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/stats", methods=["GET"])
@login_required
def get_stats():
    """
    Get statistics about the topic collection.

    Returns:
        JSON response with statistics
    """
    try:
        db = firestore.client()
        topics_service = OpenAlexTopicsService(db)

        # Get all topics
        all_topics = topics_service.get_all_topics()

        # Calculate statistics
        total_topics = len(all_topics)
        total_works = sum(t.get("works_count", 0) for t in all_topics)

        # Count by field
        fields = {}
        for topic in all_topics:
            field = topic.get("field")
            if field and field.get("display_name"):
                field_name = field.get("display_name")
                if field_name not in fields:
                    fields[field_name] = {"topic_count": 0, "works_count": 0}
                fields[field_name]["topic_count"] += 1
                fields[field_name]["works_count"] += topic.get("works_count", 0)

        # Top topics by works count
        top_topics = sorted(
            all_topics,
            key=lambda x: x.get("works_count", 0),
            reverse=True
        )[:10]

        return jsonify({
            "total_topics": total_topics,
            "total_works": total_works,
            "fields": fields,
            "top_topics": [
                {
                    "id": t.get("id"),
                    "display_name": t.get("display_name"),
                    "works_count": t.get("works_count"),
                    "field": t.get("field", {}).get("display_name")
                }
                for t in top_topics
            ]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
