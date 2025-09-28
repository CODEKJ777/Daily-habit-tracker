from flask import Blueprint, request, jsonify
from services import TaskService
from database import get_db_connection

bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")


@bp.get("")
def list_tasks_today():
    tasks = TaskService.get_tasks_for_today()
    return jsonify(tasks)


@bp.post("")
def create_task():
    data = request.get_json() or {}
    task_name = data.get("name", "").strip()
    reminder_time = data.get("reminder_time")

    if not task_name:
        return jsonify({"error": "Task name is required"}), 400

    new_task, error = TaskService.add_new_task(task_name, reminder_time)
    if error:
        return jsonify({"error": error}), 400

    return jsonify(new_task)


@bp.post("/<int:task_id>/complete")
def complete_task(task_id: int):
    success, error = TaskService.complete_task_by_id(task_id)
    if error:
        return jsonify({"error": error}), 404
    return jsonify({"success": True})


@bp.post("/<int:task_id>/uncomplete")
def uncomplete_task(task_id: int):
    success, error = TaskService.uncomplete_task_by_id(task_id)
    if error:
        return jsonify({"error": error}), 404
    return jsonify({"success": True})


@bp.delete("/<int:task_id>")
def delete_task(task_id: int):
    """Delete a task"""
    conn = get_db_connection()
    try:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({"error": "Task not found"}), 404
        conn.commit()
        return jsonify({"success": True})
    except Exception:
        conn.rollback()
        return jsonify({"error": "Failed to delete task"}), 500
    finally:
        conn.close()
