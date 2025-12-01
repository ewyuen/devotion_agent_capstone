"""
Devotion Tools Module
Provides utilities for retrieving and formatting Bible devotion passages.
"""

import xml.etree.ElementTree as ET
from typing import List, Dict
from datetime import datetime
import os
import logging

try:
    import googleapiclient.discovery
    YOUTUBE_AVAILABLE = True
except ImportError:
    YOUTUBE_AVAILABLE = False

logger = logging.getLogger(__name__)


def get_daily_devotion(xml_file: str, day: int) -> List[Dict[str, str]]:
    """
    Retrieve all devotion passages for a specific day.
    
    Args:
        xml_file: Path to the devotion XML file
        day: Day number (1-366)
    
    Returns:
        List of dictionaries containing devotion information
    """
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        devotions = []
        for devotion in root.findall('daily_devotion'):
            day_elem = devotion.find('day')
            if day_elem is not None and int(day_elem.text) == day:
                devotion_dict = {
                    'book': devotion.find('book').text,
                    'start_chapter': devotion.find('start_chapter').text,
                    'start_verse': devotion.find('start_verse').text,
                    'end_chapter': devotion.find('end_chapter').text,
                    'end_verse': devotion.find('end_verse').text,
                    'type': devotion.find('type').text,
                    'order': devotion.find('order').text
                }
                devotions.append(devotion_dict)
        
        return devotions
    except Exception as e:
        print(f"Error reading XML file: {e}")
        return []


def format_devotion(devotion: Dict[str, str]) -> str:
    """
    Format a devotion dictionary as a readable Bible passage string.
    
    Args:
        devotion: Dictionary containing devotion information
        
    Returns:
        Formatted Bible passage string (e.g., "John 3:16" or "Psalm 23:1-6")
    """
    book = devotion['book']
    start_ch = int(devotion['start_chapter'])
    start_v = int(devotion['start_verse'])
    end_ch = int(devotion['end_chapter'])
    end_v = int(devotion['end_verse'])
    
    if start_ch == end_ch:
        passage = f"{book} {start_ch}:{start_v}-{end_v}"
    else:
        passage = f"{book} {start_ch}:{start_v} - {end_ch}:{end_v}"
    
    return passage


def get_today_devotion(xml_file: str = r"data/devotion.xml") -> Dict:
    """
    Retrieve devotion passages for today's date.
    Handles leap years correctly by excluding February 29.
    
    This function calculates the current day of year and retrieves all devotion
    passages scheduled for that day from the provided XML file. It automatically
    adjusts for leap years to ensure consistent 365-day devotional schedules.
    Includes comprehensive error handling for file access and parsing issues.
    
    Args:
        xml_file: Path to the devotion XML file (default: "data/devotion.xml")
    
    Returns:
        Dict: A structured response dictionary with the following format:
            {
                "status": str,  # "success", "no_devotion", or "error"
                "devotions": List[Dict[str, str]],  # List of devotion dictionaries
                "message": str,  # Descriptive message
                "date": str,  # Today's date (ISO format)
                "day_of_year": int  # Calculated day of year (1-365)
            }
            
            Each devotion dictionary in the list contains:
                - 'book': Name of the biblical book (e.g., "Psalm", "John", "Proverbs")
                - 'start_chapter': Starting chapter number as string
                - 'start_verse': Starting verse number as string
                - 'end_chapter': Ending chapter number as string
                - 'end_verse': Ending verse number as string
                - 'type': Category of passage (e.g., "Psalm", "New Testament", "Old Testament", "Proverbs")
                - 'order': Order of passage within the day as string
            
            Status values:
            - "success": Devotions were successfully retrieved (devotions list is populated)
            - "no_devotion": No devotions scheduled for this date (e.g., February 29)
            - "error": An error occurred while reading or parsing the XML file
    
    Example:
        >>> result = get_today_devotion()
        >>> if result["status"] == "success":
        ...     for devotion in result["devotions"]:
        ...         print(f"{devotion['type']}: {devotion['book']} {devotion['start_chapter']}:{devotion['start_verse']}")
        ... else:
        ...     print(f"Error: {result['message']}")
        Psalm: Psalm 23:1
        New Testament: John 3:16
    """
    date = datetime.now()
    date_str = date.strftime("%Y-%m-%d")
    
    try:
        # Validate xml_file parameter
        if not xml_file:
            return {
                "status": "error",
                "devotions": [],
                "message": "Error: XML file path cannot be empty",
                "date": date_str,
                "day_of_year": None
            }
        
        # Handle February 29 (no devotion scheduled)
        if date.month == 2 and date.day == 29:
            return {
                "status": "no_devotion",
                "devotions": [],
                "message": "No devotion scheduled for February 29 in this 365-day schedule",
                "date": date_str,
                "day_of_year": None
            }
        
        # Calculate day of year
        day_of_year = date.timetuple().tm_yday
        
        # If after February 29 in a leap year, subtract 1
        if date.month > 2 and (date.year % 4 == 0 and (date.year % 100 != 0 or date.year % 400 == 0)):
            day_of_year -= 1
        
        # Retrieve devotions for the calculated day
        try:
            devotions = get_daily_devotion(xml_file, day_of_year)
        except FileNotFoundError:
            return {
                "status": "error",
                "devotions": [],
                "message": f"Error: XML file not found at '{xml_file}'. Please check the file path.",
                "date": date_str,
                "day_of_year": day_of_year
            }
        except ET.ParseError as e:
            return {
                "status": "error",
                "devotions": [],
                "message": f"Error: XML parsing failed. Invalid XML format: {str(e)}",
                "date": date_str,
                "day_of_year": day_of_year
            }
        except PermissionError:
            return {
                "status": "error",
                "devotions": [],
                "message": f"Error: Permission denied when accessing '{xml_file}'. Check file permissions.",
                "date": date_str,
                "day_of_year": day_of_year
            }
        
        # Check if devotions were retrieved
        if devotions:
            return {
                "status": "success",
                "devotions": devotions,
                "message": f"Successfully retrieved {len(devotions)} devotion(s) for today",
                "date": date_str,
                "day_of_year": day_of_year
            }
        else:
            return {
                "status": "error",
                "devotions": [],
                "message": f"No devotions found for day {day_of_year}. The XML file may be incomplete.",
                "date": date_str,
                "day_of_year": day_of_year
            }
    
    except Exception as e:
        # Catch any unexpected errors
        return {
            "status": "error",
            "devotions": [],
            "message": f"Unexpected error: {type(e).__name__}: {str(e)}",
            "date": date_str,
            "day_of_year": None
        }


