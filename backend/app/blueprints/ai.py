from flask import Blueprint, request, jsonify, current_app

bp = Blueprint("ai", __name__, url_prefix="/api/ai")

# Optional AI functionality
try:
    from ai_service import (
        get_daily_greeting,
        get_habit_insights,
        get_task_prioritization,
        suggest_new_habit,
        get_motivational_message,
        get_weekly_summary,
    )
    AI_AVAILABLE = True
except Exception:
    AI_AVAILABLE = False


def _guard_ai():
    if not AI_AVAILABLE:
        return jsonify({"error": "AI features not available"}), 503
    return None


@bp.get("/greeting")
def ai_greeting():
    guard = _guard_ai()
    if guard:
        return guard
    return jsonify({"message": get_daily_greeting()})


@bp.get("/insights")
def ai_insights():
    guard = _guard_ai()
    if guard:
        return guard
    return jsonify({"message": get_habit_insights()})


@bp.get("/prioritize")
def ai_prioritize():
    guard = _guard_ai()
    if guard:
        return guard
    return jsonify({"message": get_task_prioritization()})


@bp.get("/suggest")
def ai_suggest():
    guard = _guard_ai()
    if guard:
        return guard
    return jsonify({"message": suggest_new_habit()})


@bp.post("/motivate")
def ai_motivate():
    guard = _guard_ai()
    if guard:
        return guard
    data = request.get_json(silent=True) or {}
    context = data.get("context", "general")
    return jsonify({"message": get_motivational_message(context)})


@bp.get("/weekly")
def ai_weekly_summary():
    guard = _guard_ai()
    if guard:
        return guard
    return jsonify({"message": get_weekly_summary()})
