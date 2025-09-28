# Habit & Task models
#!/usr/bin/env python3
"""
Data models and business logic for AI-Powered Habit Tracker
Handles Habit and Task operations with database abstraction
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import json

from database import get_db_connection


@dataclass
class Habit:
    """Habit data model"""

    id: Optional[int] = None
    name: str = ""
    streak: int = 0
    last_done: Optional[str] = None  # YYYY-MM-DD format
    created_at: Optional[str] = None
    reminder_time: Optional[str] = None  # HH:MM format

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "streak": self.streak,
            "last_done": self.last_done,
            "created_at": self.created_at,
            "done_today": self.is_done_today(),
        }

    def is_done_today(self) -> bool:
        """Check if habit is completed today"""
        if not self.last_done:
            return False

        today = datetime.now().strftime("%Y-%m-%d")
        return self.last_done == today

    def days_since_last_done(self) -> int:
        """Calculate days since last completion"""
        if not self.last_done:
            return float("inf")

        last_done_date = datetime.strptime(self.last_done, "%Y-%m-%d")
        today = datetime.now()
        return (today.date() - last_done_date.date()).days

    def is_streak_active(self) -> bool:
        """Check if streak is currently active (done today or yesterday)"""
        days_since = self.days_since_last_done()
        return days_since <= 1  # Today or yesterday

    @classmethod
    def from_db_row(cls, row):
        """Create Habit instance from database row"""
        reminder = None
        try:
            reminder = row["reminder_time"]
        except Exception:
            reminder = None

        return cls(
            id=row["id"],
            name=row["name"],
            streak=row["streak"],
            last_done=row["last_done"],
            created_at=row["created_at"],
            reminder_time=reminder,
        )


@dataclass
class Task:
    """Task data model"""

    id: Optional[int] = None
    name: str = ""
    done: bool = False
    date: str = ""  # YYYY-MM-DD format
    created_at: Optional[str] = None
    reminder_time: Optional[str] = None  # HH:MM format

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "done": self.done,
            "date": self.date,
            "created_at": self.created_at,
        }

    def is_today(self) -> bool:
        """Check if task is for today"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.date == today

    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        if self.done:
            return False

        task_date = datetime.strptime(self.date, "%Y-%m-%d")
        return task_date.date() < datetime.now().date()

    @classmethod
    def from_db_row(cls, row):
        """Create Task instance from database row"""
        reminder = None
        try:
            reminder = row["reminder_time"]
        except Exception:
            reminder = None

        return cls(
            id=row["id"],
            name=row["name"],
            done=bool(row["done"]),
            date=row["date"],
            created_at=row["created_at"],
            reminder_time=reminder,
        )


@dataclass
class HabitCompletion:
    """Habit completion record"""

    id: Optional[int] = None
    habit_id: int = 0
    date: str = ""  # YYYY-MM-DD format
    created_at: Optional[str] = None

    @classmethod
    def from_db_row(cls, row):
        """Create HabitCompletion instance from database row"""
        return cls(
            id=row["id"],
            habit_id=row["habit_id"],
            date=row["date"],
            created_at=row["created_at"],
        )


