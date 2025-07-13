import sqlite3
import bcrypt
import os
import datetime
import streamlit as st

# Database file path
DB_PATH = "user_database.db"

def initialize_db():
    """Initialize the SQLite database for user authentication"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create users table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        phone_number TEXT,
        notifications_enabled INTEGER DEFAULT 0,
        notify_progress INTEGER DEFAULT 0,
        notify_badges INTEGER DEFAULT 0,
        notify_reminders INTEGER DEFAULT 0,
        reminder_time TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT,
        tutorial_completed INTEGER DEFAULT 0
    )
    ''')
    
    # Create study_time table for tracking study hours
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS study_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        skill_id TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT,
        duration_minutes INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    # Create table for badges/titles based on study time
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_badges (
        user_id INTEGER NOT NULL,
        total_study_minutes INTEGER DEFAULT 0,
        current_badge TEXT DEFAULT 'Member',
        badge_updated_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id),
        PRIMARY KEY (user_id)
    )
    ''')
    
    # Create table for progress notes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS progress_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        skill_id TEXT NOT NULL,
        note_text TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    # Create table for user journal entries
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS journal_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        mood TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    # Create table for daily goals
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        goal_text TEXT NOT NULL,
        completed INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash the password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()

def verify_password(stored_hash, provided_password):
    """Verify the password against its hash"""
    return bcrypt.checkpw(provided_password.encode(), stored_hash.encode())

def user_exists(username, email=None):
    """Check if a user with the given username or email already exists"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if email:
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
    else:
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result is not None

def register_user(username, email, password):
    """Register a new user in the database"""
    if user_exists(username, email):
        return False, "Username or email already exists."
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        password_hash = hash_password(password)
        
        # Insert the new user
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, current_time)
        )
        
        # Get the user ID
        user_id = cursor.lastrowid
        
        # Initialize badge record for the user
        cursor.execute(
            "INSERT INTO user_badges (user_id, total_study_minutes, current_badge, badge_updated_at) VALUES (?, ?, ?, ?)",
            (user_id, 0, "Member", current_time)
        )
        
        conn.commit()
        conn.close()
        return True, "Registration successful."
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error during registration: {str(e)}"

def login_user(username, password):
    """Authenticate a user login"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get user record by username
    cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and verify_password(user[2], password):
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.user_id = user[0]  # Store user ID in session
        return True, "Login successful."
    
    return False, "Invalid username or password."

def get_user_id(username):
    """Get user ID from username"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

def get_user_data(username):
    """Get data for a specific user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # First try getting just the core user data
        cursor.execute(
            """
            SELECT id, username, email, created_at
            FROM users WHERE username = ?
            """, 
            (username,)
        )
        user = cursor.fetchone()
        
        if user:
            # Build the base user data dictionary
            user_data = {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "created_at": user[3],
                "phone_number": None,
                "notifications_enabled": False,
                "notify_progress": False,
                "notify_badges": False,
                "notify_reminders": False,
                "reminder_time": None,
                "tutorial_completed": False  # Default to False
            }
            
            # Check if the tutorial_completed column exists
            try:
                cursor.execute("SELECT tutorial_completed FROM users WHERE id = ?", (user[0],))
                tutorial_result = cursor.fetchone()
                if tutorial_result and tutorial_result[0] is not None:
                    user_data["tutorial_completed"] = bool(tutorial_result[0])
            except sqlite3.OperationalError:
                # Column doesn't exist, keep the default False value
                pass
                
            return user_data
    except Exception as e:
        print(f"Error in get_user_data: {e}")
    finally:
        conn.close()
    
    return None

def update_user_password(username, new_password):
    """Update a user's password"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(new_password)
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE username = ?",
            (password_hash, current_time, username)
        )
        
        if cursor.rowcount == 0:
            conn.close()
            return False, "User not found."
        
        conn.commit()
        conn.close()
        return True, "Password updated successfully."
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error updating password: {str(e)}"

# Badge definitions
BADGE_LEVELS = [
    {"title": "Member", "minutes": 0},
    {"title": "Entry", "minutes": 60},  # 1 hour
    {"title": "Beginner", "minutes": 300},  # 5 hours
    {"title": "Intermediate", "minutes": 900},  # 15 hours
    {"title": "Proficient", "minutes": 1800},  # 30 hours
    {"title": "Advanced", "minutes": 3600},  # 60 hours
    {"title": "Expert", "minutes": 7200},  # 120 hours
    {"title": "A+ Student", "minutes": 12000},  # 200 hours
    {"title": "Master", "minutes": 18000},  # 300 hours
    {"title": "Grand Master", "minutes": 24000},  # 400 hours
    {"title": "Study Machine", "minutes": 30000},  # 500 hours
    {"title": "Study Master", "minutes": 36000}  # 600 hours
]

