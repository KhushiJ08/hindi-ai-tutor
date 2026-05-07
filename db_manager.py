import sqlite3
from datetime import date, datetime

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


def login_and_update_streak(student_name):
    """Logs the student in and calculates their current streak."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        today = date.today()
        today_str = today.isoformat() 

        cursor.execute("SELECT student_id FROM Students WHERE name = ?", (student_name,))
        student_row = cursor.fetchone()

        if not student_row:
            # --- NEW STUDENT ROUTINE ---
            cursor.execute("INSERT INTO Students (name, join_date) VALUES (?, ?)", (student_name, today_str))
            student_id = cursor.lastrowid
            
            cursor.execute('''
                INSERT INTO Streaks (student_id, last_active_date, current_streak, highest_streak) 
                VALUES (?, ?, 1, 1)
            ''', (student_id, today_str))
            conn.commit()
            return student_id, 1  

        else:
            # --- RETURNING STUDENT ROUTINE ---
            student_id = student_row[0]
            cursor.execute("SELECT last_active_date, current_streak, highest_streak FROM Streaks WHERE student_id = ?", (student_id,))
            streak_data = cursor.fetchone()
            
            last_active = date.fromisoformat(streak_data[0])
            current_streak = streak_data[1]
            highest_streak = streak_data[2]

            delta_days = (today - last_active).days

            if delta_days == 1:
                current_streak += 1
                highest_streak = max(current_streak, highest_streak)
            elif delta_days > 1:
                current_streak = 1

            cursor.execute('''
                UPDATE Streaks 
                SET last_active_date = ?, current_streak = ?, highest_streak = ?
                WHERE student_id = ?
            ''', (today_str, current_streak, highest_streak, student_id))
            
            conn.commit()
            return student_id, current_streak


def log_concept(student_id, concept_name, status):
    """Saves a record of the topic the student is learning."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO ConceptLogs (student_id, concept_name, status, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (student_id, concept_name, status, timestamp))
        
        conn.commit()


# Run this once when the file is executed directly to create the tables
if __name__ == "__main__":
    init_db()