def format_devotions_list(devotions: List[Dict[str, str]]) -> str:
    """
    Format a list of devotions into a readable text.
    
    Args:
        devotions: List of devotion dictionaries
        
    Returns:
        Formatted string of all devotions by type
    """
    if not devotions:
        return "No devotions found."
    
    devotion_text = "Today's Devotion Passages:\n"
    for devotion in devotions:
        formatted = format_devotion(devotion)
        devotion_type = devotion.get('type', 'Unknown')
        devotion_text += f"\n{devotion_type}: {formatted}\n"
    
    return devotion_text


# ============================================================
# YOUTUBE SEARCH TOOL
# ============================================================

def search_worship_songs(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search YouTube for worship songs using the YouTube Data API.
    
    Args:
        query: Search query for worship songs
        max_results: Maximum number of results to return (default: 5)
        
    Returns:
        List of dictionaries containing:
        - title: Song title
        - channel: Artist/Channel name
        - video_id: YouTube video ID
        - url: Direct YouTube link
    """
    if not YOUTUBE_AVAILABLE:
        logger.error("YouTube API client not available")
        return [{"error": "YouTube API client not installed. Run: pip install google-api-python-client"}]
    
    try:
        youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        if not youtube_api_key:
            logger.warning("YOUTUBE_API_KEY not configured in .env file")
            return [{"error": "YOUTUBE_API_KEY not configured in .env file"}]
        
        logger.info(f"Searching YouTube for: {query}")
        
        # Build YouTube API client
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=youtube_api_key
        )
        
        # Execute search request
        request = youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=max_results,
            order="relevance",
            videoCategoryId="10"  # Music category
        )
        
        response = request.execute()
        
        # Parse results
        results = []
        for item in response.get("items", []):
            result = {
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "video_id": item["id"]["videoId"],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            }
            results.append(result)
            logger.debug(f"Found: {result['title']} by {result['channel']}")
        
        logger.info(f"YouTube search returned {len(results)} results for query: {query}")
        return results
    
    except Exception as e:
        logger.error(f"YouTube search failed: {str(e)}")
        return [{"error": f"YouTube search failed: {str(e)}"}]


# ============================================================
# SESSION MANAGEMENT FOR AGENTS
# ============================================================

class DevotionSession:
    """
    Manages session state across multiple agent executions.
    Stores outputs from each agent so subsequent agents can access them.
    """
    
    def __init__(self):
        """Initialize a new devotion session."""
        self.session_data = {
            "timestamp": datetime.now().isoformat(),
            "devotion_summary": None,
            "user_reflection": None,
            "user_input_processing": None,
            "prayer": None,
            "agent_history": []
        }
    
    def save_devotion_summary(self, summary: str) -> None:
        """
        Save the devotion summary from the Devotion Summary Agent.
        
        Args:
            summary: The devotion summary text
        """
        self.session_data["devotion_summary"] = summary
        self._log_agent_action("devotion_summary_agent", "Retrieved and summarized devotion passages")
    
    def save_user_reflection(self, reflection: str) -> None:
        """
        Save the user's personal reflection.
        
        Args:
            reflection: The user's reflection text
        """
        self.session_data["user_reflection"] = reflection
        self._log_agent_action("user", "Submitted personal reflection")
    
    def save_user_input_processing(self, processing: str) -> None:
        """
        Save the User Input Agent's processing of the reflection.
        
        Args:
            processing: The processed user input
        """
        self.session_data["user_input_processing"] = processing
        self._log_agent_action("user_input_agent", "Processed and acknowledged user reflection")
    
    def save_prayer(self, prayer: str) -> None:
        """
        Save the personalized prayer from the Prayer Generator Agent.
        
        Args:
            prayer: The generated prayer text
        """
        self.session_data["prayer"] = prayer
        self._log_agent_action("prayer_generator_agent", "Generated personalized prayer")
    
    def get_devotion_summary(self) -> str:
        """
        Retrieve the devotion summary from this session.
        
        Returns:
            The devotion summary, or None if not yet generated
        """
        return self.session_data.get("devotion_summary")
    
    def get_user_reflection(self) -> str:
        """
        Retrieve the user's reflection from this session.
        
        Returns:
            The user's reflection, or None if not yet submitted
        """
        return self.session_data.get("user_reflection")
    
    def get_user_input_processing(self) -> str:
        """
        Retrieve the processed user input from this session.
        
        Returns:
            The processed user input, or None if not yet processed
        """
        return self.session_data.get("user_input_processing")
    
    def get_prayer(self) -> str:
        """
        Retrieve the generated prayer from this session.
        
        Returns:
            The prayer, or None if not yet generated
        """
        return self.session_data.get("prayer")
    
    def get_full_session_context(self) -> str:
        """
        Get a formatted string with all session data for agent context.
        Useful for providing agents with the full conversation history.
        
        Returns:
            Formatted session context string
        """
        context = f"""
SESSION CONTEXT:
================

Devotion Summary:
{self.session_data.get('devotion_summary', 'Not yet retrieved')}

User's Personal Reflection:
{self.session_data.get('user_reflection', 'Not yet submitted')}

Processing Summary:
{self.session_data.get('user_input_processing', 'Not yet processed')}

Generated Prayer:
{self.session_data.get('prayer', 'Not yet generated')}
"""
        return context
    
    def _log_agent_action(self, agent_name: str, action: str) -> None:
        """
        Log an agent action to the session history.
        
        Args:
            agent_name: Name of the agent that performed the action
            action: Description of the action
        """
        self.session_data["agent_history"].append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "action": action
        })
    
    def get_agent_history(self) -> List[Dict]:
        """
        Get the history of all agent actions in this session.
        
        Returns:
            List of agent action dictionaries
        """
        return self.session_data["agent_history"]
    
    def get_summary(self) -> Dict:
        """
        Get a summary of the entire session.
        
        Returns:
            Dictionary with session summary
        """
        return {
            "timestamp": self.session_data["timestamp"],
            "devotion_retrieved": self.session_data["devotion_summary"] is not None,
            "user_reflected": self.session_data["user_reflection"] is not None,
            "reflection_processed": self.session_data["user_input_processing"] is not None,
            "prayer_generated": self.session_data["prayer"] is not None,
            "agent_actions_count": len(self.session_data["agent_history"])
        }


# ============================================================
# GOOGLE ADK SESSION SERVICE INTEGRATION
# ============================================================

class DevotionSessionService:
    """
    Wraps Google ADK's InMemorySessionService for persistent agent sessions.
    Manages session state across multiple agent interactions with built-in persistence.
    
    Uses Google ADK patterns for session management as referenced in:
    https://www.kaggle.com/code/edwardyuen2/day-3a-agent-sessions
    """
    
    def __init__(self):
        """Initialize the session service."""
        self.service = None
        self.use_adk = False
        try:
            from google.adk.sessions import InMemorySessionService
            self.service = InMemorySessionService()
            self.use_adk = True
            print("✓ Using Google ADK InMemorySessionService for session management")
        except (ImportError, Exception) as e:
            print(f"⚠️  Using custom session management (ADK not available: {type(e).__name__})")
    
    def create_session(self, session_id: str = None) -> str:
        """
        Create a new session for agent interactions.
        
        Args:
            session_id: Optional custom session ID. If None, auto-generated.
            
        Returns:
            The session ID
        """
        if self.use_adk and self.service:
            try:
                return self.service.create_session(session_id)
            except Exception:
                pass
        
        # Fallback: create simple session ID
        import uuid
        return session_id or str(uuid.uuid4())
    
    def store_message(self, session_id: str, message: Dict) -> None:
        """
        Store a message in the session (agent output or user input).
        
        Args:
            session_id: The session ID
            message: Message dictionary with role, content, timestamp
        """
        if self.use_adk and self.service:
            try:
                self.service.store_message(session_id, message)
            except Exception:
                pass
    
    def get_session_history(self, session_id: str) -> List[Dict]:
        """
        Retrieve all messages in a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            List of message dictionaries in the session
        """
        if self.use_adk and self.service:
            try:
                return self.service.get_session_history(session_id)
            except Exception:
                pass
        return []
    
    def save_session(self, session_id: str, devotion_session: 'DevotionSession') -> None:
        """
        Save a DevotionSession's data through the service.
        Persists the session state using ADK's InMemorySessionService if available.
        
        Args:
            session_id: The session ID
            devotion_session: The DevotionSession object to save
        """
        if self.use_adk and self.service:
            try:
                session_data = {
                    "role": "system",
                    "content": "devotion_session_checkpoint",
                    "data": devotion_session.session_data,
                    "timestamp": datetime.now().isoformat()
                }
                self.service.store_message(session_id, session_data)
            except Exception:
                pass