class HabitManager:
    """Business logic for habit operations"""

    @staticmethod
    def get_all_habits() -> List[Habit]:
        """Get all habits with today's completion status"""
        conn = get_db_connection()
        try:
            rows = conn.execute(
                """
                SELECT * FROM habits ORDER BY created_at DESC
            """
            ).fetchall()

            return [Habit.from_db_row(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def get_habit_by_id(habit_id: int) -> Optional[Habit]:
        """Get habit by ID"""
        conn = get_db_connection()
        try:
            row = conn.execute(
                """
                SELECT * FROM habits WHERE id = ?
            """,
                (habit_id,),
            ).fetchone()

            return Habit.from_db_row(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def create_habit(name: str) -> Tuple[bool, str, Optional[Habit]]:
        """Create a new habit"""
        name = name.strip()
        if not name:
            return False, "Habit name is required", None

        conn = get_db_connection()
        try:
            # Check if habit already exists
            existing = conn.execute(
                """
                SELECT id FROM habits WHERE LOWER(name) = LOWER(?)
            """,
                (name,),
            ).fetchone()

            if existing:
                return False, "Habit already exists", None

            # Create new habit
            cursor = conn.execute(
                """
                INSERT INTO habits (name, streak, last_done, created_at)
                VALUES (?, 0, NULL, ?)
            """,
                (name, datetime.now().isoformat()),
            )

            habit_id = cursor.lastrowid
            conn.commit()

            # Return the created habit
            habit = Habit(
                id=habit_id,
                name=name,
                streak=0,
                last_done=None,
                created_at=datetime.now().isoformat(),
            )

            return True, "Habit created successfully", habit

        except Exception as e:
            conn.rollback()
            return False, str(e), None
        finally:
            conn.close()

    @staticmethod
    def complete_habit(habit_id: int) -> Tuple[bool, str, Optional[Dict]]:
        """Mark habit as completed for today"""
        conn = get_db_connection()
        today = datetime.now().strftime("%Y-%m-%d")

        try:
            # Get habit
            habit_row = conn.execute(
                """
                SELECT * FROM habits WHERE id = ?
            """,
                (habit_id,),
            ).fetchone()

            if not habit_row:
                return False, "Habit not found", None

            habit = Habit.from_db_row(habit_row)

            # Check if already completed today
            existing = conn.execute(
                """
                SELECT id FROM habit_completions WHERE habit_id = ? AND date = ?
            """,
                (habit_id, today),
            ).fetchone()

            if existing:
                return False, "Habit already completed today", None

            # Calculate new streak
            new_streak = HabitManager._calculate_new_streak(habit, today)

            # Record completion
            conn.execute(
                """
                INSERT INTO habit_completions (habit_id, date, created_at)
                VALUES (?, ?, ?)
            """,
                (habit_id, today, datetime.now().isoformat()),
            )

            # Update habit
            conn.execute(
                """
                UPDATE habits SET streak = ?, last_done = ? WHERE id = ?
            """,
                (new_streak, today, habit_id),
            )

            conn.commit()

            return (
                True,
                "Habit completed!",
                {"new_streak": new_streak, "completion_date": today},
            )

        except Exception as e:
            conn.rollback()
            return False, str(e), None
        finally:
            conn.close()

    @staticmethod
    def _calculate_new_streak(habit: Habit, completion_date: str) -> int:
        """Calculate new streak based on last completion"""
        if not habit.last_done:
            return 1

        last_done = datetime.strptime(habit.last_done, "%Y-%m-%d")
        completion = datetime.strptime(completion_date, "%Y-%m-%d")
        days_diff = (completion.date() - last_done.date()).days

        if days_diff == 1:
            # Consecutive day - continue streak
            return habit.streak + 1
        else:
            # Gap in streak - start over
            return 1

    @staticmethod
    def delete_habit(habit_id: int) -> Tuple[bool, str]:
        """Delete a habit and all its completions"""
        conn = get_db_connection()
        try:
            # Check if habit exists
            habit = conn.execute(
                """
                SELECT id FROM habits WHERE id = ?
            """,
                (habit_id,),
            ).fetchone()

            if not habit:
                return False, "Habit not found"

            # Delete completions first (foreign key constraint)
            conn.execute(
                """
                DELETE FROM habit_completions WHERE habit_id = ?
            """,
                (habit_id,),
            )

            # Delete habit
            conn.execute(
                """
                DELETE FROM habits WHERE id = ?
            """,
                (habit_id,),
            )

            conn.commit()
            return True, "Habit deleted successfully"

        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def get_habit_statistics() -> Dict:
        """Get comprehensive habit statistics"""
        conn = get_db_connection()
        try:
            today = datetime.now().strftime("%Y-%m-%d")

            stats = {
                "total_habits": 0,
                "habits_done_today": 0,
                "completion_rate_today": 0,
                "total_active_streaks": 0,
                "longest_streak": 0,
                "habits_by_streak": {
                    "excellent": 0,  # 7+ days
                    "good": 0,  # 3-6 days
                    "starting": 0,  # 1-2 days
                    "inactive": 0,  # 0 days
                },
            }

            # Basic counts
            stats["total_habits"] = conn.execute(
                """
                SELECT COUNT(*) FROM habits
            """
            ).fetchone()[0]

            stats["habits_done_today"] = conn.execute(
                """
                SELECT COUNT(*) FROM habit_completions WHERE date = ?
            """,
                (today,),
            ).fetchone()[0]

            # Completion rate
            if stats["total_habits"] > 0:
                stats["completion_rate_today"] = round(
                    (stats["habits_done_today"] / stats["total_habits"]) * 100, 1
                )

            # Streak statistics
            streak_data = conn.execute(
                """
                SELECT streak FROM habits
            """
            ).fetchall()

            for row in streak_data:
                streak = row[0]
                if streak >= 7:
                    stats["habits_by_streak"]["excellent"] += 1
                elif streak >= 3:
                    stats["habits_by_streak"]["good"] += 1
                elif streak >= 1:
                    stats["habits_by_streak"]["starting"] += 1
                else:
                    stats["habits_by_streak"]["inactive"] += 1

                if streak > 0:
                    stats["total_active_streaks"] += 1

                if streak > stats["longest_streak"]:
                    stats["longest_streak"] = streak

            return stats

        finally:
            conn.close()


class TaskManager:
    """Business logic for task operations"""

    @staticmethod
    def get_tasks_for_date(date: str = None) -> List[Task]:
        """Get tasks for specific date (defaults to today)"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        conn = get_db_connection()
        try:
            rows = conn.execute(
                """
                SELECT * FROM tasks WHERE date = ? ORDER BY created_at DESC
            """,
                (date,),
            ).fetchall()

            return [Task.from_db_row(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def get_task_by_id(task_id: int) -> Optional[Task]:
        """Get task by ID"""
        conn = get_db_connection()
        try:
            row = conn.execute(
                """
                SELECT * FROM tasks WHERE id = ?
            """,
                (task_id,),
            ).fetchone()

            return Task.from_db_row(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def create_task(name: str, date: str = None) -> Tuple[bool, str, Optional[Task]]:
        """Create a new task"""
        name = name.strip()
        if not name:
            return False, "Task name is required", None

        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        conn = get_db_connection()
        try:
            cursor = conn.execute(
                """
                INSERT INTO tasks (name, done, date, created_at)
                VALUES (?, 0, ?, ?)
            """,
                (name, date, datetime.now().isoformat()),
            )

            task_id = cursor.lastrowid
            conn.commit()

            task = Task(
                id=task_id,
                name=name,
                done=False,
                date=date,
                created_at=datetime.now().isoformat(),
            )

            return True, "Task created successfully", task

        except Exception as e:
            conn.rollback()
            return False, str(e), None
        finally:
            conn.close()

    @staticmethod
    def toggle_task_completion(task_id: int) -> Tuple[bool, str, Optional[bool]]:
        """Toggle task completion status"""
        conn = get_db_connection()
        try:
            # Get current status
            row = conn.execute(
                """
                SELECT done FROM tasks WHERE id = ?
            """,
                (task_id,),
            ).fetchone()

            if not row:
                return False, "Task not found", None

            current_status = bool(row[0])
            new_status = not current_status

            # Update status
            conn.execute(
                """
                UPDATE tasks SET done = ? WHERE id = ?
            """,
                (new_status, task_id),
            )

            conn.commit()

            status_text = "completed" if new_status else "marked as pending"
            return True, f"Task {status_text}", new_status

        except Exception as e:
            conn.rollback()
            return False, str(e), None
        finally:
            conn.close()

    @staticmethod
    def delete_task(task_id: int) -> Tuple[bool, str]:
        """Delete a task"""
        conn = get_db_connection()
        try:
            cursor = conn.execute(
                """
                DELETE FROM tasks WHERE id = ?
            """,
                (task_id,),
            )

            if cursor.rowcount == 0:
                return False, "Task not found"

            conn.commit()
            return True, "Task deleted successfully"

        except Exception as e:
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def get_task_statistics(date: str = None) -> Dict:
        """Get task statistics for specific date"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        conn = get_db_connection()
        try:
            stats = {
                "date": date,
                "total_tasks": 0,
                "completed_tasks": 0,
                "pending_tasks": 0,
                "completion_rate": 0,
            }

            # Get counts
            stats["total_tasks"] = conn.execute(
                """
                SELECT COUNT(*) FROM tasks WHERE date = ?
            """,
                (date,),
            ).fetchone()[0]

            stats["completed_tasks"] = conn.execute(
                """
                SELECT COUNT(*) FROM tasks WHERE date = ? AND done = 1
            """,
                (date,),
            ).fetchone()[0]

            stats["pending_tasks"] = stats["total_tasks"] - stats["completed_tasks"]

            # Calculate completion rate
            if stats["total_tasks"] > 0:
                stats["completion_rate"] = round(
                    (stats["completed_tasks"] / stats["total_tasks"]) * 100, 1
                )

            return stats

        finally:
            conn.close()


class DataExporter:
    """Export data to various formats"""

    @staticmethod
    def export_to_json(include_completions: bool = True) -> str:
        """Export all data to JSON format"""
        data = {
            "export_date": datetime.now().isoformat(),
            "habits": [],
            "tasks": [],
        }

        # Export habits
        habits = HabitManager.get_all_habits()
        data["habits"] = [habit.to_dict() for habit in habits]

        # Export tasks (last 30 days)
        start_date = datetime.now() - timedelta(days=30)
        conn = get_db_connection()

        try:
            rows = conn.execute(
                """
                SELECT * FROM tasks WHERE date >= ? ORDER BY date DESC, created_at DESC
            """,
                (start_date.strftime("%Y-%m-%d"),),
            ).fetchall()

            data["tasks"] = [Task.from_db_row(row).to_dict() for row in rows]

            # Include completion history if requested
            if include_completions:
                completion_rows = conn.execute(
                    """
                    SELECT * FROM habit_completions 
                    WHERE date >= ? 
                    ORDER BY date DESC
                """,
                    (start_date.strftime("%Y-%m-%d"),),
                ).fetchall()

                data["habit_completions"] = [
                    HabitCompletion.from_db_row(row).__dict__ for row in completion_rows
                ]

        finally:
            conn.close()

        return json.dumps(data, indent=2, ensure_ascii=False)

    @staticmethod
    def export_habits_csv() -> str:
        """Export habits to CSV format"""
        habits = HabitManager.get_all_habits()

        csv_lines = ["Name,Streak,Last Done,Created At,Status"]

        for habit in habits:
            status = "Active" if habit.is_streak_active() else "Inactive"
            csv_lines.append(
                f'"{habit.name}",{habit.streak},"{habit.last_done or "Never"}","{habit.created_at}",{status}'
            )

        return "\n".join(csv_lines)
