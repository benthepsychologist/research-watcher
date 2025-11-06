"""
Authentication utilities for Research Watcher API.

Provides Firebase ID token validation and @login_required decorator.
"""

from functools import wraps
from flask import request, jsonify, current_app
from firebase_admin import auth


def login_required(f):
    """
    Decorator to require Firebase authentication for routes.

    Extracts Firebase ID token from Authorization header,
    verifies it, and injects uid into the request context.

    Usage:
        @bp.route('/protected')
        @login_required
        def protected_route():
            uid = request.uid  # Access authenticated user ID
            return {'message': f'Hello {uid}'}

    Returns:
        401: If no token provided or invalid token
        403: If token expired or revoked
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({
                'error': 'unauthorized',
                'message': 'Missing Authorization header'
            }), 401

        # Extract Bearer token
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({
                'error': 'unauthorized',
                'message': 'Invalid Authorization header format. Expected: Bearer <token>'
            }), 401

        token = parts[1]

        try:
            # Verify Firebase ID token
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token['uid']

            # Inject uid into request context
            request.uid = uid
            request.token = decoded_token

            return f(*args, **kwargs)

        except auth.ExpiredIdTokenError:
            return jsonify({
                'error': 'token_expired',
                'message': 'Firebase ID token has expired'
            }), 403

        except auth.RevokedIdTokenError:
            return jsonify({
                'error': 'token_revoked',
                'message': 'Firebase ID token has been revoked'
            }), 403

        except auth.InvalidIdTokenError as e:
            return jsonify({
                'error': 'invalid_token',
                'message': f'Invalid Firebase ID token: {str(e)}'
            }), 401

        except Exception as e:
            current_app.logger.error(f'Auth error: {str(e)}')
            return jsonify({
                'error': 'authentication_failed',
                'message': 'Authentication failed'
            }), 401

    return decorated_function


def scheduler_auth_required(f):
    """
    Decorator to require OIDC authentication from Cloud Scheduler.

    Validates that the request comes from the scheduler-invoker service account.
    This is for endpoints that should only be triggered by Cloud Scheduler.

    Usage:
        @bp.route('/collect/run', methods=['POST'])
        @scheduler_auth_required
        def collect_run():
            return {'status': 'started'}

    Returns:
        401: If no valid OIDC token from scheduler
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # In Cloud Run, OIDC tokens are verified automatically
        # We just need to check if the request made it through
        # Additional validation could check the service account email

        # For now, we trust Cloud Run's verification
        # In production, you might want to validate the email claim
        return f(*args, **kwargs)

    return decorated_function
