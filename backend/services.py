from database import get_db_connection
from datetime import datetime, timedelta
import os
import json

class HabitService:
    @staticmethod
    def get_all_habits_with_status():
        conn = get_db_connection()
        habits = conn.execute("""
            SELECT * FROM habits
            WHERE COALESCE(is_archived, 0) = 0
            ORDER BY created_at DESC
        """).fetchall()
        
        today = datetime.now().strftime('%Y-%m-%d')
        result = []
        
        for habit in habits:
            done_today = conn.execute("""
                SELECT COUNT(*) FROM habit_completions 
                WHERE habit_id = ? AND date = ?
            """, (habit['id'], today)).fetchone()[0] > 0
            
            result.append({
                'id': habit['id'],
                'name': habit['name'],
                'streak': habit['streak'],
                'last_done': habit['last_done'],
                'done_today': done_today,
                'created_at': habit['created_at'],
                'reminder_time': habit['reminder_time'] if 'reminder_time' in habit.keys() else None
            })
        
        conn.close()
        return result

    @staticmethod
    def add_new_habit(habit_name, reminder_time=None):
        conn = get_db_connection()
        
        existing = conn.execute("""
            SELECT id FROM habits WHERE LOWER(name) = LOWER(?)
        """, (habit_name,)).fetchone()
        
        if existing:
            conn.close()
            return None, "Habit already exists"
        
        if reminder_time:
            cursor = conn.execute("""
                INSERT INTO habits (name, streak, last_done, created_at, reminder_time)
                VALUES (?, 0, NULL, ?, ?)
            """, (habit_name, datetime.now().isoformat(), reminder_time))
        else:
            cursor = conn.execute("""
                INSERT INTO habits (name, streak, last_done, created_at)
                VALUES (?, 0, NULL, ?)
            """, (habit_name, datetime.now().isoformat()))
        
        habit_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            'id': habit_id,
            'name': habit_name,
            'streak': 0,
            'last_done': None,
            'done_today': False,
            'reminder_time': reminder_time,
        }, None
    
    @staticmethod
    def complete_habit_for_today(habit_id):
        conn = get_db_connection()
        today = datetime.now().strftime('%Y-%m-%d')
        
        habit = conn.execute("""
            SELECT * FROM habits WHERE id = ?
        """, (habit_id,)).fetchone()
        
        if not habit:
            conn.close()
            return None, "Habit not found"
        
        existing = conn.execute("""
            SELECT id FROM habit_completions WHERE habit_id = ? AND date = ?
        """, (habit_id, today)).fetchone()
        
        if existing:
            conn.close()
            return None, "Habit already completed today"
        
        new_streak = 1
        if habit['last_done'] is not None:
            last_done = datetime.strptime(habit['last_done'], '%Y-%m-%d')
            today_date = datetime.strptime(today, '%Y-%m-%d')
            days_diff = (today_date - last_done).days
            
            if days_diff == 1:
                new_streak = habit['streak'] + 1
            else:
                new_streak = 1
        
        conn.execute("""
            INSERT INTO habit_completions (habit_id, date, created_at)
            VALUES (?, ?, ?)
        """, (habit_id, today, datetime.now().isoformat()))
        
        conn.execute("""
            UPDATE habits SET streak = ?, last_done = ? WHERE id = ?
        """, (new_streak, today, habit_id))
        
        conn.commit()
        conn.close()
        
        return {'success': True, 'new_streak': new_streak}, None

    @staticmethod
    def uncomplete_habit_for_today(habit_id):
        """Undo today's completion for a habit and recompute streak/last_done"""
        conn = get_db_connection()
        today = datetime.now().strftime('%Y-%m-%d')

        habit = conn.execute("""
            SELECT * FROM habits WHERE id = ?
        """, (habit_id,)).fetchone()
        if not habit:
            conn.close()
            return None, "Habit not found"

        existing = conn.execute("""
            SELECT id FROM habit_completions WHERE habit_id = ? AND date = ?
        """, (habit_id, today)).fetchone()
        if not existing:
            conn.close()
            return None, "Habit not completed today"

        try:
            # Remove today's completion
            conn.execute("DELETE FROM habit_completions WHERE habit_id = ? AND date = ?", (habit_id, today))

            # Recompute streak ending at latest completion date (if any)
            dates = conn.execute(
                "SELECT date FROM habit_completions WHERE habit_id = ? ORDER BY date DESC",
                (habit_id,)
            ).fetchall()

            if not dates:
                new_streak = 0
                last_done = None
            else:
                # Compute consecutive streak ending at the most recent completion date
                def to_date(s):
                    return datetime.strptime(s, '%Y-%m-%d').date()
                last_done_date = to_date(dates[0]['date'])
                new_streak = 1
                expected = last_done_date - timedelta(days=1)
                for row in dates[1:]:
                    d = to_date(row['date'])
                    if d == expected:
                        new_streak += 1
                        expected = expected - timedelta(days=1)
                    else:
                        break
                last_done = last_done_date.strftime('%Y-%m-%d')

            conn.execute("UPDATE habits SET streak = ?, last_done = ? WHERE id = ?", (new_streak, last_done, habit_id))
            conn.commit()
            return { 'success': True, 'new_streak': new_streak }, None
        except Exception:
            conn.rollback()
            return None, "Failed to uncomplete habit"
        finally:
            conn.close()

    @staticmethod
    def update_habit(habit_id, name=None, reminder_time=None):
        """Update habit fields (name, reminder_time). Returns updated fields."""
        conn = get_db_connection()
        try:
            habit = conn.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
            if not habit:
                return None, "Habit not found"

            updates = []
            params = []

            if name is not None:
                new_name = name.strip()
                if not new_name:
                    return None, "Habit name cannot be empty"
                # Check duplicate name
                dup = conn.execute("SELECT id FROM habits WHERE LOWER(name) = LOWER(?) AND id != ?", (new_name, habit_id)).fetchone()
                if dup:
                    return None, "Habit with this name already exists"
                updates.append("name = ?")
                params.append(new_name)

            if reminder_time is not None:
                updates.append("reminder_time = ?")
                params.append(reminder_time if reminder_time else None)

            if not updates:
                return None, "No fields to update"

            params.append(habit_id)
            sql = f"UPDATE habits SET {', '.join(updates)} WHERE id = ?"
            conn.execute(sql, tuple(params))
            conn.commit()

            updated = conn.execute("SELECT id, name, streak, last_done, created_at, reminder_time FROM habits WHERE id = ?", (habit_id,)).fetchone()
            return {
                'id': updated['id'],
                'name': updated['name'],
                'streak': updated['streak'],
                'last_done': updated['last_done'],
                'created_at': updated['created_at'],
                'reminder_time': updated['reminder_time'],
            }, None
        except Exception:
            conn.rollback()
            return None, "Failed to update habit"
        finally:
            conn.close()

    @staticmethod
    def archive_habit(habit_id):
        conn = get_db_connection()
        try:
            cursor = conn.execute("UPDATE habits SET is_archived = 1 WHERE id = ?", (habit_id,))
            if cursor.rowcount == 0:
                conn.rollback()
                return None, "Habit not found"
            conn.commit()
            return { 'success': True }, None
        except Exception:
            conn.rollback()
            return None, "Failed to archive habit"
        finally:
            conn.close()

    @staticmethod
    def get_archived_habits():
        conn = get_db_connection()
        habits = conn.execute(
            """
            SELECT * FROM habits
            WHERE COALESCE(is_archived, 0) = 1
            ORDER BY created_at DESC
            """
        ).fetchall()
        today = datetime.now().strftime('%Y-%m-%d')
        result = []
        for habit in habits:
            done_today = conn.execute(
                """
                SELECT COUNT(*) FROM habit_completions
                WHERE habit_id = ? AND date = ?
                """,
                (habit['id'], today),
            ).fetchone()[0] > 0
            result.append({
                'id': habit['id'],
                'name': habit['name'],
                'streak': habit['streak'],
                'last_done': habit['last_done'],
                'done_today': done_today,
                'created_at': habit['created_at'],
                'reminder_time': habit['reminder_time'] if 'reminder_time' in habit.keys() else None
            })
        conn.close()
        return result

    @staticmethod
    def unarchive_habit(habit_id):
        conn = get_db_connection()
        try:
            cursor = conn.execute("UPDATE habits SET is_archived = 0 WHERE id = ?", (habit_id,))
            if cursor.rowcount == 0:
                conn.rollback()
                return None, "Habit not found"
            conn.commit()
            return { 'success': True }, None
        except Exception:
            conn.rollback()
            return None, "Failed to unarchive habit"
        finally:
            conn.close()