def get_badge_for_minutes(total_minutes):
    """Determine the appropriate badge title based on study minutes"""
    badge = BADGE_LEVELS[0]["title"]  # Default to the lowest badge
    
    for level in reversed(BADGE_LEVELS):
        if total_minutes >= level["minutes"]:
            badge = level["title"]
            break
    
    return badge

def start_study_session(user_id, skill_id):
    """Start a new study session for tracking time"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # Check for any ongoing sessions for this user and skill
        cursor.execute(
            "SELECT id FROM study_sessions WHERE user_id = ? AND skill_id = ? AND end_time IS NULL",
            (user_id, skill_id)
        )
        ongoing = cursor.fetchone()
        
        if ongoing:
            conn.close()
            return False, "You already have an ongoing study session for this skill."
        
        # Insert new study session
        cursor.execute(
            "INSERT INTO study_sessions (user_id, skill_id, start_time) VALUES (?, ?, ?)",
            (user_id, skill_id, current_time)
        )
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return True, session_id
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error starting study session: {str(e)}"

def end_study_session(session_id):
    """End an ongoing study session and calculate duration"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        # Get the session details
        cursor.execute(
            "SELECT user_id, skill_id, start_time FROM study_sessions WHERE id = ? AND end_time IS NULL",
            (session_id,)
        )
        session = cursor.fetchone()
        
        if not session:
            conn.close()
            return False, "No active study session found."
        
        user_id, skill_id, start_time = session
        
        # Calculate duration in minutes
        start_dt = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.datetime.strptime(current_time, "%Y-%m-%d %H:%M:%S")
        duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
        
        # Update the session with end time and duration
        cursor.execute(
            "UPDATE study_sessions SET end_time = ?, duration_minutes = ? WHERE id = ?",
            (current_time, duration_minutes, session_id)
        )
        
        # Update user's total study time and badge
        cursor.execute(
            "SELECT total_study_minutes FROM user_badges WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        
        if result:
            total_minutes = result[0] + duration_minutes
            
            # Get the new badge based on total time
            new_badge = get_badge_for_minutes(total_minutes)
            
            cursor.execute(
                "UPDATE user_badges SET total_study_minutes = ?, current_badge = ?, badge_updated_at = ? WHERE user_id = ?",
                (total_minutes, new_badge, current_time, user_id)
            )
        
        conn.commit()
        conn.close()
        
        return True, duration_minutes
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error ending study session: {str(e)}"

def get_user_study_stats(user_id):
    """Get study statistics for a user including total time and current badge"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT total_study_minutes, current_badge FROM user_badges WHERE user_id = ?",
        (user_id,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return {
            "total_minutes": 0,
            "total_hours": 0,
            "current_badge": "Member",
            "next_badge": "Entry",
            "minutes_to_next_badge": 60
        }
    
    total_minutes, current_badge = result
    
    # Find the next badge level
    current_level_index = next((i for i, level in enumerate(BADGE_LEVELS) if level["title"] == current_badge), 0)
    
    if current_level_index < len(BADGE_LEVELS) - 1:
        next_badge = BADGE_LEVELS[current_level_index + 1]["title"]
        next_badge_minutes = BADGE_LEVELS[current_level_index + 1]["minutes"]
        minutes_to_next_badge = max(0, next_badge_minutes - total_minutes)
    else:
        next_badge = "Highest Level Achieved!"
        minutes_to_next_badge = 0
    
    return {
        "total_minutes": total_minutes,
        "total_hours": round(total_minutes / 60, 1),
        "current_badge": current_badge,
        "next_badge": next_badge,
        "minutes_to_next_badge": minutes_to_next_badge
    }

def get_active_study_session(user_id, skill_id):
    """Get any active study session for the user and skill"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, start_time FROM study_sessions WHERE user_id = ? AND skill_id = ? AND end_time IS NULL",
        (user_id, skill_id)
    )
    session = cursor.fetchone()
    conn.close()
    
    if session:
        session_id, start_time = session
        start_dt = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        current_dt = datetime.datetime.now()
        elapsed_seconds = int((current_dt - start_dt).total_seconds())
        
        return {
            "session_id": session_id,
            "start_time": start_time,
            "elapsed_seconds": elapsed_seconds
        }
    
    return None

