from flask import Blueprint, jsonify
from services import TaskService

bp = Blueprint("migrate", __name__, url_prefix="/api")


@bp.post("/migrate")
def migrate_from_json():
    migration_result, error = TaskService.migrate_data_from_json()
    if error:
        return jsonify({"error": error}), 404
    return jsonify(migration_result)
