import os
import sqlite3

# Base directory where the database should be located
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "tasks.db")

def initialize_database():
    # Connect to the database and create tables if they don't exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create "tasks" table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """)

    # Create "time_logs" table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_logs (
            id INTEGER PRIMARY KEY,
            task_id INTEGER,
            start_time TEXT,
            end_time TEXT,
            duration TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks (id)
        )
    """)

    conn.commit()
    conn.close()

    print(f"Database initialized at: {db_path}")

if __name__ == "__main__":
    initialize_database()