class TaskService:
    @staticmethod
    def get_tasks_for_today():
        today = datetime.now().strftime('%Y-%m-%d')
        conn = get_db_connection()
        
        tasks = conn.execute("""
            SELECT * FROM tasks WHERE date = ? ORDER BY created_at DESC
        """, (today,)).fetchall()
        
        result = []
        for task in tasks:
            result.append({
                'id': task['id'],
                'name': task['name'],
                'done': bool(task['done']),
                'date': task['date'],
                'created_at': task['created_at'],
                'reminder_time': task['reminder_time'] if 'reminder_time' in task.keys() else None
            })
        
        conn.close()
        return result

    @staticmethod
    def add_new_task(task_name, reminder_time=None):
        today = datetime.now().strftime('%Y-%m-%d')
        conn = get_db_connection()
        
        if reminder_time:
            cursor = conn.execute("""
                INSERT INTO tasks (name, done, date, created_at, reminder_time)
                VALUES (?, 0, ?, ?, ?)
            """, (task_name, today, datetime.now().isoformat(), reminder_time))
        else:
            cursor = conn.execute("""
                INSERT INTO tasks (name, done, date, created_at)
                VALUES (?, 0, ?, ?)
            """, (task_name, today, datetime.now().isoformat()))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            'id': task_id,
            'name': task_name,
            'done': False,
            'date': today,
            'reminder_time': reminder_time,
        }, None

    @staticmethod
    def complete_task_by_id(task_id):
        conn = get_db_connection()
        
        cursor = conn.execute("""
            UPDATE tasks SET done = 1 WHERE id = ?
        """, (task_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return False, "Task not found"
        
        conn.commit()
        conn.close()
        
        return True, None

    @staticmethod
    def uncomplete_task_by_id(task_id):
        conn = get_db_connection()
        
        cursor = conn.execute("""
            UPDATE tasks SET done = 0 WHERE id = ?
        """, (task_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return False, "Task not found"
        
        conn.commit()
        conn.close()
        
        return True, None

    @staticmethod
    def get_dashboard_stats():
        conn = get_db_connection()
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Habit stats
        total_habits = conn.execute('SELECT COUNT(*) FROM habits').fetchone()[0]
        habits_done_today = conn.execute("""
            SELECT COUNT(*) FROM habit_completions WHERE date = ?
        """, (today,)).fetchone()[0]
        
        # Task stats
        total_tasks_today = conn.execute("""
            SELECT COUNT(*) FROM tasks WHERE date = ?
        """, (today,)).fetchone()[0]
        tasks_done_today = conn.execute("""
            SELECT COUNT(*) FROM tasks WHERE date = ? AND done = 1
        """, (today,)).fetchone()[0]
        
        # Streak stats
        best_streak = conn.execute("""
            SELECT MAX(streak) FROM habits
        """).fetchone()[0] or 0
        
        active_streaks = conn.execute("""
            SELECT COUNT(*) FROM habits WHERE streak > 0
        """).fetchone()[0]
        
        conn.close()
        
        return {
            'habits': {
                'total': total_habits,
                'done_today': habits_done_today,
                'completion_rate': round((habits_done_today / total_habits * 100) if total_habits > 0 else 0, 1)
            },
            'tasks': {
                'total_today': total_tasks_today,
                'done_today': tasks_done_today,
                'completion_rate': round((tasks_done_today / total_tasks_today * 100) if total_tasks_today > 0 else 0, 1)
            },
            'streaks': {
                'best_streak': best_streak,
                'active_streaks': active_streaks
            }
        }

    @staticmethod
    def migrate_data_from_json():
        if not os.path.exists('data.json'):
            return None, "data.json not found"
        
        with open('data.json', 'r') as f:
            data = json.load(f)
        
        conn = get_db_connection()
        migrated_habits = 0
        migrated_tasks = 0
        
        # Migrate habits
        for habit_data in data.get('habits', []):
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO habits (name, streak, last_done, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    habit_data['name'],
                    habit_data.get('streak', 0),
                    habit_data.get('last_done'),
                    datetime.now().isoformat()
                ))
                migrated_habits += 1
            except:
                pass
        
        # Migrate tasks
        for task_data in data.get('tasks', []):
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO tasks (name, done, date, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    task_data['name'],
                    1 if task_data.get('done', False) else 0,
                    task_data.get('date', datetime.now().strftime('%Y-%m-%d')),
                    datetime.now().isoformat()
                ))
                migrated_tasks += 1
            except:
                pass
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'migrated_habits': migrated_habits,
            'migrated_tasks': migrated_tasks
        }, None

class StatsService:
    @staticmethod
    def get_daily_stats_for_ai():
        conn = get_db_connection()
        today = datetime.now().strftime("%Y-%m-%d")
        
        total_habits = conn.execute('SELECT COUNT(*) FROM habits').fetchone()[0]
        habits_done_today = conn.execute("""
            SELECT COUNT(*) FROM habit_completions WHERE date = ?
        """, (today,)).fetchone()[0]
        
        total_tasks_today = conn.execute("""
            SELECT COUNT(*) FROM tasks WHERE date = ?
        """, (today,)).fetchone()[0]
        tasks_done_today = conn.execute("""
            SELECT COUNT(*) FROM tasks WHERE date = ? AND done = 1
        """, (today,)).fetchone()[0]
        
        best_streak_result = conn.execute('SELECT MAX(streak) FROM habits').fetchone()
        best_streak = best_streak_result[0] if best_streak_result[0] else 0
        active_streaks = conn.execute('SELECT COUNT(*) FROM habits WHERE streak > 0').fetchone()[0]
        
        conn.close()
        
        return {
            "total_habits": total_habits,
            "habits_done_today": habits_done_today,
            "total_tasks_today": total_tasks_today,
            "tasks_done_today": tasks_done_today,
            "best_streak": best_streak,
            "active_streaks": active_streaks
        }

    @staticmethod
    def get_all_habits_for_insights():
        conn = get_db_connection()
        habits = conn.execute("""
            SELECT name, streak, last_done FROM habits ORDER BY streak DESC
        """).fetchall()
        conn.close()
        return habits

    @staticmethod
    def get_pending_tasks():
        conn = get_db_connection()
        today = datetime.now().strftime("%Y-%m-%d")
        pending_tasks = conn.execute("""
            SELECT name FROM tasks WHERE date = ? AND done = 0
        """, (today,)).fetchall()
        conn.close()
        return pending_tasks

    @staticmethod
    def get_existing_habit_names():
        conn = get_db_connection()
        existing_habits = conn.execute('SELECT name FROM habits').fetchall()
        conn.close()
        return [habit['name'] for habit in existing_habits]

    @staticmethod
    def get_weekly_summary_stats():
        conn = get_db_connection()
        
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        
        weekly_completions = conn.execute("""
            SELECT COUNT(*) FROM habit_completions 
            WHERE date >= ? AND date <= ?
        """, (week_ago, today)).fetchone()[0]
        
        weekly_tasks = conn.execute("""
            SELECT COUNT(*) FROM tasks 
            WHERE date >= ? AND date <= ? AND done = 1
        """, (week_ago, today)).fetchone()[0]
        
        active_streaks = conn.execute('SELECT COUNT(*) FROM habits WHERE streak > 0').fetchone()[0]
        
        conn.close()
        
        return {
            "weekly_completions": weekly_completions,
            "weekly_tasks": weekly_tasks,
            "active_streaks": active_streaks
        }
