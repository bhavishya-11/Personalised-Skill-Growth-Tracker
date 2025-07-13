from database import (
    SKILLS_DB_PATH, 
    get_user_data_from_db, 
    add_item_to_db, 
    update_item_in_db, 
    delete_item_from_db,
    get_unique_values_from_db
)
import auth_db
import streamlit as st
import datetime

def get_user_skills(username):
    """Get all skills for a specific user"""
    return get_user_data_from_db(username, SKILLS_DB_PATH, "skills")

def add_skill(username, skill_id, name, category, description, progress=0):
    """Add a new skill for a user"""
    skill_data = {
        "id": skill_id,
        "name": name,
        "category": category,
        "description": description,
        "progress": progress
    }
    
    return add_item_to_db(username, skill_data, SKILLS_DB_PATH, "skills")

def update_skill_progress(username, skill_id, progress):
    """Update the progress of a skill"""
    updated_data = {"progress": progress}
    return update_item_in_db(username, skill_id, updated_data, SKILLS_DB_PATH, "skills")

def update_skill_details(username, skill_id, name, category, description):
    """Update the details of a skill"""
    updated_data = {
        "name": name,
        "category": category,
        "description": description
    }
    
    return update_item_in_db(username, skill_id, updated_data, SKILLS_DB_PATH, "skills")

def delete_skill(username, skill_id):
    """Delete a skill"""
    return delete_item_from_db(username, skill_id, SKILLS_DB_PATH, "skills")

def get_skill_categories():
    """Get all unique skill categories from the database"""
    categories = get_unique_values_from_db("category", SKILLS_DB_PATH, "skills")
    
    # Add default categories if none exist
    if not categories:
        categories = {
            "Programming", 
            "Design", 
            "Data Science", 
            "Language", 
            "Soft Skills",
            "Music", 
            "Cooking", 
            "Sports", 
            "Business", 
            "Academic"
        }
    
    return sorted(categories)

def get_skill_by_id(username, skill_id):
    """Get a specific skill by its ID"""
    user_skills = get_user_skills(username)
    
    for skill in user_skills:
        if skill["id"] == skill_id:
            return skill
    
    return None

def get_skills_by_category(username, category):
    """Get all skills for a user in a specific category"""
    user_skills = get_user_skills(username)
    return [skill for skill in user_skills if skill["category"] == category]

def get_skills_progress_summary(username):
    """Get a summary of progress for all user skills"""
    user_skills = get_user_skills(username)
    
    if not user_skills:
        return {
            "total_skills": 0,
            "completed_skills": 0,
            "in_progress_skills": 0,
            "avg_progress": 0
        }
    
    total_skills = len(user_skills)
    completed_skills = len([s for s in user_skills if s["progress"] == 100])
    in_progress_skills = total_skills - completed_skills
    avg_progress = sum(s["progress"] for s in user_skills) / total_skills
    
    return {
        "total_skills": total_skills,
        "completed_skills": completed_skills,
        "in_progress_skills": in_progress_skills,
        "avg_progress": avg_progress
    }

def format_time(seconds):
    """Format seconds into hours:minutes:seconds"""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

def start_study_timer(username, skill_id):
    """Start a study timer for a specific skill"""
    # Get user ID
    user_id = auth_db.get_user_id(username)
    if not user_id:
        return False, "User not found"
    
    # Start the session in the database
    success, result = auth_db.start_study_session(user_id, skill_id)
    
    if success:
        # Store session ID in session state
        if "active_study_sessions" not in st.session_state:
            st.session_state.active_study_sessions = {}
        
        st.session_state.active_study_sessions[skill_id] = result
        return True, "Study timer started"
    else:
        return False, result

def end_study_timer(username, skill_id):
    """End a study timer for a specific skill"""
    if "active_study_sessions" not in st.session_state or skill_id not in st.session_state.active_study_sessions:
        return False, "No active study timer found"
    
    session_id = st.session_state.active_study_sessions[skill_id]
    
    # Store the old stats to check for badge change
    user_id = auth_db.get_user_id(username)
    old_stats = auth_db.get_user_study_stats(user_id)
    old_badge = old_stats["current_badge"]
    
    # End the session in the database
    success, result = auth_db.end_study_session(session_id)
    
    if success:
        # Check if badge changed
        new_stats = auth_db.get_user_study_stats(user_id)
        new_badge = new_stats["current_badge"]
        
        # Remove from active sessions
        del st.session_state.active_study_sessions[skill_id]
        return True, f"Study session ended. You studied for {result} minutes."
    else:
        return False, result

def get_active_study_timer(username, skill_id):
    """Get the current active study timer for a skill if exists"""
    user_id = auth_db.get_user_id(username)
    if not user_id:
        return None
    
    return auth_db.get_active_study_session(user_id, skill_id)

