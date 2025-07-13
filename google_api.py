import os
import requests
import json
import time

# Google Custom Search API configuration
API_KEY = os.getenv("GOOGLE_API_KEY", "")
SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")

def search_study_materials(query, max_results=10):
    """
    Search for study materials using Google Custom Search API
    
    This function searches for learning resources related to the given query
    If the API keys are not available, it will use a simple web search fallback
    """
    if not API_KEY or not SEARCH_ENGINE_ID:
        # Fallback if API keys are not available
        return fallback_search(query, max_results)
    
    # Add "learn" or "tutorial" to the query to get better learning resources
    search_query = f"{query} learn tutorial resources"
    
    try:
        # Use Google Custom Search API
        results = []
        start_index = 1
        
        # Google API allows only 10 results per request
        # To get more, we need to make multiple requests with different start indexes
        while len(results) < max_results:
            url = f"https://www.googleapis.com/customsearch/v1"
            params = {
                "key": API_KEY,
                "cx": SEARCH_ENGINE_ID,
                "q": search_query,
                "start": start_index,
                "num": min(10, max_results - len(results))
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if "items" in data:
                    for item in data["items"]:
                        result = {
                            "title": item.get("title", ""),
                            "link": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "source": "Google Search API"
                        }
                        results.append(result)
                
                # If there are no more results or we have enough, break the loop
                if "items" not in data or len(data["items"]) < 10 or len(results) >= max_results:
                    break
                
                # Update start index for the next request
                start_index += 10
                
                # Add a small delay to avoid rate limiting
                time.sleep(0.2)
            else:
                # If API request fails, use fallback
                return fallback_search(query, max_results)
        
        return results[:max_results]
    
    except Exception as e:
        # If any error occurs, use fallback
        print(f"Error using Google API: {str(e)}")
        return fallback_search(query, max_results)

def fallback_search(query, max_results=10):
    """
    Fallback function when API keys are not available
    
    This function returns a set of common learning platforms with search links
    for the given query
    """
    # Encode the query for URL
    encoded_query = requests.utils.quote(query)
    
    # Create a list of common learning platforms with search URLs
    platforms = [
        {
            "title": f"Learn {query} on Coursera",
            "link": f"https://www.coursera.org/search?query={encoded_query}",
            "snippet": "Coursera offers courses from top universities and organizations. Find professional certificates, degree programs, and free courses on various subjects.",
            "source": "Fallback Search"
        },
        {
            "title": f"{query} tutorials on YouTube",
            "link": f"https://www.youtube.com/results?search_query={encoded_query}+tutorial",
            "snippet": "YouTube offers thousands of free tutorial videos on almost any skill you want to learn, from beginner to advanced levels.",
            "source": "Fallback Search"
        },
        {
            "title": f"Learn {query} on Khan Academy",
            "link": f"https://www.khanacademy.org/search?page_search_query={encoded_query}",
            "snippet": "Khan Academy offers practice exercises, instructional videos, and a personalized learning dashboard that empower learners to study at their own pace.",
            "source": "Fallback Search"
        },
        {
            "title": f"{query} courses on Udemy",
            "link": f"https://www.udemy.com/courses/search/?q={encoded_query}",
            "snippet": "Udemy is an online learning platform with thousands of courses on various topics. Many courses include certificates of completion.",
            "source": "Fallback Search"
        },
        {
            "title": f"{query} resources on edX",
            "link": f"https://www.edx.org/search?q={encoded_query}",
            "snippet": "edX offers courses from top educational institutions around the world, including many that offer verified certificates or university credit.",
            "source": "Fallback Search"
        },
        {
            "title": f"{query} on MIT OpenCourseWare",
            "link": f"https://ocw.mit.edu/search/?q={encoded_query}",
            "snippet": "MIT OpenCourseWare is a web-based publication of virtually all MIT course content, open and available to the world.",
            "source": "Fallback Search"
        },
        {
            "title": f"{query} tutorials on W3Schools",
            "link": f"https://www.w3schools.com/search/search.php?q={encoded_query}",
            "snippet": "W3Schools offers free tutorials, references, and exercises in all the major web development languages and technologies.",
            "source": "Fallback Search"
        },
        {
            "title": f"{query} on Stack Overflow",
            "link": f"https://stackoverflow.com/search?q={encoded_query}",
            "snippet": "Stack Overflow is a question and answer site for professional and enthusiast programmers. It's a great resource for solving specific problems.",
            "source": "Fallback Search"
        },
        {
            "title": f"{query} books on Open Library",
            "link": f"https://openlibrary.org/search?q={encoded_query}",
            "snippet": "Open Library is an open, editable library catalog with the goal of creating a web page for every book ever published.",
            "source": "Fallback Search"
        },
        {
            "title": f"{query} articles on Medium",
            "link": f"https://medium.com/search?q={encoded_query}",
            "snippet": "Medium is an open platform where readers find dynamic thinking, and where expert and undiscovered voices can share their writing.",
            "source": "Fallback Search"
        }
    ]
    
    return platforms[:max_results]

def get_resource_details(url):
    """
    Get additional details about a resource
    
    This function is meant to retrieve more information about a learning resource
    Not implemented in the current version due to complexity and rate limiting concerns
    """
    # This would require more complex scraping or API calls
    # Not implemented for simplicity
    return {
        "url": url,
        "description": "Detailed information not available",
        "rating": None,
        "reviews": []
    }
