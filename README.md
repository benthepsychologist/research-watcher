# Research Watcher

## Overview

Research Watcher is a public-facing research-intelligence web application. It delivers ranked, daily digests of academic papers based on user interests (authors, venues, keywords). This project is built on a modern, serverless-first stack using Python, Flask, and Google Cloud Platform.

The core architecture is designed to be scalable and maintainable, starting with a simple dual-write system and providing a clear path to a fully event-sourced model.

## Current Status

- ✅ **Phase 0**: Bootstrap & Environment (Complete)
  - GCP infrastructure deployed
  - Firebase/Firestore configured
  - Cloud Run, Pub/Sub, BigQuery operational
  - 36 bash tests + 30 pytest tests passing

- ✅ **Phase 1**: Backend Core (API Skeleton) (Complete)
  - Flask app factory with Firebase Admin SDK
  - Authentication system (@login_required decorator)
  - All API blueprints implemented (users, seeds, digest, collector, feedback)
  - Deployed to Cloud Run: https://rw-api-491582996945.us-central1.run.app
  - 16 API integration tests written

- ⏳ **Phase 2**: Collector + Dual-Write (Next)
  - External API clients (OpenAlex, Semantic Scholar, Crossref, arXiv)
  - Paper collection and scoring logic
  - Dual-write to Firestore + Pub/Sub WAL

## Key Documents

This repository is organized and developed following a clear specification and an agent-driven implementation plan. All developers, human or AI, should familiarize themselves with these documents before contributing.

*   **[Project Specification](./docs/spec.md):** The canonical source of truth for the project's architecture, data models, and features (Spec v1.0).
*   **[Implementation Plan](./docs/AIP.md):** The step-by-step plan for building, deploying, and evolving the application (AIP v1.0).

## Technology Stack

*   **Backend:** Python 3 with the Flask micro-framework.
*   **Hosting:** Google Cloud Run for the backend API and Firebase Hosting for the static frontend.
*   **Database:** Firestore (Native Mode) for the primary application state.
*   **Authentication:** Firebase Authentication (Google & Email/Password).
*   **Event Bus:** Google Cloud Pub/Sub for a durable Write-Ahead Log (WAL).
*   **Data Warehouse:** Google BigQuery for the permanent event ledger.
*   **Scheduling:** Google Cloud Scheduler to trigger daily collection jobs.

## Development Environment

This project is configured to run in a Nix-based environment managed by Firebase Studio.

1.  **Activate Virtual Environment:** The environment uses a Python virtual environment located at `.venv`. You must activate it to access project dependencies:
    ```bash
    source .venv/bin/activate
    ```

2.  **Install Dependencies:** If new packages are added to `requirements.txt`, install them:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Development Server:** The Flask development server can be started using the provided script. This will make the API available for local testing and development.
    ```bash
    ./devserver.sh
    ```

Please refer to the [Implementation Plan](./docs/AIP.md) for detailed instructions on the phased development and deployment of this project.