def get_study_badge(username):
    """Get the current user's badge and study stats"""
    user_id = auth_db.get_user_id(username)
    if not user_id:
        return {
            "current_badge": "Member",
            "next_badge": "Entry",
            "progress_percent": 0,
            "total_hours": 0,
            "minutes_to_next_badge": 60
        }
    
    stats = auth_db.get_user_study_stats(user_id)
    
    # Calculate progress to next badge
    if stats["minutes_to_next_badge"] > 0:
        # Find current and next badge thresholds
        current_badge_index = next((i for i, b in enumerate(auth_db.BADGE_LEVELS) 
                                    if b["title"] == stats["current_badge"]), 0)
        
        current_threshold = auth_db.BADGE_LEVELS[current_badge_index]["minutes"]
        next_threshold = auth_db.BADGE_LEVELS[current_badge_index + 1]["minutes"] if current_badge_index < len(auth_db.BADGE_LEVELS) - 1 else current_threshold
        
        # Calculate progress
        progress_range = next_threshold - current_threshold
        progress_value = stats["total_minutes"] - current_threshold
        progress_percent = min(100, int((progress_value / progress_range) * 100)) if progress_range > 0 else 100
    else:
        progress_percent = 100
    
    stats["progress_percent"] = progress_percent
    return stats

def get_study_history_by_skill(username):
    """Get study history for all skills"""
    user_id = auth_db.get_user_id(username)
    if not user_id:
        return []
    
    skill_times = auth_db.get_study_history_by_skill(user_id)
    
    # Enrich with skill names
    user_skills = get_user_skills(username)
    skill_dict = {skill["id"]: skill["name"] for skill in user_skills}
    
    for item in skill_times:
        item["skill_name"] = skill_dict.get(item["skill_id"], "Unknown Skill")
        item["hours"] = round(item["total_minutes"] / 60, 1)
    
    return skill_times

def add_progress_note(username, skill_id, note_text):
    """Add a progress note for a skill"""
    user_id = auth_db.get_user_id(username)
    if not user_id:
        return False, "User not found"
    
    return auth_db.add_progress_note(user_id, skill_id, note_text)

def get_progress_notes(username, skill_id=None):
    """Get progress notes for a user, optionally filtered by skill"""
    user_id = auth_db.get_user_id(username)
    if not user_id:
        return []
    
    notes = auth_db.get_progress_notes(user_id, skill_id)
    
    # Enrich with skill names if no specific skill was requested
    if not skill_id and notes:
        user_skills = get_user_skills(username)
        skill_dict = {skill["id"]: skill["name"] for skill in user_skills}
        
        for note in notes:
            note["skill_name"] = skill_dict.get(note["skill_id"], "Unknown Skill")
    
    return notes

def add_journal_entry(username, title, content, mood=None):
    """Add a journal entry for a user"""
    user_id = auth_db.get_user_id(username)
    if not user_id:
        return False, "User not found"
    
    return auth_db.add_journal_entry(user_id, title, content, mood)

def get_journal_entries(username, limit=None):
    """Get journal entries for a user"""
    user_id = auth_db.get_user_id(username)
    if not user_id:
        return []
    
    return auth_db.get_journal_entries(user_id, limit)

def get_journal_entry(username, entry_id):
    """Get a specific journal entry"""
    user_id = auth_db.get_user_id(username)
    if not user_id:
        return None
    
    return auth_db.get_journal_entry(user_id, entry_id)

def update_journal_entry(username, entry_id, title, content, mood=None):
    """Update a journal entry"""
    user_id = auth_db.get_user_id(username)
    if not user_id:
        return False, "User not found"
    
    return auth_db.update_journal_entry(user_id, entry_id, title, content, mood)

def delete_journal_entry(username, entry_id):
    """Delete a journal entry"""
    user_id = auth_db.get_user_id(username)
    if not user_id:
        return False, "User not found"
    
    return auth_db.delete_journal_entry(user_id, entry_id)

# Daily Goals Functions
def add_daily_goal(username, goal_text):
    """Add a new daily goal for a user"""
    user_id = auth_db.get_user_id(username)
    if not user_id:
        return False, "User not found"
    
    return auth_db.add_daily_goal(user_id, goal_text)

def get_daily_goals(username):
    """Get all daily goals for a user"""
    user_id = auth_db.get_user_id(username)
    if not user_id:
        return []
    
    return auth_db.get_daily_goals(user_id)

def toggle_goal_completion(username, goal_id):
    """Toggle the completion status of a daily goal"""
    user_id = auth_db.get_user_id(username)
    if not user_id:
        return False, "User not found"
    
    return auth_db.toggle_goal_completion(user_id, goal_id)

def delete_daily_goal(username, goal_id):
    """Delete a daily goal"""
    user_id = auth_db.get_user_id(username)
    if not user_id:
        return False, "User not found"
    
    return auth_db.delete_daily_goal(user_id, goal_id)

# Tutorial Functions
def mark_tutorial_completed(username, completed=True):
    """Mark the tutorial as completed for a user"""
    user_id = auth_db.get_user_id(username)
    if not user_id:
        return False, "User not found"
    
    return auth_db.update_tutorial_completed(user_id, completed)

def is_tutorial_completed(username):
    """Check if the tutorial is completed for a user"""
    user_data = auth_db.get_user_data(username)
    if not user_data:
        return False
    
    return user_data.get("tutorial_completed", False)
