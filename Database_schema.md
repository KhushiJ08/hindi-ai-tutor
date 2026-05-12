## Backend & Database Documentation (Part D)

This section covers the local SQLite database (`students.db`) and the structured LLM extraction engine. 

### 1. Database Schema
The app uses a local SQLite database to track student progress and streaks without requiring cloud storage. It consists of four tables:
* **`Students`**: Stores `student_id`, `name`, `password_hash`, and `join_date`.
* **`Streaks`**: Tracks the `last_active_date` and calculates the `current_streak`.
* **`ConceptLogs`**: The core memory engine. It logs every topic the student learns and their mastery status.
* **`QuizLogs`**: Tracks quiz attempts with question, answer, and correctness.

### 2. Available Backend Functions
The `db_manager.py` file exposes the following functions:

* `login_and_update_streak(student_name, password)`: Returns the `student_id` and their updated `current_streak`. Uses name + password to uniquely identify students.
* `log_concept(student_id, concept_name, status)`: Silently writes a new topic (e.g., "Fractions", "Struggling") to the database.
* `log_quiz_result(...)`: Logs a quiz attempt and updates mastery status based on the result.
* `get_student_progress(student_id)`: Returns a dictionary of status counts (Mastered/Learning/Struggling) for progress charts.