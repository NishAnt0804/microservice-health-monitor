"""
Notification Service — Dispatches alerts and notifications with health monitoring.
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
SERVICE_NAME = "notification-service"
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
# Mock Data Store — notification log
# ---------------------------------------------------------------------------
NOTIFICATIONS = []
NOTIFICATION_COUNTER = 0

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
@app.route("/api/notifications/health", methods=["GET"])
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
            "email_gateway": "connected",
            "sms_gateway": "connected",
        },
    }), 200


@app.route("/api/notifications", methods=["GET"])
def list_notifications():
    """Return recent notifications."""
    limit = request.args.get("limit", 50, type=int)
    recent = sorted(NOTIFICATIONS, key=lambda n: n["sent_at"], reverse=True)[:limit]
    return jsonify({
        "count": len(recent),
        "notifications": recent,
    }), 200


@app.route("/api/notifications/send", methods=["POST"])
def send_notification():
    """Dispatch a notification (mock — logs and stores)."""
    global NOTIFICATION_COUNTER
    data = request.get_json(silent=True)
    if not data or not data.get("recipient") or not data.get("message"):
        return jsonify({"error": "recipient and message are required"}), 400

    valid_channels = ["email", "sms", "slack", "webhook"]
    channel = data.get("channel", "email")
    if channel not in valid_channels:
        return jsonify({"error": f"channel must be one of {valid_channels}"}), 400

    NOTIFICATION_COUNTER += 1
    notification = {
        "id": str(NOTIFICATION_COUNTER),
        "recipient": data["recipient"],
        "message": data["message"],
        "channel": channel,
        "priority": data.get("priority", "normal"),
        "status": "sent",
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }
    NOTIFICATIONS.append(notification)

    logger.info(
        "notification_sent id=%s channel=%s recipient=%s priority=%s",
        notification["id"],
        channel,
        data["recipient"],
        notification["priority"],
    )
    return jsonify(notification), 201


@app.route("/api/notifications/stats", methods=["GET"])
def notification_stats():
    """Return notification statistics."""
    total = len(NOTIFICATIONS)
    by_channel = {}
    by_priority = {}
    for n in NOTIFICATIONS:
        by_channel[n["channel"]] = by_channel.get(n["channel"], 0) + 1
        by_priority[n["priority"]] = by_priority.get(n["priority"], 0) + 1

    return jsonify({
        "total_sent": total,
        "by_channel": by_channel,
        "by_priority": by_priority,
    }), 200


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5003))
    logger.info("Starting %s on port %s (version %s)", SERVICE_NAME, port, APP_VERSION)
    app.run(host="0.0.0.0", port=port)