def get_study_history_by_skill(user_id):
    """Get study history grouped by skill"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT skill_id, SUM(duration_minutes) as total_minutes
        FROM study_sessions
        WHERE user_id = ? AND duration_minutes IS NOT NULL
        GROUP BY skill_id
        ORDER BY total_minutes DESC
        """,
        (user_id,)
    )
    results = cursor.fetchall()
    conn.close()
    
    return [{"skill_id": row[0], "total_minutes": row[1]} for row in results]

def add_progress_note(user_id, skill_id, note_text):
    """Add a progress note for a specific skill"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        cursor.execute(
            "INSERT INTO progress_notes (user_id, skill_id, note_text, created_at) VALUES (?, ?, ?, ?)",
            (user_id, skill_id, note_text, current_time)
        )
        
        note_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return True, note_id
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error adding progress note: {str(e)}"

def get_progress_notes(user_id, skill_id=None):
    """Get progress notes for a user, optionally filtered by skill"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        if skill_id:
            cursor.execute(
                """
                SELECT id, skill_id, note_text, created_at
                FROM progress_notes
                WHERE user_id = ? AND skill_id = ?
                ORDER BY created_at DESC
                """,
                (user_id, skill_id)
            )
        else:
            cursor.execute(
                """
                SELECT id, skill_id, note_text, created_at
                FROM progress_notes
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,)
            )
        
        notes = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": note[0],
                "skill_id": note[1],
                "note_text": note[2],
                "created_at": note[3]
            }
            for note in notes
        ]
    except Exception as e:
        conn.close()
        return []

def add_journal_entry(user_id, title, content, mood=None):
    """Add a journal entry"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        cursor.execute(
            """
            INSERT INTO journal_entries 
            (user_id, title, content, mood, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, content, mood, current_time, current_time)
        )
        
        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return True, entry_id
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error adding journal entry: {str(e)}"

def get_journal_entries(user_id, limit=None):
    """Get journal entries for a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        if limit:
            cursor.execute(
                """
                SELECT id, title, content, mood, created_at, updated_at
                FROM journal_entries
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit)
            )
        else:
            cursor.execute(
                """
                SELECT id, title, content, mood, created_at, updated_at
                FROM journal_entries
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,)
            )
        
        entries = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": entry[0],
                "title": entry[1],
                "content": entry[2],
                "mood": entry[3],
                "created_at": entry[4],
                "updated_at": entry[5]
            }
            for entry in entries
        ]
    except Exception as e:
        conn.close()
        return []

def get_journal_entry(user_id, entry_id):
    """Get a specific journal entry"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT id, title, content, mood, created_at, updated_at
        FROM journal_entries
        WHERE user_id = ? AND id = ?
        """,
        (user_id, entry_id)
    )
    
    entry = cursor.fetchone()
    conn.close()
    
    if entry:
        return {
            "id": entry[0],
            "title": entry[1],
            "content": entry[2],
            "mood": entry[3],
            "created_at": entry[4],
            "updated_at": entry[5]
        }
    
    return None

def update_journal_entry(user_id, entry_id, title, content, mood=None):
    """Update a journal entry"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        cursor.execute(
            """
            UPDATE journal_entries
            SET title = ?, content = ?, mood = ?, updated_at = ?
            WHERE user_id = ? AND id = ?
            """,
            (title, content, mood, current_time, user_id, entry_id)
        )
        
        if cursor.rowcount == 0:
            conn.close()
            return False, "Journal entry not found."
        
        conn.commit()
        conn.close()
        
        return True, "Journal entry updated successfully."
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error updating journal entry: {str(e)}"

def delete_journal_entry(user_id, entry_id):
    """Delete a journal entry"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "DELETE FROM journal_entries WHERE user_id = ? AND id = ?",
            (user_id, entry_id)
        )
        
        if cursor.rowcount == 0:
            conn.close()
            return False, "Journal entry not found."
        
        conn.commit()
        conn.close()
        
        return True, "Journal entry deleted successfully."
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error deleting journal entry: {str(e)}"

# Daily Goals Functions
def add_daily_goal(user_id, goal_text):
    """Add a new daily goal for a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        cursor.execute(
            "INSERT INTO daily_goals (user_id, goal_text, completed, created_at) VALUES (?, ?, ?, ?)",
            (user_id, goal_text, 0, current_time)
        )
        
        goal_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return True, goal_id
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error adding daily goal: {str(e)}"

def get_daily_goals(user_id):
    """Get all daily goals for a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get today's date in YYYY-MM-DD format
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    try:
        cursor.execute(
            """
            SELECT id, goal_text, completed, created_at
            FROM daily_goals
            WHERE user_id = ? AND created_at LIKE ?
            ORDER BY created_at DESC, id DESC
            """,
            (user_id, f"{today}%")
        )
        
        goals = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": goal[0],
                "goal_text": goal[1],
                "completed": bool(goal[2]),
                "created_at": goal[3]
            }
            for goal in goals
        ]
    except Exception as e:
        conn.close()
        return []

