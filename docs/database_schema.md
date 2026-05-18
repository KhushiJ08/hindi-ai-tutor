## Backend & Database Documentation

This section covers the local SQLite database (`students.db`) and the structured LLM extraction engine.

### 1. Database Schema
The app uses a local SQLite database (WAL mode, foreign keys enforced) to track student progress, streaks, and conversation history without requiring cloud storage. It consists of six tables:

* **`Students`**: Stores `student_id`, `name`, `password_hash`, and `join_date`.
* **`Streaks`**: Tracks the `last_active_date` and calculates the `current_streak` and `highest_streak`.
* **`ConceptLogs`**: The core memory engine. It logs every topic the student learns, their mastery status, `next_review_date`, and `interval_days` for spaced repetition.
* **`QuizLogs`**: Tracks quiz attempts with `topic`, `quiz_type`, `question`, `student_answer`, `correct_answer`, and `is_correct`.
* **`Conversations`**: Persistent chat sessions per student, storing `title`, `created_at`, and `updated_at`.
* **`Messages`**: Individual messages within a conversation, storing `role` (user/assistant), `content`, and `created_at`.

### 2. Performance Indexes
The database includes optimized indexes for common query patterns:
* `idx_concept_student` — ConceptLogs by student + timestamp
* `idx_concept_name` — ConceptLogs by student + concept name + timestamp
* `idx_quiz_student_topic` — QuizLogs by student + topic + timestamp
* `idx_conversations_student` — Conversations by student + updated_at
* `idx_messages_convo` — Messages by conversation + created_at

### 3. Available Backend Functions
The `db_manager.py` file exposes the following functions:

**Auth & Streaks:**
* `login_and_update_streak(student_name, password)`: Returns the `student_id` and their updated `current_streak`. Uses name + password to uniquely identify students. Raises `ValueError` on wrong password.

**Concept & Quiz Tracking:**
* `log_concept(student_id, concept_name)`: Silently records that a topic was discussed in chat. Does NOT assign mastery status — only quiz results determine mastery.
* `log_quiz_result(...)`: Logs a quiz attempt and updates mastery status based on streak-based logic (2+ consecutive correct → Mastered, 2+ consecutive wrong → Struggling, otherwise → Learning).
* `get_student_progress(student_id)`: Returns a dictionary of status counts (Mastered/Learning/Struggling) based exclusively on quiz performance.
* `get_due_reviews(student_id)`: Returns concepts that are due for revision today or overdue.
* `get_calendar_data(student_id)`: Returns a sorted list of distinct dates the student was active (from both chat and quiz activity).

**Conversation Management:**
* `create_conversation(student_id, title)`: Creates a new conversation session and returns its ID.
* `get_conversations(student_id)`: Returns all conversations for a student, newest first.
* `get_messages(conversation_id)`: Returns all messages in a conversation, oldest first.
* `add_message(conversation_id, role, content)`: Saves a message and bumps the conversation's `updated_at` timestamp.
* `rename_conversation(conversation_id, title)`: Renames a conversation.
* `delete_conversation(conversation_id)`: Deletes a conversation and all its messages.