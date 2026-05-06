import sqlite3
import datetime

DB_NAME = "tutor.db"

def init_db():
    """Initializes the database with the required tables."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        
        # 1. Students Table (The Profile)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Students (
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                join_date TEXT NOT NULL
            )
        ''')
        
        # 2. Streaks Table (Daily Activity Tracking)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Streaks (
                student_id INTEGER PRIMARY KEY,
                last_active_date TEXT,
                current_streak INTEGER DEFAULT 0,
                highest_streak INTEGER DEFAULT 0,
                FOREIGN KEY (student_id) REFERENCES Students(student_id)
            )
        ''')
        
        # 3. ConceptLogs Table (The "Memory" for Weak Topics)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ConceptLogs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                concept_name TEXT NOT NULL,
                status TEXT NOT NULL,  -- e.g., 'Mastered', 'Struggling'
                timestamp TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES Students(student_id)
            )
        ''')
        
        conn.commit()
    print("Database initialized successfully.")

# Run this once when the file is executed directly to create the file
if __name__ == "__main__":
    init_db()