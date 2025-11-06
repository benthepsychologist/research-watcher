"""
Research Watcher - Flask Application Factory

Initializes Flask app with Firebase Admin SDK and registers blueprints.
"""

import os
from flask import Flask
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import pubsub_v1


def create_app():
    """
    Application factory for Research Watcher Flask app.

    Initializes:
    - Flask application
    - Firebase Admin SDK
    - Firestore client
    - Pub/Sub publisher client
    - Registers all API blueprints

    Returns:
        Flask: Configured Flask application
    """
    # Create Flask app
    app = Flask(__name__)

    # Load configuration from environment
    app.config['PROJECT_ID'] = os.getenv('GOOGLE_CLOUD_PROJECT', 'research-watcher')
    app.config['DEBUG'] = os.getenv('FLASK_ENV', 'production') == 'development'

    # Initialize Firebase Admin SDK
    if not firebase_admin._apps:
        # Check if running in Cloud Run (uses default credentials)
        cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if cred_path and os.path.exists(cred_path):
            # Local development with service account key
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'projectId': app.config['PROJECT_ID']
            })
        else:
            # Cloud Run with default service account
            firebase_admin.initialize_app(options={
                'projectId': app.config['PROJECT_ID']
            })

    # Initialize Firestore client
    db = firestore.client()
    app.db = db

    # Initialize Pub/Sub publisher client
    publisher = pubsub_v1.PublisherClient()
    app.publisher = publisher
    app.pubsub_topic = f"projects/{app.config['PROJECT_ID']}/topics/rw-wal"

    # Register blueprints
    from app.api import users, seeds, digest, collector, feedback

    app.register_blueprint(users.bp, url_prefix='/api')
    app.register_blueprint(seeds.bp, url_prefix='/api')
    app.register_blueprint(digest.bp, url_prefix='/api')
    app.register_blueprint(collector.bp, url_prefix='/api/collect')
    app.register_blueprint(feedback.bp, url_prefix='/api')

    # Health check endpoint
    @app.route('/')
    def health_check():
        """Health check endpoint"""
        return {
            'status': 'healthy',
            'service': 'research-watcher-api',
            'version': '0.1.0'
        }

    return app
