"""
Order Service — Manages orders with health monitoring.
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
SERVICE_NAME = "order-service"
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
ORDERS = {
    "101": {
        "id": "101",
        "user_id": "1",
        "product": "Cloud Architecture Handbook",
        "quantity": 1,
        "price": 49.99,
        "status": "delivered",
        "created_at": "2026-06-01T10:00:00Z",
    },
    "102": {
        "id": "102",
        "user_id": "2",
        "product": "DevOps Toolkit Pro",
        "quantity": 2,
        "price": 29.99,
        "status": "processing",
        "created_at": "2026-06-10T14:30:00Z",
    },
    "103": {
        "id": "103",
        "user_id": "1",
        "product": "Terraform Masterclass",
        "quantity": 1,
        "price": 79.99,
        "status": "shipped",
        "created_at": "2026-06-11T09:15:00Z",
    },
}

ORDER_COUNTER = 103

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
@app.route("/api/orders/health", methods=["GET"])
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
            "queue": "ok",
        },
    }), 200


@app.route("/api/orders", methods=["GET"])
def list_orders():
    """Return all orders with optional user_id filtering."""
    user_id = request.args.get("user_id")
    orders = list(ORDERS.values())
    if user_id:
        orders = [o for o in orders if o["user_id"] == user_id]
    return jsonify({
        "count": len(orders),
        "orders": orders,
    }), 200


@app.route("/api/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    """Return a single order by ID."""
    order = ORDERS.get(order_id)
    if not order:
        return jsonify({"error": "Order not found", "order_id": order_id}), 404
    return jsonify(order), 200


@app.route("/api/orders", methods=["POST"])
def create_order():
    """Create a new order."""
    global ORDER_COUNTER
    data = request.get_json(silent=True)
    if not data or not data.get("user_id") or not data.get("product"):
        return jsonify({"error": "user_id and product are required"}), 400

    ORDER_COUNTER += 1
    new_id = str(ORDER_COUNTER)
    new_order = {
        "id": new_id,
        "user_id": data["user_id"],
        "product": data["product"],
        "quantity": data.get("quantity", 1),
        "price": data.get("price", 0.0),
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    ORDERS[new_id] = new_order
    logger.info("order_created id=%s user_id=%s product=%s", new_id, data["user_id"], data["product"])
    return jsonify(new_order), 201


@app.route("/api/orders/<order_id>/status", methods=["PATCH"])
def update_order_status(order_id):
    """Update the status of an order."""
    order = ORDERS.get(order_id)
    if not order:
        return jsonify({"error": "Order not found", "order_id": order_id}), 404

    data = request.get_json(silent=True)
    valid_statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
    if not data or data.get("status") not in valid_statuses:
        return jsonify({"error": f"status must be one of {valid_statuses}"}), 400

    order["status"] = data["status"]
    logger.info("order_status_updated id=%s status=%s", order_id, data["status"])
    return jsonify(order), 200


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5002))
    logger.info("Starting %s on port %s (version %s)", SERVICE_NAME, port, APP_VERSION)
    app.run(host="0.0.0.0", port=port)
