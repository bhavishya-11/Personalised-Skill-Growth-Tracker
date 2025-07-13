import uuid
import re

def generate_skill_id():
    """Generate a unique ID for a skill"""
    return str(uuid.uuid4())

def validate_skill_data(name, category, description):
    """
    Validate skill data
    
    Args:
        name: Skill name
        category: Skill category
        description: Skill description
        
    Returns:
        Dict with validation result
    """
    # Check if skill name is valid
    if not name or len(name) < 2:
        return {
            "valid": False,
            "message": "Skill name must be at least 2 characters long"
        }
    
    # Check if skill name contains only allowed characters
    if not re.match(r'^[a-zA-Z0-9\s\-\+\#\.]+$', name):
        return {
            "valid": False,
            "message": "Skill name contains invalid characters"
        }
    
    # Check if category is valid
    if not category or len(category) < 2:
        return {
            "valid": False,
            "message": "Category must be at least 2 characters long"
        }
    
    # Check if category contains only allowed characters
    if not re.match(r'^[a-zA-Z0-9\s\-]+$', category):
        return {
            "valid": False,
            "message": "Category contains invalid characters"
        }
    
    # Description is optional but if provided, check length
    if description and len(description) > 500:
        return {
            "valid": False,
            "message": "Description must be less than 500 characters"
        }
    
    return {
        "valid": True,
        "message": "Validation successful"
    }

def format_date(date_str):
    """Format a date string to a more readable format"""
    # This assumes date_str is in format 'YYYY-MM-DD HH:MM:SS'
    try:
        date_parts = date_str.split(' ')[0].split('-')
        return f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]}"
    except:
        return date_str

def calculate_time_since(date_str):
    """Calculate time passed since a given date"""
    import datetime
    
    try:
        date_format = "%Y-%m-%d %H:%M:%S"
        past_date = datetime.datetime.strptime(date_str, date_format)
        now = datetime.datetime.now()
        
        diff = now - past_date
        
        if diff.days > 365:
            years = diff.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
        elif diff.days > 30:
            months = diff.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds // 3600 > 0:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds // 60 > 0:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    except:
        return "Unknown"

def sanitize_input(text):
    """Sanitize user input to prevent security issues"""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\'\%\{\}\[\]\&\#\*]', '', text)
    
    return sanitized.strip()

def truncate_text(text, max_length=50):
    """Truncate text to a maximum length"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."
