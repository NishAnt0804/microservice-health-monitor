"""
User Service — Manages user data with health monitoring.
Part of the Microservice Health Monitor platform.
"""

import os
import time
import uuid
import logging
from datetime import datetime, timezone
from flask import Flask, jsonify, request, g
from flask_cors import CORS

# ---------------------------------------------------------------------------
# App Configuration
# ---------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
SERVICE_NAME = "user-service"
START_TIME = time.time()

# ---------------------------------------------------------------------------
# Structured Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(SERVICE_NAME)

# ---------------------------------------------------------------------------
# Mock Data Store
# ---------------------------------------------------------------------------
USERS = {
    "1": {"id": "1", "name": "Alice Johnson", "email": "alice@example.com", "role": "admin"},
    "2": {"id": "2", "name": "Bob Smith", "email": "bob@example.com", "role": "user"},
    "3": {"id": "3", "name": "Charlie Brown", "email": "charlie@example.com", "role": "user"},
    "4": {"id": "4", "name": "Diana Prince", "email": "diana@example.com", "role": "moderator"},
    "5": {"id": "5", "name": "Eve Davis", "email": "eve@example.com", "role": "user"},
}

# ---------------------------------------------------------------------------
# Middleware — Request ID tracing
# ---------------------------------------------------------------------------
@app.before_request
def attach_request_id():
    g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    g.start_time = time.time()


@app.after_request
def log_request(response):
    duration_ms = round((time.time() - g.start_time) * 1000, 2)
    logger.info(
        "method=%s path=%s status=%s duration_ms=%s request_id=%s",
        request.method,
        request.path,
        response.status_code,
        duration_ms,
        g.request_id,
    )
    response.headers["X-Request-ID"] = g.request_id
    return response


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/api/users/health", methods=["GET"])
def health_check():
    """Health check endpoint for ALB and dashboard."""
    uptime_seconds = round(time.time() - START_TIME, 2)
    return jsonify({
        "service": SERVICE_NAME,
        "status": "healthy",
        "version": APP_VERSION,
        "uptime_seconds": uptime_seconds,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {
            "data_store": "connected",
            "memory": "ok",
        },
    }), 200


@app.route("/api/users", methods=["GET"])
def list_users():
    """Return all users with optional role filtering."""
    role = request.args.get("role")
    users = list(USERS.values())
    if role:
        users = [u for u in users if u["role"] == role]
    return jsonify({
        "count": len(users),
        "users": users,
    }), 200


@app.route("/api/users/<user_id>", methods=["GET"])
def get_user(user_id):
    """Return a single user by ID."""
    user = USERS.get(user_id)
    if not user:
        return jsonify({"error": "User not found", "user_id": user_id}), 404
    return jsonify(user), 200


@app.route("/api/users", methods=["POST"])
def create_user():
    """Create a new user."""
    data = request.get_json(silent=True)
    if not data or not data.get("name") or not data.get("email"):
        return jsonify({"error": "name and email are required"}), 400

    new_id = str(max(int(k) for k in USERS.keys()) + 1)
    new_user = {
        "id": new_id,
        "name": data["name"],
        "email": data["email"],
        "role": data.get("role", "user"),
    }
    USERS[new_id] = new_user
    logger.info("user_created id=%s name=%s", new_id, data["name"])
    return jsonify(new_user), 201


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    logger.info("Starting %s on port %s (version %s)", SERVICE_NAME, port, APP_VERSION)
    app.run(host="0.0.0.0", port=port)
