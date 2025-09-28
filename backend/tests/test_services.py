import pytest

from database import reset_db
from services import HabitService, TaskService


@pytest.fixture(autouse=True)
def fresh_db():
    # Ensure a clean database for each test
    reset_db()
    yield


def test_add_complete_and_uncomplete_habit():
    new_habit, error = HabitService.add_new_habit("Drink Water")
    assert error is None
    assert new_habit["name"] == "Drink Water"
    assert new_habit["streak"] == 0

    result, error = HabitService.complete_habit_for_today(new_habit["id"])
    assert error is None
    assert result["success"] is True
    assert result["new_streak"] >= 1

    undo, error = HabitService.uncomplete_habit_for_today(new_habit["id"])
    assert error is None
    assert undo["success"] is True


def test_duplicate_habit_name_rejected():
    h1, e1 = HabitService.add_new_habit("Read Book")
    assert e1 is None

    h2, e2 = HabitService.add_new_habit("Read Book")
    assert h2 is None
    assert isinstance(e2, str)


def test_tasks_flow_complete_uncomplete():
    new_task, error = TaskService.add_new_task("Write Report")
    assert error is None
    assert new_task["name"] == "Write Report"
    assert new_task["done"] is False

    ok, error = TaskService.complete_task_by_id(new_task["id"])
    assert error is None and ok is True

    ok2, error = TaskService.uncomplete_task_by_id(new_task["id"])
    assert error is None and ok2 is True


def test_dashboard_stats_shape():
    # Seed some data
    HabitService.add_new_habit("Exercise")
    TaskService.add_new_task("Plan day")

    stats = TaskService.get_dashboard_stats()

    assert set(stats.keys()) == {"habits", "tasks", "streaks"}
    assert set(stats["habits"].keys()) == {"total", "done_today", "completion_rate"}
    assert set(stats["tasks"].keys()) == {"total_today", "done_today", "completion_rate"}
    assert set(stats["streaks"].keys()) == {"best_streak", "active_streaks"}
