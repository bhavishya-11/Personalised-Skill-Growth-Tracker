import json
import os
import datetime

# Paths for the database files
SKILLS_DB_PATH = "skills_data.json"

def initialize_database():
    """Initialize the database files if they don't exist"""
    if not os.path.exists(SKILLS_DB_PATH):
        create_empty_skills_db()

def create_empty_skills_db():
    """Create an empty skills database file"""
    empty_db = {"skills": []}
    save_to_db(empty_db, SKILLS_DB_PATH)

def load_from_db(file_path):
    """Load data from a database file"""
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # Return empty database if file is corrupted
            if file_path == SKILLS_DB_PATH:
                return {"skills": []}
    else:
        # If file doesn't exist, return empty database
        if file_path == SKILLS_DB_PATH:
            return {"skills": []}
    
    return {}

def save_to_db(data, file_path):
    """Save data to a database file"""
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def get_user_data_from_db(username, db_path, key):
    """Get user-specific data from a database file"""
    db_data = load_from_db(db_path)
    
    if key in db_data:
        user_items = []
        
        for item in db_data[key]:
            if item.get("username") == username:
                user_items.append(item)
        
        return user_items
    
    return []

def add_item_to_db(username, item_data, db_path, key):
    """Add an item to a database file"""
    db_data = load_from_db(db_path)
    
    if key not in db_data:
        db_data[key] = []
    
    # Add username and timestamp to item data
    item_data["username"] = username
    item_data["created_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    db_data[key].append(item_data)
    save_to_db(db_data, db_path)
    
    return True

def update_item_in_db(username, item_id, updated_data, db_path, key):
    """Update an item in a database file"""
    db_data = load_from_db(db_path)
    
    if key in db_data:
        for i, item in enumerate(db_data[key]):
            if item.get("username") == username and item.get("id") == item_id:
                # Update only the provided fields
                for field, value in updated_data.items():
                    db_data[key][i][field] = value
                
                # Add updated timestamp
                db_data[key][i]["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                save_to_db(db_data, db_path)
                return True
    
    return False

def delete_item_from_db(username, item_id, db_path, key):
    """Delete an item from a database file"""
    db_data = load_from_db(db_path)
    
    if key in db_data:
        for i, item in enumerate(db_data[key]):
            if item.get("username") == username and item.get("id") == item_id:
                db_data[key].pop(i)
                save_to_db(db_data, db_path)
                return True
    
    return False

def get_unique_values_from_db(field, db_path, key):
    """Get unique values for a field from a database file"""
    db_data = load_from_db(db_path)
    unique_values = set()
    
    if key in db_data:
        for item in db_data[key]:
            if field in item:
                unique_values.add(item[field])
    
    return unique_values
def save_chat_message(username, is_user, content):
    """Save a chat message to the database"""
    db_data = load_from_db("chat_history.json")
    
    if "messages" not in db_data:
        db_data["messages"] = {}
    
    if username not in db_data["messages"]:
        db_data["messages"][username] = []
    
    message = {
        "is_user": is_user,
        "content": content,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    db_data["messages"][username].append(message)
    save_to_db(db_data, "chat_history.json")

def get_chat_history(username):
    """Get chat history for a user"""
    db_data = load_from_db("chat_history.json")
    if "messages" in db_data and username in db_data["messages"]:
        return db_data["messages"][username]
    return []
