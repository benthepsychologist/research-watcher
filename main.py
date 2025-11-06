"""
Research Watcher - Main Entry Point

Entry point for Gunicorn in Cloud Run and local development.
"""

import os
from app import create_app

# Create Flask application
app = create_app()

if __name__ == "__main__":
    # Local development server
    port = int(os.environ.get("PORT", 3000))
    app.run(debug=True, host="0.0.0.0", port=port)