def toggle_goal_completion(user_id, goal_id):
    """Toggle the completion status of a daily goal"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # First get the current completion status
        cursor.execute(
            "SELECT completed FROM daily_goals WHERE id = ? AND user_id = ?",
            (goal_id, user_id)
        )
        
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return False, "Goal not found."
        
        # Toggle the completion status
        new_status = 0 if result[0] else 1
        
        cursor.execute(
            "UPDATE daily_goals SET completed = ? WHERE id = ? AND user_id = ?",
            (new_status, goal_id, user_id)
        )
        
        conn.commit()
        conn.close()
        
        return True, "Goal status updated successfully."
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error updating goal status: {str(e)}"

def delete_daily_goal(user_id, goal_id):
    """Delete a daily goal"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "DELETE FROM daily_goals WHERE id = ? AND user_id = ?",
            (goal_id, user_id)
        )
        
        if cursor.rowcount == 0:
            conn.close()
            return False, "Goal not found."
        
        conn.commit()
        conn.close()
        
        return True, "Goal deleted successfully."
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error deleting goal: {str(e)}"

def update_tutorial_completed(user_id, completed=True):
    """Update the tutorial completion status for a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if the tutorial_completed column exists
        try:
            cursor.execute("SELECT tutorial_completed FROM users WHERE id = ?", (user_id,))
            # Column exists, proceed with update
            status = 1 if completed else 0
            
            cursor.execute(
                "UPDATE users SET tutorial_completed = ? WHERE id = ?",
                (status, user_id)
            )
            
            if cursor.rowcount == 0:
                conn.close()
                return False, "User not found."
        except sqlite3.OperationalError:
            # Column doesn't exist, add it
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN tutorial_completed INTEGER DEFAULT 0")
                # Now update the record
                status = 1 if completed else 0
                cursor.execute(
                    "UPDATE users SET tutorial_completed = ? WHERE id = ?",
                    (status, user_id)
                )
            except Exception as e:
                conn.rollback()
                conn.close()
                return False, f"Error adding tutorial_completed column: {str(e)}"
        
        conn.commit()
        conn.close()
        
        return True, "Tutorial status updated successfully."
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return False, f"Error updating tutorial status: {str(e)}"

def update_notification_settings(user_id, phone_number=None, notifications_enabled=False, 
                          notify_progress=False, notify_badges=False, notify_reminders=False, 
                          reminder_time=None):
    """Update notification settings for a user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Convert boolean values to integers for SQLite
        notifications_enabled_int = 1 if notifications_enabled else 0
        notify_progress_int = 1 if notify_progress else 0
        notify_badges_int = 1 if notify_badges else 0
        notify_reminders_int = 1 if notify_reminders else 0
        
        cursor.execute(
            """
            UPDATE users SET
                phone_number = ?,
                notifications_enabled = ?,
                notify_progress = ?,
                notify_badges = ?,
                notify_reminders = ?,
                reminder_time = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (phone_number, notifications_enabled_int, notify_progress_int, notify_badges_int,
             notify_reminders_int, reminder_time, current_time, user_id)
        )
        
        if cursor.rowcount == 0:
            conn.close()
            return False, "User not found."
        
        conn.commit()
        conn.close()
        return True, "Notification settings updated successfully."
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error updating notification settings: {str(e)}"

def migrate_users_from_json(json_path):
    """Migrate users from JSON file to SQLite database"""
    import json
    
    if not os.path.exists(json_path):
        return False, "JSON file not found."
    
    try:
        with open(json_path, "r") as f:
            data = json.load(f)
        
        if "users" not in data:
            return False, "Invalid JSON structure."
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for user in data["users"]:
            username = user.get("username")
            email = user.get("email", f"{username}@example.com")  # Fallback email if missing
            password_hash = user.get("password")  # Note: This is SHA-256, not bcrypt
            created_at = user.get("created_at", current_time)
            
            # Skip if user already exists
            if user_exists(username, email):
                continue
                
            # Insert user with existing hash (will need to update later with bcrypt)
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (username, email, password_hash, created_at)
            )
            
            user_id = cursor.lastrowid
            
            # Initialize badge record
            cursor.execute(
                "INSERT INTO user_badges (user_id, total_study_minutes, current_badge, badge_updated_at) VALUES (?, ?, ?, ?)",
                (user_id, 0, "Member", current_time)
            )
        
        conn.commit()
        conn.close()
        return True, f"Successfully migrated users from {json_path}."
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False, f"Error during migration: {str(e)}"