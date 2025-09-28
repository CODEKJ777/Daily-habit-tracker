from flask import Blueprint, request, jsonify
from services import HabitService
from database import get_db_connection

# Optional AI dependency handled at call sites
try:
    from ai_service import get_motivational_message
    AI_ENABLED = True
except Exception:
    AI_ENABLED = False
    def get_motivational_message(*args, **kwargs):
        return ""

bp = Blueprint("habits", __name__, url_prefix="/api/habits")


@bp.get("/archived")
def list_archived():
    habits = HabitService.get_archived_habits()
    return jsonify(habits)


@bp.get("")
def list_habits():
    habits = HabitService.get_all_habits_with_status()
    return jsonify(habits)


@bp.post("")
def create_habit():
    data = request.get_json() or {}
    habit_name = data.get("name", "").strip()
    reminder_time = data.get("reminder_time")

    if not habit_name:
        return jsonify({"error": "Habit name is required"}), 400

    new_habit, error = HabitService.add_new_habit(habit_name, reminder_time)
    if error:
        return jsonify({"error": error}), 400

    motivation = ""
    if AI_ENABLED:
        try:
            motivation = get_motivational_message("new_habit")
        except Exception:
            pass

    response_data = dict(new_habit)
    response_data["motivation"] = motivation
    return jsonify(response_data)


@bp.post("/<int:habit_id>/uncomplete")
def uncomplete_habit(habit_id: int):
    result, error = HabitService.uncomplete_habit_for_today(habit_id)
    if error:
        status_code = 404 if "not found" in error.lower() else 400
        return jsonify({"error": error}), status_code
    return jsonify(result)


@bp.post("/<int:habit_id>/complete")
def complete_habit(habit_id: int):
    result, error = HabitService.complete_habit_for_today(habit_id)
    if error:
        status_code = 404 if "not found" in error.lower() else 400
        return jsonify({"error": error}), status_code

    motivation = ""
    if AI_ENABLED:
        try:
            motivation = get_motivational_message("habit_completed")
        except Exception:
            pass

    response_data = dict(result)
    response_data["motivation"] = motivation
    return jsonify(response_data)


@bp.patch("/<int:habit_id>")
def update_habit(habit_id: int):
    data = request.get_json() or {}
    name = data.get('name')
    reminder_time = data.get('reminder_time') if 'reminder_time' in data else None
    updated, error = HabitService.update_habit(habit_id, name=name, reminder_time=reminder_time)
    if error:
        code = 400 if error.startswith('Habit name') or error.startswith('Habit with this') or error.startswith('No fields') else 404
        return jsonify({"error": error}), code
    return jsonify(updated)


@bp.post("/<int:habit_id>/unarchive")
def unarchive_habit(habit_id: int):
    result, error = HabitService.unarchive_habit(habit_id)
    if error:
        return jsonify({"error": error}), 404
    return jsonify(result)


@bp.post("/<int:habit_id>/archive")
def archive_habit(habit_id: int):
    result, error = HabitService.archive_habit(habit_id)
    if error:
        return jsonify({"error": error}), 404
    return jsonify(result)


@bp.delete("/<int:habit_id>")
def delete_habit(habit_id: int):
    """Delete a habit and its completion history"""
    conn = get_db_connection()
    try:
        # Remove dependent completions first
        conn.execute("DELETE FROM habit_completions WHERE habit_id = ?", (habit_id,))
        cursor = conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({"error": "Habit not found"}), 404
        conn.commit()
        return jsonify({"success": True})
    except Exception:
        conn.rollback()
        return jsonify({"error": "Failed to delete habit"}), 500
    finally:
        conn.close()
