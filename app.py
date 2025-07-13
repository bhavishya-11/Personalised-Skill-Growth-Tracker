import streamlit as st
import pandas as pd
import time
import auth_db
from database import initialize_database
from skills import (
    get_user_skills, add_skill, update_skill_progress, delete_skill,
    get_skill_categories, format_time, start_study_timer, end_study_timer,
    get_active_study_timer, get_study_badge, get_study_history_by_skill,
    add_progress_note, get_progress_notes, add_journal_entry, get_journal_entries,
    get_journal_entry, update_journal_entry, delete_journal_entry,
    # New functions for daily goals
    add_daily_goal, get_daily_goals, toggle_goal_completion, delete_daily_goal,
    # New functions for tutorial
    mark_tutorial_completed, is_tutorial_completed
)
from google_api import search_study_materials
from visualizations import create_skill_progress_chart, create_skills_radar_chart
from utils import generate_skill_id, validate_skill_data
from ai_assistant import generate_skill_path, display_ai_chat_interface

# Page configuration
st.set_page_config(
    page_title="SkillGrow - Personal Skill Tracker",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_auth():
    """Initialize authentication related session state variables"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "active_study_sessions" not in st.session_state:
        st.session_state.active_study_sessions = {}
    if "show_tutorial" not in st.session_state:
        st.session_state.show_tutorial = False
    if "tutorial_step" not in st.session_state:
        st.session_state.tutorial_step = 1
    if "current_learning_path" not in st.session_state:
        st.session_state.current_learning_path = None
    if "current_skill_id" not in st.session_state:
        st.session_state.current_skill_id = None

def is_authenticated():
    """Check if a user is currently authenticated"""
    return st.session_state.authenticated

def get_username():
    """Get the username of the currently authenticated user"""
    return st.session_state.username if is_authenticated() else None

def logout_user():
    """Log out the current user"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_id = None
    
    # End any active study sessions
    if "active_study_sessions" in st.session_state and st.session_state.active_study_sessions:
        for skill_id, session_id in st.session_state.active_study_sessions.items():
            auth_db.end_study_session(session_id)
        st.session_state.active_study_sessions = {}

def login_user(username, password):
    """Login a user using the SQLite database"""
    success, message = auth_db.login_user(username, password)
    return success

def register_user(username, email, password):
    """Register a new user in the SQLite database"""
    success, message = auth_db.register_user(username, email, password)
    return success

def main():
    # Initialize databases
    initialize_database()
    auth_db.initialize_db()
    initialize_auth()
    
    # Migrate users if needed (one-time operation)
    if "migration_done" not in st.session_state:
        # Try to migrate users from JSON to SQLite
        success, message = auth_db.migrate_users_from_json("user_data.json")
        st.session_state.migration_done = True
    
    # Sidebar for navigation
    with st.sidebar:
        st.title("SkillGrow")
        st.write("Track your personal skill development")
        
        if is_authenticated():
            username = get_username()
            
            # Get user badge and display it
            badge_data = get_study_badge(username)
            
            st.write(f"Welcome, **{username}**!")
            st.write(f"🏆 **{badge_data['current_badge']}**")
            st.progress(badge_data['progress_percent'] / 100)
            st.write(f"Total study time: **{badge_data['total_hours']}** hours")
            st.write(f"Next badge: **{badge_data['next_badge']}** ({badge_data['minutes_to_next_badge']} mins needed)")
            
            nav_option = st.radio(
                "Navigation",
                ["Dashboard", "Add New Skill", "Study Resources", "Study Timer", "Progress Notes", "Journal", "Daily Goals", "AI Assistant", "Profile"]
            )
            
            if st.button("Logout"):
                logout_user()
                st.rerun()
        else:
            nav_option = st.radio("Navigation", ["Login", "Register"])
    
    # Display the appropriate page based on navigation choice
    if not is_authenticated():
        if nav_option == "Login":
            display_login_page()
        elif nav_option == "Register":
            display_register_page()
    else:
        # Check if we should show tutorial
        username = get_username()
        if not is_tutorial_completed(username) and not st.session_state.show_tutorial:
            st.session_state.show_tutorial = True
            
        # Show tutorial if applicable
        if st.session_state.show_tutorial:
            display_tutorial()
        else:
            # Display selected page
            if nav_option == "Dashboard":
                display_dashboard()
            elif nav_option == "Add New Skill":
                display_add_skill_page()
            elif nav_option == "Study Resources":
                display_study_resources_page()
            elif nav_option == "Study Timer":
                display_study_timer_page()
            elif nav_option == "Progress Notes":
                display_progress_notes_page()
            elif nav_option == "Journal":
                display_journal_page()
            elif nav_option == "Daily Goals":
                display_daily_goals_page()
            elif nav_option == "AI Assistant":
                display_ai_assistant_page()
            elif nav_option == "Profile":
                display_profile_page()

def display_login_page():
    st.title("Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if username and password:
                if login_user(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.error("Please enter both username and password")

def display_register_page():
    st.title("Register")
    
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit_button = st.form_submit_button("Register")
        
        if submit_button:
            if not username or not email or not password or not confirm_password:
                st.error("Please fill out all fields")
            elif password != confirm_password:
                st.error("Passwords do not match")
            else:
                if register_user(username, email, password):
                    st.success("Registration successful! You can now login.")
                else:
                    st.error("Username or email already exists")



def display_dashboard():
    st.title("Your Skills Dashboard")
    
    username = get_username()
    user_skills = get_user_skills(username)
    
    if not user_skills:
        st.info("You haven't added any skills yet. Go to 'Add New Skill' to get started!")
    else:
        # Display overall progress chart
        st.subheader("Overall Skill Progress")
        progress_chart = create_skill_progress_chart(user_skills)
        st.plotly_chart(progress_chart, use_container_width=True)
        
        # Display radar chart for skill categories
        st.subheader("Skills by Category")
        radar_chart = create_skills_radar_chart(user_skills)
        st.plotly_chart(radar_chart, use_container_width=True)
        
        # List all skills with options to update progress
        st.subheader("Your Skills")
        
        # Create columns for better display
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write("Select a skill to update its progress:")
        
        with col2:
            if st.button("Refresh"):
                st.rerun()
                
        for skill in user_skills:
            with st.expander(f"{skill['name']} - {skill['category']} ({skill['progress']}%)"):
                st.write(f"**Description:** {skill['description']}")
                st.write(f"**Started:** {skill['created_at']}")
                
                # Skill progress update
                st.subheader("Update Progress")
                new_progress = st.slider(
                    "Progress Percentage",
                    min_value=0,
                    max_value=100,
                    value=skill['progress'],
                    key=f"progress_{skill['id']}"
                )
                
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    if st.button("Update Progress", key=f"update_{skill['id']}"):
                        update_skill_progress(username, skill['id'], new_progress)
                        st.success("Progress updated!")
                        st.rerun()
                
               
                
                with col3:
                    if st.button("Delete Skill", key=f"delete_{skill['id']}"):
                        delete_skill(username, skill['id'])
                        st.success("Skill deleted!")
                        st.rerun()
                


def display_add_skill_page():
    st.title("Add New Skill")
    
    username = get_username()
    
    with st.form("add_skill_form"):
        skill_name = st.text_input("Skill Name")
        
        # Get predefined categories and allow custom category creation
        categories = get_skill_categories()
        category_options = list(categories)
        
        # Custom radio selection for category handling
        category_selection = st.radio(
            "Category", 
            ["Select from existing categories"]
        )
        
        if category_selection == "Select from existing categories":
            selected_category = st.selectbox("Choose a category", category_options) if category_options else ""
        else:
            selected_category = st.text_input("Create a custom category", placeholder="Enter a new category name...",key="custom_category_input")
        
        skill_description = st.text_area("Description")
        initial_progress = st.slider("Initial Progress (%)", 0, 100, 0)
        
        submit_button = st.form_submit_button("Add Skill")
        
        if submit_button:
            if not skill_name or not selected_category:
                st.error("Skill name and category are required")
            else:
                validation_result = validate_skill_data(skill_name, selected_category, skill_description)
                
                if validation_result["valid"]:
                    skill_id = generate_skill_id()
                    add_skill(
                        username,
                        skill_id,
                        skill_name,
                        selected_category,
                        skill_description,
                        initial_progress
                    )
                    st.success(f"Skill '{skill_name}' added successfully!")
                else:
                    st.error(validation_result["message"])

def display_study_resources_page():
    st.title("Study Resources")
    
    # Get user skills for dropdown
    username = get_username()
    user_skills = get_user_skills(username)
    skill_names = [skill["name"] for skill in user_skills]
    
    # Search box
    search_skill = st.selectbox(
        "Select a skill to find study materials",
        [""] + skill_names,
        index=0
    )
    
    additional_keywords = st.text_input(
        "Additional search keywords (optional)",
        placeholder="e.g., tutorial, beginner, advanced"
    )
    
    search_query = ""
    if search_skill:
        search_query = search_skill
        if additional_keywords:
            search_query += f" {additional_keywords}"
    
    if st.button("Search") and search_query:
        with st.spinner("Searching for study materials..."):
            search_results = search_study_materials(search_query, max_results=10)
            
            if search_results:
                st.subheader(f"Study Resources for {search_skill}")
                
                for i, result in enumerate(search_results):
                    with st.expander(f"{i+1}. {result['title']}"):
                        st.write(f"**Link:** [{result['link']}]({result['link']})")
                        st.write(f"**Description:** {result['snippet']}")
            else:
                st.error("No study materials found. Try different keywords.")

def display_study_timer_page():
    st.title("Study Timer")
    st.subheader("Track your study time and earn badges")
    
    username = get_username()
    user_skills = get_user_skills(username)
    
    if not user_skills:
        st.info("You haven't added any skills yet. Go to 'Add New Skill' to get started!")
        return
    
    # Badge information
    badge_data = get_study_badge(username)
    
    # Display badge progress in a more visual way
    st.markdown(f"### Your Current Badge: 🏆 {badge_data['current_badge']}")
    st.write(f"Total study time: **{badge_data['total_hours']}** hours")
    
    # Progress bar to next badge
    if badge_data['next_badge'] != "Highest Level Achieved!":
        st.write(f"Progress to **{badge_data['next_badge']}**:")
        st.progress(badge_data['progress_percent'] / 100)
        st.write(f"*{badge_data['minutes_to_next_badge']} more minutes needed*")
    else:
        st.success("Congratulations! You've reached the highest badge level!")
    
    # Badge Levels Explanation
    with st.expander("View All Badge Levels"):
        # Create a DataFrame for badge levels
        badge_levels = auth_db.BADGE_LEVELS
        levels_df = pd.DataFrame({
            "Badge": [level["title"] for level in badge_levels],
            "Required Hours": [round(level["minutes"] / 60, 1) for level in badge_levels]
        })
        st.table(levels_df)
    
    st.markdown("---")
    
    # Study History
    history = get_study_history_by_skill(username)
    if history:
        st.subheader("Your Study History")
        
        # Create DataFrame for study history
        history_df = pd.DataFrame({
            "Skill": [item["skill_name"] for item in history],
            "Hours": [item["hours"] for item in history]
        })
        
        # Display as chart
        st.bar_chart(history_df.set_index("Skill"))
    
    st.markdown("---")
    
    # Study Timer Interface
    st.subheader("Study Timer")
    
    # Select skill to study
    skill_options = [(skill["id"], skill["name"]) for skill in user_skills]
    selected_skill_idx = st.selectbox(
        "Select a skill to track study time:",
        range(len(skill_options)),
        format_func=lambda i: skill_options[i][1]
    )
    
    selected_skill_id, selected_skill_name = skill_options[selected_skill_idx]
    
    # Check if there's an active timer for this skill
    active_session = get_active_study_timer(username, selected_skill_id)
    
    col1, col2 = st.columns(2)
    
    # Timer display and controls
    if active_session:
        elapsed_seconds = active_session["elapsed_seconds"]
        
        # Create a placeholder for the timer display that updates
        timer_placeholder = st.empty()
        
        # Function to update timer display
        def update_timer():
            current_time = time.time()
            updated_seconds = int(elapsed_seconds + (current_time - start_time))
            timer_placeholder.markdown(f"## ⏱️ {format_time(updated_seconds)}")
            return updated_seconds
        
        # Initial timer display
        start_time = time.time()
        updated_seconds = update_timer()
        
        # Controls for stopping the timer
        if st.button("End Study Session", key="end_session"):
            # End the session
            success, message = end_study_timer(username, selected_skill_id)
            
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
        
        # Update the timer every second (up to 10 seconds)
        for _ in range(10):
            time.sleep(1)
            updated_seconds = update_timer()
        
        st.info("Timer is running! The displayed time will update when you interact with the page.")
            
    else:
        # Start timer button
        if st.button("Start Study Session", key="start_session"):
            success, message = start_study_timer(username, selected_skill_id)
            if success:
                st.success(f"Started study timer for {selected_skill_name}")
                st.rerun()
            else:
                st.error(message)
    
    # Study tips
    with st.expander("Study Tips"):
        st.markdown("""
        ### Effective Study Techniques
        1. **Pomodoro Technique**: Study for 25 minutes, then take a 5-minute break
        2. **Active Recall**: Test yourself on what you've learned
        3. **Spaced Repetition**: Review material at increasing intervals
        4. **Teach Someone Else**: Explaining concepts reinforces understanding
        5. **Change Your Environment**: Different environments can boost focus
        """)

def display_progress_notes_page():
    st.title("Progress Notes")
    st.subheader("Track your learning achievements and challenges")
    
    username = get_username()
    user_skills = get_user_skills(username)
    
    if not user_skills:
        st.info("You haven't added any skills yet. Go to 'Add New Skill' to get started!")
        return
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["All Notes", "Add New Note"])
    
    # All Notes Tab
    with tab1:
        # Get all notes
        all_notes = get_progress_notes(username)
        
        if not all_notes:
            st.info("You haven't added any progress notes yet. Use the 'Add New Note' tab to get started!")
        else:
            # Filter options
            st.subheader("Filter Notes")
            
            # Get skill names for filter
            skill_map = {skill['id']: skill['name'] for skill in user_skills}
            skill_options = ["All Skills"] + list(skill_map.values())
            
            selected_skill_filter = st.selectbox(
                "Filter by skill:",
                skill_options
            )
            
            # Search functionality
            search_query = st.text_input("Search notes:", placeholder="Enter keywords...")
            
            # Filter notes based on selections
            filtered_notes = all_notes
            
            # Filter by skill if not "All Skills"
            if selected_skill_filter != "All Skills":
                # Find the skill ID for the selected name
                selected_skill_id = None
                for skill_id, skill_name in skill_map.items():
                    if skill_name == selected_skill_filter:
                        selected_skill_id = skill_id
                        break
                
                if selected_skill_id:
                    filtered_notes = [note for note in filtered_notes if note['skill_id'] == selected_skill_id]
            
            # Filter by search query if present
            if search_query:
                filtered_notes = [
                    note for note in filtered_notes 
                    if search_query.lower() in note['note_text'].lower()
                ]
            
            # Display filtered notes
            if not filtered_notes:
                st.warning("No notes match your filter criteria.")
            else:
                st.subheader(f"Showing {len(filtered_notes)} Notes")
                
                for note in filtered_notes:
                    # Format date for display
                    note_date = note['created_at'].split()[0]
                    
                    # Get skill name for note
                    skill_name = skill_map.get(note['skill_id'], "Unknown Skill")
                    
                    # Display note in expander
                    with st.expander(f"{skill_name} - {note_date}"):
                        st.markdown(f"### Note for: {skill_name}")
                        st.caption(f"Created on {note_date}")
                        st.markdown(note['note_text'])
    
    # Add New Note Tab
    with tab2:
        st.subheader("Add a New Progress Note")
        
        # Select skill for the note
        skill_options = [(skill["id"], skill["name"]) for skill in user_skills]
        selected_skill_idx = st.selectbox(
            "Select a skill:",
            range(len(skill_options)),
            format_func=lambda i: skill_options[i][1]
        )
        
        selected_skill_id, selected_skill_name = skill_options[selected_skill_idx]
        
        # Note text area
        new_note = st.text_area(
            f"Progress note for {selected_skill_name}:",
            placeholder="Record your progress, challenges, insights, or achievements...",
            height=200
        )
        
        # Guidelines for effective notes
        with st.expander("Tips for Effective Progress Notes"):
            st.markdown("""
            ### How to Write Effective Progress Notes
            
            1. **Be specific** about what you learned or accomplished
            2. **Document challenges** you faced and how you addressed them
            3. **Include resources** that were particularly helpful
            4. **Note any insights** or "aha moments" you experienced
            5. **Record questions** that came up during your learning
            6. **Set next steps** for future learning sessions
            """)
        
        # Save button
        if st.button("Save Note"):
            if new_note:
                success, message = add_progress_note(username, selected_skill_id, new_note)
                if success:
                    st.success("Progress note added successfully!")
                    # Clear the input
                    st.rerun()
                else:
                    st.error(f"Error adding note: {message}")
            else:
                st.warning("Please enter a note before saving.")

def display_profile_page():
    st.title("Your Profile")
    
    username = get_username()
    user_id = auth_db.get_user_id(username)
    user_skills = get_user_skills(username)
    user_data = auth_db.get_user_data(username)
    
    # Create tabs for different profile sections
    tab1, tab2 = st.tabs(["Stats & Summary", "Account Settings"])
    
    with tab1:
        # Get badge information
        badge_data = get_study_badge(username)
        
        # Study stats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Study Hours", badge_data["total_hours"])
        
        with col2:
            st.metric("Current Badge", badge_data["current_badge"])
        
        with col3:
            next_level_hours = round(badge_data["minutes_to_next_badge"] / 60, 1)
            st.metric("Hours to Next Badge", next_level_hours)
        
        # Skills summary stats
        st.subheader("Skills Summary")
        
        total_skills = len(user_skills)
        completed_skills = len([s for s in user_skills if s["progress"] == 100])
        avg_progress = sum(s["progress"] for s in user_skills) / total_skills if total_skills > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Skills", total_skills)
        
        with col2:
            st.metric("Completed Skills", completed_skills)
        
        with col3:
            st.metric("Average Progress", f"{avg_progress:.1f}%")
        
        # Skill distribution by category
        if user_skills:
            st.subheader("Skills by Category")
            
            # Count skills per category
            category_counts = {}
            for skill in user_skills:
                category = skill["category"]
                if category in category_counts:
                    category_counts[category] += 1
                else:
                    category_counts[category] = 1
            
            # Create a DataFrame for the chart
            categories_df = pd.DataFrame({
                "Category": list(category_counts.keys()),
                "Count": list(category_counts.values())
            })
            
            st.bar_chart(categories_df.set_index("Category"))
        
        # Study history
        history = get_study_history_by_skill(username)
        if history:
            st.subheader("Study Time by Skill")
            
            # Create DataFrame for study history
            history_df = pd.DataFrame({
                "Skill": [item["skill_name"] for item in history],
                "Hours": [item["hours"] for item in history]
            })
            
            # Display as chart
            st.bar_chart(history_df.set_index("Skill"))
        
        # Option to export skills data
        if st.button("Export Skills Data"):
            if user_skills:
                # Create a DataFrame from user skills
                skills_df = pd.DataFrame(user_skills)
                
                # Convert to CSV for download
                csv = skills_df.to_csv(index=False)
                st.download_button(
                    label="Download as CSV",
                    data=csv,
                    file_name=f"{username}_skills.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No skills data to export.")
    
    with tab2:
        st.subheader("Account Information")
        st.write(f"**Username:** {username}")
        st.write(f"**Email:** {user_data['email']}")
        st.write(f"**Account Created:** {user_data['created_at'].split()[0]}")
        



def display_journal_page():
    st.title("Learning Journal")
    st.subheader("Track your learning journey")
    
    username = get_username()
    
    # Tabs for journal sections
    tab1, tab2 = st.tabs(["My Journal", "Add New Entry"])
    
    with tab1:
        # Display existing journal entries
        journal_entries = get_journal_entries(username)
        
        if not journal_entries:
            st.info("You haven't added any journal entries yet. Use the 'Add New Entry' tab to get started!")
        else:
            # Filter/search functionality
            search_query = st.text_input("Search entries", placeholder="Type to search...")
            
            filtered_entries = journal_entries
            if search_query:
                filtered_entries = [
                    entry for entry in journal_entries 
                    if search_query.lower() in entry["title"].lower() or search_query.lower() in entry["content"].lower()
                ]
            
            if not filtered_entries:
                st.warning("No entries match your search.")
            
            # Display entries
            for entry in filtered_entries:
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    st.markdown(f"### {entry['title']}")
                    st.caption(f"Created: {entry['created_at'].split()[0]}")
                
                with col2:
                    # Display mood emoji if available
                    if entry.get("mood"):
                        mood_emoji = "😊" if entry["mood"] == "happy" else "😐" if entry["mood"] == "neutral" else "😔"
                        st.markdown(f"### {mood_emoji}")
                
                # Entry content
                st.markdown(entry["content"])
                
                # Action buttons
                col1, col2 = st.columns([1, 5])
                with col1:
                    # Delete button with confirmation
                    if st.button("Delete", key=f"delete_{entry['id']}"):
                        st.session_state[f"confirm_delete_{entry['id']}"] = True
                
                # Confirmation dialog
                if st.session_state.get(f"confirm_delete_{entry['id']}", False):
                    st.warning("Are you sure you want to delete this entry?")
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("Yes, delete", key=f"confirm_{entry['id']}"):
                            delete_journal_entry(username, entry['id'])
                            st.success("Entry deleted!")
                            st.session_state[f"confirm_delete_{entry['id']}"] = False
                            st.rerun()
                    with col2:
                        if st.button("Cancel", key=f"cancel_{entry['id']}"):
                            st.session_state[f"confirm_delete_{entry['id']}"] = False
                            st.rerun()
                
                st.markdown("---")
    
    with tab2:
        # Form to add a new journal entry
        st.subheader("Create New Journal Entry")
        
        entry_title = st.text_input("Title", placeholder="Give your entry a title...")
        
        # Mood selection
        mood_options = {"😊 Happy": "happy", "😐 Neutral": "neutral", "😔 Challenging": "challenging"}
        selected_mood = st.radio("How was your learning experience?", list(mood_options.keys()))
        mood_value = mood_options[selected_mood]
        
        entry_content = st.text_area(
            "Journal Entry", 
            height=200,
            placeholder="Reflect on what you learned today, challenges you faced, or achievements you're proud of..."
        )
        
        if st.button("Save Journal Entry"):
            if entry_title and entry_content:
                success, message = add_journal_entry(username, entry_title, entry_content, mood_value)
                if success:
                    st.success("Journal entry saved!")
                    st.rerun()
                else:
                    st.error(f"Error saving entry: {message}")
            else:
                st.warning("Please enter both a title and content for your journal entry.")
        
        # Journaling prompts for inspiration
        with st.expander("Need inspiration? Try these journaling prompts:"):
            st.markdown("""
            - What was the most interesting thing you learned today?
            - What challenges did you face and how did you overcome them?
            - How can you apply what you learned to real-world situations?
            - What are your learning goals for tomorrow?
            - How has your understanding of this topic evolved?
            """)

def display_daily_goals_page():
    st.title("Daily Goals")
    st.subheader("Set and track your daily learning goals")
    
    username = get_username()
    
    # Create two columns for layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("Create a new goal for today:")
        
        # Add new goal form
        with st.form("add_goal_form"):
            goal_text = st.text_input("Goal", placeholder="Learn a new concept, practice for 30 mins, etc.")
            submit_button = st.form_submit_button("Add Goal")
            
            if submit_button and goal_text:
                success, message = add_daily_goal(username, goal_text)
                if success:
                    st.success("Goal added successfully!")
                    st.rerun()
                else:
                    st.error(f"Error adding goal: {message}")
    
    # Display existing goals
    st.subheader("Today's Goals")
    
    # Get user's goals for today
    goals = get_daily_goals(username)
    
    if not goals:
        st.info("You haven't set any goals for today. Add your first goal above!")
    else:
        for goal in goals:
            col1, col2 = st.columns([5, 1])
            
            with col1:
                # Use a checkbox for completion
                is_checked = st.checkbox(
                    goal['goal_text'], 
                    value=goal["completed"],
                    key=f"check_{goal['id']}"
                )
                
                # Toggle if checkbox state changed
                if is_checked != goal["completed"]:
                    toggle_goal_completion(username, goal['id'])
                    st.rerun()
            
            with col2:
                # Only show delete button
                if st.button("Delete", key=f"delete_{goal['id']}"):
                        delete_daily_goal(username, goal['id'])
                        st.rerun()
        
        # Display goal stats
        completed_goals = sum(1 for goal in goals if goal["completed"])
        total_goals = len(goals)
        
        st.progress(completed_goals / total_goals if total_goals > 0 else 0)
        st.write(f"**{completed_goals}** of **{total_goals}** goals completed")
        
        if completed_goals == total_goals and total_goals > 0:
            st.balloons()
            st.success("Congratulations! You've completed all your goals for today! 🎉")

def display_tutorial():
    st.title("Welcome to SkillGrow! 🚀")
    
    username = get_username()
    step = st.session_state.tutorial_step
    
    # Add JavaScript to automatically scroll to top when the page loads
    st.markdown("""
    <script>
        // Function to scroll to top of page
        function scrollToTop() {
            window.scrollTo(0, 0);
        }
        
        // Scroll to top when the page loads
        window.addEventListener('load', scrollToTop);
        
        // Also set up MutationObserver to detect DOM changes (for when buttons are clicked)
        const observer = new MutationObserver(scrollToTop);
        observer.observe(document.body, { childList: true, subtree: true });
    </script>
    """, unsafe_allow_html=True)
    
    # Create a consistent container style for the tutorial
    tutorial_container = st.container()
    with tutorial_container:
        # Tutorial content
        if step == 1:
            st.header("🎉 Let's Get Started!")
            
            # Introduction with feature highlights
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown("""
                Welcome to **SkillGrow**, your personal AI-powered skill development platform 
                focused on Machine Learning and AI skills.
                
                This quick interactive tutorial will guide you through the main features
                to help you make the most of the platform.
                """)
                
                st.markdown("""
                ### ✨ Key Features:
                
                📊 **Track your skills** with visual progress indicators
                
                ⏱️ **Monitor study time** and earn progression badges
                
                📚 **Find learning resources** for any ML/AI concept
                
                🎯 **Set daily goals** to build consistent habits
                
                📝 **Journal your learning** to reflect on progress
                
                🤖 **AI Assistant** for personalized learning paths
                """)
            
            with col2:
                # Simple visual to make tutorial more engaging
                # st.image("generated-icon.png", use_container_width=True)
                st.info("**Pro tip:** Complete this tutorial to get a solid understanding of how SkillGrow can enhance your learning journey.")
            
            # Set goals for the tutorial experience
            st.markdown("### 🚀 By the end of this tutorial, you'll be able to:")
            
            # Use checkboxes to create interactive feel (though they're just visual)
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("✓ Navigate the SkillGrow platform")
                st.markdown("✓ Add and track your skills")
                st.markdown("✓ Set daily goals and track progress")
            
            with col2:
                st.markdown("✓ Use the study timer system")
                st.markdown("✓ Create journal entries")
                st.markdown("✓ Use the AI learning assistant")
            
            # Clear call to action button
            if st.button("Start Tutorial →", type="primary"):
                st.session_state.tutorial_step = 2
                st.rerun()
                
        elif step == 2:
            st.header("📊 Your Dashboard")
            
            # Create a mockup of what the dashboard will look like
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown("""
                Your dashboard is the command center for your learning journey.
                
                Here you'll find all your skills organized with visual progress indicators
                and detailed analytics to track your growth over time.
                """)
                
                # Interactive elements to demonstrate dashboard features
                st.markdown("### 🔍 Dashboard Features:")
                
                # Collapsable demo feature
                with st.expander("📊 **Progress Charts**"):
                    st.write("Visual charts show your progress across all skills and categories.")
                    st.write("Examples include bar charts, radar charts, and progress meters.")
                    # Small demo chart
                    st.bar_chart({"Python": 80, "TensorFlow": 60, "PyTorch": 40, "ML Theory": 70})
                
                with st.expander("🔄 **Skill Updates**"):
                    st.write("Update your skill progress directly from the dashboard.")
                    # Demo slider
                    st.slider("Example: Python Progress", 0, 100, 75)
                    st.button("Update Progress (Demo)", disabled=True)
                
                with st.expander("📝 **Progress Notes**"):
                    st.write("Record your achievements, challenges, and insights for each skill.")
                    # Demo text area
                    st.text_area("Example note:", "Today I learned about neural network architectures...", disabled=True)
                    st.button("Save Note (Demo)", disabled=True)
            
            with col2:
                st.markdown("### 💡 Pro Tips")
                st.markdown("- Use the progress charts to identify skills that need attention")
                st.markdown("- Update progress regularly to stay motivated")
                st.markdown("- Add detailed notes to track your learning journey")
                st.markdown("- Click the Refresh button to see the latest data")
            
            # Navigation
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Previous"):
                    st.session_state.tutorial_step = 1
                    st.rerun()
            with col2:
                if st.button("Next: Study Timer →"):
                    st.session_state.tutorial_step = 3
                    st.rerun()
                    
        elif step == 3:
            st.header("⏱️ Study Timer & Badges")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown("""
                The Study Timer helps you track your learning time and rewards
                your dedication with achievement badges.
                
                Each minute you track contributes to your badge progression,
                creating a gamified learning experience.
                """)
                
                # Demo of the timer functionality
                st.markdown("### ⚙️ How the Study Timer Works:")
                
                with st.expander("**1. Select a Skill**"):
                    # Demo select box
                    st.selectbox("Choose skill:", ["Machine Learning", "Python", "Neural Networks"], disabled=True)
                
                with st.expander("**2. Start the Timer**"):
                    # Demo buttons
                    st.button("Start Timer (Demo)", disabled=True)
                    # Demo timer display
                    st.code("00:45:30", language=None)
                
                with st.expander("**3. Stop the Timer & Record Progress**"):
                    # Demo buttons
                    st.button("Stop Timer (Demo)", disabled=True)
                    st.success("✓ 45 minutes added to your study time!")
                
                # Badge system explanation
                st.markdown("### 🏆 Badge System")
                col1a, col2a = st.columns(2)
                with col1a:
                    st.markdown("- **Novice**: 0-2 hours")
                    st.markdown("- **Apprentice**: 2-10 hours")
                    st.markdown("- **Practitioner**: 10-30 hours")
                with col2a:
                    st.markdown("- **Expert**: 30-60 hours")
                    st.markdown("- **Master**: 60-100 hours")
                    st.markdown("- **Grandmaster**: 100+ hours")
            
            with col2:
                st.markdown("### 💡 Pro Tips")
                st.markdown("- Study in focused 25-minute sessions")
                st.markdown("- Take regular breaks between sessions")
                st.markdown("- Aim for consistent daily study time")
                st.markdown("- Track all your learning time, even short sessions")
            
            # Navigation
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Previous"):
                    st.session_state.tutorial_step = 2
                    st.rerun()
            with col2:
                if st.button("Next: Daily Goals →"):
                    st.session_state.tutorial_step = 4
                    st.rerun()
                    
        elif step == 4:
            st.header("🎯 Daily Goals")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown("""
                Daily Goals help you break down your learning journey into manageable
                daily tasks, building consistency and momentum.
                
                Research shows that setting specific, achievable daily goals significantly
                increases learning effectiveness and retention.
                """)
                
                # Interactive demo of daily goals
                st.markdown("### 📝 How Daily Goals Work:")
                
                # Sample goals with checkboxes
                st.markdown("#### Example Goals:")
                col1a, col1b = st.columns(2)
                with col1a:
                    st.checkbox("Complete 2 lectures on neural networks", value=True, disabled=True)
                    st.checkbox("Implement a simple classifier in PyTorch", disabled=True)
                
                with col1b:
                    st.checkbox("Read research paper on transformers", value=True, disabled=True)
                    st.checkbox("Debug gradient descent algorithm", disabled=True)
                
                # Add goal demo
                st.text_input("Add a new goal (Demo):", "Practice with TensorFlow for 30 minutes", disabled=True)
                st.button("Add Goal (Demo)", disabled=True)
                
                # Progress tracking
                st.markdown("#### Progress Tracking:")
                st.progress(0.5)
                st.caption("Example: 2/4 goals completed (50%)")
            
            with col2:
                st.markdown("### 💡 Pro Tips")
                st.markdown("- Set 3-5 realistic goals each day")
                st.markdown("- Make goals specific and measurable")
                st.markdown("- Celebrate completing all daily goals")
                st.markdown("- Review and adjust goals regularly")
            
            # Navigation
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Previous"):
                    st.session_state.tutorial_step = 3
                    st.rerun()
            with col2:
                if st.button("Next: Journal →"):
                    st.session_state.tutorial_step = 5
                    st.rerun()
                    
        elif step == 5:
            st.header("📝 Learning Journal")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown("""
                Your Learning Journal is a powerful tool for reflection and insight.
                
                By recording your learning experiences, challenges, and breakthroughs,
                you create a valuable record of your growth and deepen your understanding.
                """)
                
                # Demo of journal functionality
                st.markdown("### 📔 Journal Features:")
                
                # Example journal entry
                with st.expander("**Example Journal Entry**"):
                    st.markdown("#### Understanding Backpropagation")
                    st.markdown("**Date:** Today")
                    st.markdown("""
                    Today I finally understood how backpropagation works in neural networks. 
                    The key insight was seeing it as applying the chain rule repeatedly.
                    
                    I struggled with the matrix calculus until I visualized each step of the process.
                    Resources that helped: Stanford CS231n lecture notes and 3Blue1Brown videos.
                    
                    Next steps: Implement backpropagation from scratch to solidify understanding.
                    """)
                
                # New entry demo
                st.text_input("Title (Demo):", "Learning About Transformers", disabled=True)
                st.text_area("Content (Demo):", "Today I studied the transformer architecture...", disabled=True)
                st.button("Save Entry (Demo)", disabled=True)
            
            with col2:
                st.markdown("### 💡 Pro Tips")
                st.markdown("- Write entries soon after learning")
                st.markdown("- Note both successes and challenges")
                st.markdown("- Record useful resources")
                st.markdown("- Review old entries to see progress")
            
            # Navigation
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Previous"):
                    st.session_state.tutorial_step = 4
                    st.rerun()
            with col2:
                if st.button("Next: AI Assistant →"):
                    st.session_state.tutorial_step = 6
                    st.rerun()
                
        elif step == 6:
            st.header("🤖 AI Learning Assistant")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown("""
                The AI Learning Assistant is a powerful feature to enhance your skill development
                with personalized guidance and resources.
                
                It offers two main capabilities to accelerate your learning in ML/AI fields.
                """)
                
                # Skill Path Generator demo
                st.markdown("### 🛤️ Skill Path Generator")
                st.markdown("""
                Get a personalized learning path for any ML/AI skill with:
                
                - Prerequisites and foundational concepts
                - Step-by-step learning milestones
                - Curated resources for each milestone
                - Practical project ideas
                - Estimated completion timeframes
                """)
                
                # Small demo example
                with st.expander("**Example Learning Path (for Deep Learning)**"):
                    st.markdown("""
                    **Milestone 1:** Understand Neural Network Fundamentals (2 weeks)
                    - Resources: Stanford CS231n, Deep Learning Book Ch. 1-4
                    - Project: Build a simple neural network from scratch
                    
                    **Milestone 2:** Master Convolutional Networks (3 weeks)
                    - Resources: Fast.ai course, PyTorch tutorials
                    - Project: Image classification system
                    """)
                
                # AI Chat Assistant demo
                st.markdown("### 💬 AI Chat Assistant")
                st.markdown("""
                Chat with an AI assistant specialized in ML/AI topics:
                
                - Get explanations of complex concepts
                - Ask for learning resources and recommendations
                - Receive guidance on project implementation
                - Discuss latest trends in machine learning and AI
                """)
                
                # Example chat
                with st.expander("**Example Chat**"):
                    st.markdown("""
                    **You:** Explain backpropagation in simple terms.
                    
                    **AI Assistant:** Backpropagation is like fixing mistakes by working backwards. Imagine you're baking a cake that didn't turn out right. You'd go backwards through your recipe to find where you went wrong.
                    
                    In neural networks, the process works by:
                    1. Checking how wrong the prediction was
                    2. Calculating how each weight contributed to the error
                    3. Adjusting weights slightly to reduce future errors
                    
                    The math involves calculating gradients (directions of increase) and moving in the opposite direction to minimize errors.
                    """)
            
            with col2:
                st.markdown("### 💡 Pro Tips")
                st.markdown("- Generate paths for skills you've added")
                st.markdown("- Save useful learning paths as notes")
                st.markdown("- Ask specific questions to the AI")
                st.markdown("- Use AI explanations to supplement your learning")
            
            # Navigation
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Previous"):
                    st.session_state.tutorial_step = 5
                    st.rerun()
            with col2:
                if st.button("Finish Tutorial", type="primary"):
                    mark_tutorial_completed(username)
                    st.session_state.show_tutorial = False
                    st.balloons()
                    st.rerun()
    
    # Progress bar and step indicator for tutorial
    total_steps = 6
    st.progress((step - 1) / (total_steps - 1))
    st.caption(f"Step {step} of {total_steps}")
    
    if st.button("Skip Tutorial"):
        mark_tutorial_completed(username)
        st.session_state.show_tutorial = False
        st.rerun()

def display_ai_assistant_page():
    st.title("AI Learning Assistant")
    st.subheader("Personalized ML/AI Skill Development")
    
    username = get_username()
    user_skills = get_user_skills(username)
    
    # Create tabs for different AI features
    tab1, tab2 = st.tabs(["Skill Path Generator", "AI Chat Assistant"])
    
    with tab1:
        st.subheader("Generate a Learning Path for Your Skills")
        
        # Check the API status and display a message if there are issues
        from ai_assistant import check_api_status
        api_ok, api_message = check_api_status()
        if not api_ok:
            st.warning(f"⚠️ {api_message}")
            st.info("The skill path generator might not work correctly due to API limitations.")
        
        st.markdown("""
        Get a personalized learning path with milestones, resources, and project ideas tailored to your current level.
        This AI-powered tool focuses specifically on machine learning and artificial intelligence skill development.
        """)
        
        # Select skill
        if not user_skills:
            st.info("You haven't added any skills yet. Go to 'Add New Skill' to get started!")
        else:
            # Select a skill to generate a path for
            skill_options = [(skill["id"], skill["name"], skill["description"]) for skill in user_skills]
            selected_skill_idx = st.selectbox(
                "Select a skill to generate a learning path:",
                range(len(skill_options)),
                format_func=lambda i: skill_options[i][1]
            )
            
            selected_skill_id, selected_skill_name, selected_skill_desc = skill_options[selected_skill_idx]
            
            # User's current level
            level_options = ["Beginner", "Intermediate", "Advanced"]
            selected_level = st.radio("Your current level in this skill:", level_options)
            
            # Generate path button
            if st.button("Generate Learning Path", key="generate_path"):
                with st.spinner("Generating your personalized learning path..."):
                    # Call the AI model to generate the path
                    learning_path = generate_skill_path(
                        selected_skill_name,
                        selected_skill_desc,
                        selected_level.lower()
                    )
                    
                    if "error" in learning_path:
                        st.error(f"Error generating learning path: {learning_path['error']}")
                    else:
                        # Display the learning path in a nice format
                        st.success("Your personalized learning path is ready!")
                        st.markdown(f"## Learning Path for {selected_skill_name}")
                        st.markdown(learning_path["learning_path"])
                        
                        # Save the learning path in session state for persisting
                        st.session_state.current_learning_path = learning_path["learning_path"]
                        st.session_state.current_skill_id = selected_skill_id
            
            # Option to save as a note - outside of the generate button action to persist
            if "current_learning_path" in st.session_state:
                if st.button("Save this path as a note", key="save_path"):
                    note_text = f"## AI-Generated Learning Path\n\n{st.session_state.current_learning_path}"
                    success, message = add_progress_note(username, st.session_state.current_skill_id, note_text)
                    if success:
                        st.success("Learning path saved to skill notes!")
                    else:
                        st.error(f"Error saving note: {message}")
        
    # AI Chat Assistant tab
    with tab2:
        # Display the chat interface
        display_ai_chat_interface()

if __name__ == "__main__":
    main()
