import streamlit as st
import hashlib
import datetime
import json
import os
import uuid

# Path for the user database file
USER_DB_PATH = "user_data.json"

def initialize_auth():
    """Initialize authentication related session state variables"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None

def hash_password(password):
    """Hash a password using SHA-256 for secure storage"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    """Load user data from the JSON file"""
    if os.path.exists(USER_DB_PATH):
        try:
            with open(USER_DB_PATH, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # Return empty user database if file is corrupted or doesn't exist
            return {"users": []}
    else:
        # If file doesn't exist, return empty user database
        return {"users": []}

def save_users(users_data):
    """Save user data to the JSON file"""
    with open(USER_DB_PATH, "w") as f:
        json.dump(users_data, f, indent=4)

def user_exists(username, email=None):
    """Check if a user with the given username or email already exists"""
    users_data = load_users()
    
    for user in users_data["users"]:
        if user["username"] == username:
            return True
        if email and user["email"] == email:
            return True
    
    return False

def register_user(username, email, password):
    """Register a new user"""
    if user_exists(username, email):
        return False
    
    users_data = load_users()
    
    # Create new user entry
    new_user = {
        "username": username,
        "email": email,
        "password": hash_password(password),
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    users_data["users"].append(new_user)
    save_users(users_data)
    
    return True

def login_user(username, password):
    """Authenticate user login"""
    users_data = load_users()
    
    for user in users_data["users"]:
        if user["username"] == username and user["password"] == hash_password(password):
            st.session_state.authenticated = True
            st.session_state.username = username
            return True
    
    return False

def logout_user():
    """Log out the current user"""
    st.session_state.authenticated = False
    st.session_state.username = None

def is_authenticated():
    """Check if a user is currently authenticated"""
    return st.session_state.authenticated

def get_username():
    """Get the username of the currently authenticated user"""
    return st.session_state.username if is_authenticated() else None

def get_user_data(username):
    """Get data for a specific user"""
    users_data = load_users()
    
    for user in users_data["users"]:
        if user["username"] == username:
            return user
    
    return None

def find_user_by_email(email):
    """Find a user by email"""
    users_data = load_users()
    
    for user in users_data["users"]:
        if user.get("email") == email:
            return user
    
    return None

def update_user_password(username, new_password):
    """Update a user's password"""
    users_data = load_users()
    
    for i, user in enumerate(users_data["users"]):
        if user["username"] == username:
            users_data["users"][i]["password"] = hash_password(new_password)
            users_data["users"][i]["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_users(users_data)
            return True
    
    return False

def update_user_password_by_email(email, new_password):
    """Update a user's password by email"""
    users_data = load_users()
    
    for i, user in enumerate(users_data["users"]):
        if user.get("email") == email:
            users_data["users"][i]["password"] = hash_password(new_password)
            users_data["users"][i]["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_users(users_data)
            return True
    
    return False

def store_reset_request(email, token):
    """Store a password reset request"""
    users_data = load_users()
    
    if "password_resets" not in users_data:
        users_data["password_resets"] = []
    
    # Remove any previous reset requests for this email
    users_data["password_resets"] = [
        reset for reset in users_data["password_resets"] 
        if reset.get("email") != email
    ]
    
    # Add new reset request
    reset_request = {
        "email": email,
        "token": token,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "expires_at": (datetime.datetime.now() + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    }
    
    users_data["password_resets"].append(reset_request)
    save_users(users_data)
    
    return True
