# SQLite database setup
#!/usr/bin/env python3
"""
Database setup and connection management for Habit Tracker
SQLite database with proper schema for habits, tasks, and completions
"""

import sqlite3
import os
from datetime import datetime

# Store the database file alongside this module to avoid duplicate DBs created
# from varying working directories
DATABASE_FILE = os.path.join(os.path.dirname(__file__), "habit_tracker.db")


def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    return conn


def init_db():
    """Initialize database with required tables"""
    conn = get_db_connection()

    try:
        # Create habits table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                streak INTEGER DEFAULT 0,
                last_done DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Add new columns for reminders to habits table
        try:
            conn.execute("ALTER TABLE habits ADD COLUMN reminder_time TEXT;")
        except sqlite3.OperationalError as e:
            print(f"Skipping habit reminder column creation: {e}")

        # Add archive flag to habits table
        try:
            conn.execute("ALTER TABLE habits ADD COLUMN is_archived BOOLEAN DEFAULT 0;")
        except sqlite3.OperationalError as e:
            print(f"Skipping habit is_archived column creation: {e}")

        # Create tasks table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                done BOOLEAN DEFAULT FALSE,
                date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Add new columns for reminders to tasks table
        try:
            conn.execute("ALTER TABLE tasks ADD COLUMN reminder_time TEXT;")
        except sqlite3.OperationalError as e:
            print(f"Skipping task reminder column creation: {e}")

        # Create habit completions tracking table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS habit_completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (habit_id) REFERENCES habits (id),
                UNIQUE(habit_id, date)
            )
        """
        )

        # Create indexes for better performance
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_habits_name ON habits(name)
        """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tasks_date ON tasks(date)
        """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_habit_completions_habit_date 
            ON habit_completions(habit_id, date)
        """
        )

        conn.commit()
        print("Database initialized successfully")

    except Exception as e:
        print(f"Database initialization error: {e}")
        conn.rollback()

    finally:
        conn.close()


def reset_db():
    """Reset database (for development/testing)"""
    if os.path.exists(DATABASE_FILE):
        os.remove(DATABASE_FILE)
        print("Database reset")
    init_db()


def get_database_stats():
    """Get database statistics"""
    conn = get_db_connection()

    try:
        stats = {}

        # Count records
        stats["habits_count"] = conn.execute("SELECT COUNT(*) FROM habits").fetchone()[
            0
        ]
        stats["tasks_count"] = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        stats["completions_count"] = conn.execute(
            "SELECT COUNT(*) FROM habit_completions"
        ).fetchone()[0]

        # Get date ranges
        first_habit = conn.execute("SELECT MIN(created_at) FROM habits").fetchone()[0]
        first_task = conn.execute("SELECT MIN(created_at) FROM tasks").fetchone()[0]

        stats["first_habit_date"] = first_habit
        stats["first_task_date"] = first_task

        return stats

    except Exception as e:
        print(f"❌ Error getting database stats: {e}")
        return {}

    finally:
        conn.close()


def backup_database(backup_path=None):
    """Create database backup"""
    if not backup_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"habit_tracker_backup_{timestamp}.db"

    try:
        import shutil

        shutil.copy2(DATABASE_FILE, backup_path)
        print(f"Database backed up to {backup_path}")
        return backup_path
    except Exception as e:
        print(f"Backup failed: {e}")
        return None


def restore_database(backup_path):
    """Restore database from backup"""
    try:
        import shutil

        if os.path.exists(backup_path):
            shutil.copy2(backup_path, DATABASE_FILE)
            print(f"Database restored from {backup_path}")
            return True
        else:
            print(f"Backup file not found: {backup_path}")
            return False
    except Exception as e:
        print(f"Restore failed: {e}")
        return False


def migrate_from_json(json_file_path="data.json"):
    """Migrate data from CLI version's JSON file"""
    import json

    if not os.path.exists(json_file_path):
        print(f"JSON file not found: {json_file_path}")
        return False

    try:
        with open(json_file_path, "r") as f:
            data = json.load(f)

        conn = get_db_connection()
        migrated_habits = 0
        migrated_tasks = 0

        # Migrate habits
        for habit_data in data.get("habits", []):
            try:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO habits (name, streak, last_done, created_at)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        habit_data["name"],
                        habit_data.get("streak", 0),
                        habit_data.get("last_done"),
                        datetime.now().isoformat(),
                    ),
                )

                # If habit has completions, create completion records
                if habit_data.get("last_done"):
                    habit_id = conn.execute(
                        "SELECT id FROM habits WHERE name = ?", (habit_data["name"],)
                    ).fetchone()

                    if habit_id:
                        conn.execute(
                            """
                            INSERT OR IGNORE INTO habit_completions (habit_id, date, created_at)
                            VALUES (?, ?, ?)
                        """,
                            (
                                habit_id[0],
                                habit_data["last_done"],
                                datetime.now().isoformat(),
                            ),
                        )

                migrated_habits += 1

            except Exception as e:
                print(
                    f"Warning: Error migrating habit '{habit_data.get('name', 'unknown')}': {e}"
                )

        # Migrate tasks
        for task_data in data.get("tasks", []):
            try:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO tasks (name, done, date, created_at)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        task_data["name"],
                        1 if task_data.get("done", False) else 0,
                        task_data.get("date", datetime.now().strftime("%Y-%m-%d")),
                        datetime.now().isoformat(),
                    ),
                )
                migrated_tasks += 1

            except Exception as e:
                print(
                    f"Warning: Error migrating task '{task_data.get('name', 'unknown')}': {e}"
                )

        conn.commit()
        conn.close()

        print(f"Migration completed:")
        print(f"   📊 Habits migrated: {migrated_habits}")
        print(f"   📋 Tasks migrated: {migrated_tasks}")

        return True

    except Exception as e:
        print(f"Migration failed: {e}")
        return False


def create_sample_data():
    """Create sample data for development/testing"""
    conn = get_db_connection()
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        # Sample habits
        sample_habits = [
            ("Drink Water", 5, today),
            ("Morning Exercise", 12, today),
            ("Read for 30 minutes", 0, None),
            ("Meditate", 3, today),
        ]

        for name, streak, last_done in sample_habits:
            conn.execute(
                """
                INSERT OR IGNORE INTO habits (name, streak, last_done)
                VALUES (?, ?, ?)
            """,
                (name, streak, last_done),
            )

        # Sample tasks for today
        sample_tasks = [
            ("Review project proposal", False),
            ("Call dentist for appointment", True),
            ("Buy groceries", False),
            ("Prepare presentation slides", True),
            ("Update resume", False),
        ]

        for name, done in sample_tasks:
            conn.execute(
                """
                INSERT OR IGNORE INTO tasks (name, done, date)
                VALUES (?, ?, ?)
            """,
                (name, done, today),
            )

        conn.commit()
        print("Sample data created")

    except Exception as e:
        print(f"Error creating sample data: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    # Initialize database when run directly
    print("Initializing Habit Tracker Database...")
    init_db()

    # Optionally create sample data for development
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--sample":
        create_sample_data()

    # Show database stats
    stats = get_database_stats()
    print(f"\nDatabase Stats:")
    print(f"   Habits: {stats.get('habits_count', 0)}")
    print(f"   Tasks: {stats.get('tasks_count', 0)}")
    print(f"   Completions: {stats.get('completions_count', 0)}")

    print(f"\nDatabase ready at: {DATABASE_FILE}")
