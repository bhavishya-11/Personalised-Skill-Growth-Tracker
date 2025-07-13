import json
import os
import requests
import streamlit as st

# Hugging Face API configuration
API_TOKEN = os.getenv("MY_API_KEY")
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

headers = {"Authorization": f"Bearer {API_TOKEN}"}

def query_huggingface(payload):
    """
    Send a query to the Hugging Face Inference API
    
    Args:
        payload (dict): The payload to send to the API
        
    print(f"🚨 Sending API request with prompt: {payload['inputs'][:60]}...")
        
    Returns:
        dict: The API response
    """
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def generate_skill_path(skill_name, skill_description=None, user_level="beginner"):
    """
    Generate a learning path for a specific skill using an AI model
    
    Args:
        skill_name (str): The name of the skill
        skill_description (str, optional): A description of the skill
        user_level (str, optional): The user's current level (beginner, intermediate, advanced)
        
    Returns:
        dict: A structured learning path with milestones and resources
    """
    # Create the prompt with ML/AI focus
    prompt = f"""As an AI learning assistant specialized in machine learning and artificial intelligence, create a detailed learning path for mastering '{skill_name}'.

Context: {skill_description if skill_description else f"The skill is '{skill_name}'"}
User's current level: {user_level}

Format your response as a structured learning path with:
1. Prerequisites (if any)
2. 5-7 clear learning milestones
3. Recommended resources for each milestone (focus on ML/AI tools, frameworks, and practices)
4. Practical project ideas
5. Estimated time to completion for each milestone

Focus on modern practices in the field of machine learning and AI. Include references to important libraries, frameworks, and methodologies used by professionals.
"""

    # Create the payload for the Hugging Face API
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True
        }
    }
    
    # Query the Hugging Face model
    response = query_huggingface(payload)
    
    if "error" in response:
        error_msg = response["error"]
        if "exceeded your monthly included credits" in error_msg:
            return {"error": "The Hugging Face API quota has been exceeded. Please try again later or contact the administrator to update the API token."}
        return {"error": error_msg}
    
    # Extract the generated text
    try:
        if isinstance(response, list) and len(response) > 0:
            generated_text = response[0].get("generated_text", "")
        else:
            generated_text = "No response from the model."
        
        # Return the generated learning path
        return {
            "skill_name": skill_name,
            "user_level": user_level,
            "learning_path": generated_text
        }
    except Exception as e:
        return {"error": f"Error processing response: {str(e)}"}

def chat_with_ai(user_message, chat_history=None):
    """
    Chat with the AI assistant about learning and skill development
    
    Args:
        user_message (str): The user's message
        chat_history (list, optional): List of previous messages
        
    Returns:
        str: The AI's response
    """
    if chat_history is None:
        chat_history = []
    
    # Create a system prompt focused on ML/AI learning
    system_prompt = """You are an AI learning assistant specialized in machine learning, deep learning, and artificial intelligence. 
    Your primary goal is to help users develop their skills in AI/ML fields, provide guidance on learning paths, explain complex concepts in simple terms, 
    and suggest resources for further learning. Focus on providing accurate, practical advice that reflects current industry best practices in machine learning and AI. 
    Use terminology that is appropriate for ML/AI professionals and students."""
    
    # Format the conversation for the model
    conversation = f"{system_prompt}\n\n"
    
    for message in chat_history:
        role = "User" if message["is_user"] else "Assistant"
        conversation += f"{role}: {message['content']}\n"
    
    conversation += f"User: {user_message}\nAssistant:"
    
    # Create the payload for the Hugging Face API
    payload = {
        "inputs": conversation,
        "parameters": {
            "max_new_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True
        }
    }
    
    # Query the model
    response = query_huggingface(payload)
    
    if "error" in response:
        error_msg = response['error']
        if "exceeded your monthly included credits" in error_msg:
            return "I'm sorry, but the Hugging Face API quota has been exceeded. Please try again later or contact the administrator to update the API token."
        return f"Sorry, I encountered an error: {error_msg}"
    
    # Extract the generated text
    try:
        if isinstance(response, list) and len(response) > 0:
            full_response = response[0].get("generated_text", "")
            # Extract just the assistant's response (after the prompt)
            assistant_response = full_response.split("Assistant:")[-1].strip()
            # If the response contains a "User:" part, trim it
            if "User:" in assistant_response:
                assistant_response = assistant_response.split("User:")[0].strip()
            return assistant_response
        else:
            return "I'm having trouble generating a response right now. Please try again."
    except Exception as e:
        return f"Sorry, I encountered an error processing my response: {str(e)}"

@st.cache_data(ttl=3600)  # Cache for 1 hour
def check_api_status():
    """
    Check the status of the Hugging Face API credentials
    
    Returns:
        tuple: (is_configured, message)
    """
    if not API_TOKEN:
        return False, "Hugging Face API token is not configured."
    
    print("🚨 Performing API status check...")
    return True, "API token is configured"

def display_ai_chat_interface():
    """
    Display the AI chat interface in the Streamlit app
    """
    from database import save_chat_message, get_chat_history
    
    st.subheader("AI Learning Assistant")
    
    # Get username
    username = st.session_state.username
    if not username:
        st.warning("Please login to use the chat interface")
        return
        
    # Load existing chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = get_chat_history(username)
    
    # Check API status and display status message
    api_ok, api_message = check_api_status()
    
    # Show the current model name
    model_name = "Mistral-7B"
    st.write(f"**AI Model**: {model_name}")
    
    # Display model description
    with st.expander("About the AI Model"):
        st.write("A powerful 7B parameter instruction-tuned model optimized for chat and knowledge-based answers, specializing in machine learning and AI topics.")
    
    # Display appropriate status message
    if api_ok:
        st.success(f"✅ {api_message}")
    else:
        st.warning(f"⚠️ {api_message}")
        st.info("The AI assistant requires a valid Hugging Face API token with sufficient quota.")
    
    # Initialize chat history in session state if it doesn't exist
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Display chat messages
    for message in st.session_state.chat_history:
        with st.chat_message("user" if message["is_user"] else "assistant"):
            st.write(message["content"])
    
    # Chat input
    user_input = st.chat_input("Ask about machine learning, AI concepts, or skill development...")
    
    if user_input:
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Save and add user message to chat history
        save_chat_message(username, True, user_input)
        st.session_state.chat_history.append({"is_user": True, "content": user_input})
        
        # Get AI response
        with st.spinner("Thinking..."):
            response = chat_with_ai(user_input, st.session_state.chat_history)
        
        # Display AI response
        with st.chat_message("assistant"):
            st.write(response)
        
        # Save and add AI response to chat history
        save_chat_message(username, False, response)
        st.session_state.chat_history.append({"is_user": False, "content": response})