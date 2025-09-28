from flask import Blueprint, jsonify
from services import TaskService

bp = Blueprint("stats", __name__, url_prefix="/api")


@bp.get("/stats")
def get_stats():
    stats = TaskService.get_dashboard_stats()
    return jsonify(stats)
