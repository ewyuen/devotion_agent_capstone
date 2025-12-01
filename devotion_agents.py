"""
Devotion Agents Module

Contains agent definitions for the DevotionAgent workflow:
- Devotion Summary Agent: Retrieves and summarizes daily devotion passages
- User Input Agent: Processes personal reflections
- Prayer Generator Agent: Generates personalized prayers
- Worship Song Agent: Discovers worship songs via YouTube Music MCP
"""

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from devotion_tools import get_today_devotion
import os
import logging
from typing import List, Dict

try:
    import googleapiclient.discovery
    YOUTUBE_AVAILABLE = True
except ImportError:
    YOUTUBE_AVAILABLE = False
    logging.warning("YouTube API client not installed. Install with: pip install google-api-python-client")

logger = logging.getLogger(__name__)

# ============================================================
# DEVOTION SUMMARY AGENT
# ============================================================

devotion_summary_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="devotion_summary_agent",
    tools=[get_today_devotion],  # Pass the function as a tool
    instruction="""You are a Biblical devotion summary expert. 
    You have access to a function called get_today_devotion() that retrieves today's devotion passages.
    Use this function to get the passages and return them in this EXACT order:
    1. Psalms
    2. Old Testament
    3. New Testament
    4. Proverbs
    
    For each passage in this order, 
    a) generate a concise 2-3 sentence spiritual summary that captures the key messages.
    b) capture 2-3 bible verses that support the summary.
    c) Format the output clearly with the passage type, summary and bible verses.""",
    description="Agent that retrieves and summarizes daily devotion passages in a specific order"
)

# Create a devotion summary runner
devotion_runner = InMemoryRunner(
    agent=devotion_summary_agent,
    app_name="devotion_summary"
)


# ============================================================
# USER INPUT AGENT
# ============================================================

user_input_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="user_input_agent",
    instruction="""You are a compassionate spiritual journal facilitator. Your role is to guide the user to reflect on and record their personal response to today's devotion.

Present the following prompts to the user in a warm, encouraging tone:

1. **What God Showed Me**: What spiritual insight, lesson, or message did God reveal to you through today's devotion passages?

2. **Personal Response**: How does this message apply to your life right now? What specific situation or challenge comes to mind?

3. **Prayer Requests**: What prayer requests or concerns would you like to lift up to God based on today's devotion?

4. **Praises & Gratitude**: What answers to previous prayers or blessings from God do you want to acknowledge and thank Him for?

5. **Action Steps**: What is one practical step you can take today to apply this spiritual insight?

After collecting the user's responses, create a brief personalized summary that acknowledges their reflections and affirms their faith journey.

Format your response professionally and encouragingly, helping the user feel heard and supported in their spiritual walk.""",
    description="Agent that prompts users to record personal devotion reflections and responses"
)

# Create a user input runner
user_input_runner = InMemoryRunner(
    agent=user_input_agent,
    app_name="user_input_collector"
)


# ============================================================
# YOUTUBE SEARCH TOOL
# ============================================================

def search_worship_songs(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search YouTube for worship songs using the YouTube Data API.
    
    Args:
        query: Search query for worship songs
        max_results: Maximum number of results to return
        
    Returns:
        List of dictionaries containing song title, artist, and YouTube URL
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
        
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=youtube_api_key
        )
        
        request = youtube.search().list(
            q=query,
            part="snippet",
            type="video",
            maxResults=max_results,
            order="relevance",
            videoCategoryId="10"  # Music category
        )
        
        response = request.execute()
        
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
        
        logger.info(f"YouTube search returned {len(results)} results")
        return results
    
    except Exception as e:
        logger.error(f"YouTube search failed: {str(e)}")
        return [{"error": f"YouTube search failed: {str(e)}"}]


# ============================================================
# PRAYER GENERATOR AGENT
# ============================================================

prayer_generator_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="prayer_generator_agent",
    instruction="""You are a spiritual prayer composer. 
    Based on the themes, spiritual concepts, and God's promises identified from today's devotion passages, you will:
    
    Craft a personalized, heartfelt prayer (150-250 words) that:
    - Acknowledges the spiritual themes from today's passages
    - Addresses God with reverence
    - Includes gratitude for God's promises and attributes
    - Contains personal reflection and requests
    - Ends with affirmation of faith

    Format your response as "Today's Prayer" with the full prayer text.""",
    description="Agent that generates personalized prayers based on devotion themes"
)

# Create a prayer generator runner
prayer_runner = InMemoryRunner(
    agent=prayer_generator_agent,
    app_name="prayer_generator"
)


# ============================================================
# WORSHIP SONG AGENT (With YouTube API Search)
# ============================================================

worship_song_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="worship_song_agent",
    tools=[search_worship_songs],  # Add YouTube search tool
    instruction="""You are a worship music specialist. Based on the spiritual themes and emotional tone from today's devotion and prayer, you will:

1. Identify 3-5 key spiritual themes from the devotion (e.g., faith, peace, hope, grace, strength, surrender, praise, thanksgiving, redemption, guidance, healing)
2. Use the search_worship_songs() function to find 5-7 appropriate Christian worship songs that match these themes
3. For each song found, provide the title, artist/channel name, the spiritual theme it addresses, AND the direct YouTube link

Call search_worship_songs() with queries like:
- "Christian worship songs about faith"
- "worship songs about peace"
- "gospel worship music hope"
- "contemporary Christian worship"
- etc.

Format your response EXACTLY like this:

**RECOMMENDED WORSHIP SONGS FOR TODAY**

Based on today's devotion themes of [THEMES], here are songs selected for your spiritual journey:

🎵 **[Song Title]** - [Artist/Channel]
   Theme: [Primary Theme]
   Listen: [YouTube URL]

Provide 5-7 song recommendations with direct YouTube links from the search results.""",
    description="Agent that recommends Christian worship songs using YouTube API search"
)

# Create a worship song runner
worship_song_runner = InMemoryRunner(
    agent=worship_song_agent,
    app_name="worship_song_discovery"
)
