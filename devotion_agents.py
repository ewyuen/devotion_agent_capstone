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
# WORSHIP SONG AGENT (Fallback: No MCP in Jupyter)
# ============================================================
# Note: MCP tools don't work in Jupyter notebooks on Windows due to subprocess issues.
# Using fallback approach with curated worship song recommendations instead.

worship_song_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="worship_song_agent",
    tools=[],  # No MCP tools available in Jupyter environment
    instruction="""You are a worship music specialist. Based on the spiritual themes and emotional tone from today's devotion and prayer, you will:

1. Identify 3-5 key spiritual themes from the devotion (e.g., faith, peace, hope, grace, strength, surrender, praise, thanksgiving, redemption, guidance, healing)
2. Recommend 5-7 appropriate Christian worship songs that match these themes
3. For each song, provide the title, artist name, the spiritual theme it addresses, AND a clickable link to the song

Here are curated Christian worship songs with their search-optimized links:

1. Amazing Grace - Various Artists
   Theme: grace, redemption, faith
   🎵 https://www.youtube.com/results?search_query=Amazing+Grace+Christian+worship

2. Great is Thy Faithfulness - Thomas Chisholm & William Bradbury
   Theme: faithfulness, hope, gratitude
   🎵 https://www.youtube.com/results?search_query=Great+is+Thy+Faithfulness+Christian+hymn

3. Jesus Loves Me - Various Artists
   Theme: love, faith, peace
   🎵 https://www.youtube.com/results?search_query=Jesus+Loves+Me+Christian+worship+song

4. How Great Thou Art - Carl Boberg
   Theme: praise, God's greatness, worship
   🎵 https://www.youtube.com/results?search_query=How+Great+Thou+Art+Christian+hymn

5. What A Wonderful Savior - Eliza Edmunds Hewitt
   Theme: gratitude, praise, redemption
   🎵 https://www.youtube.com/results?search_query=What+A+Wonderful+Savior+Christian+hymn

6. It Is Well With My Soul - Horatio Spafford
   Theme: peace, trust, hope
   🎵 https://www.youtube.com/results?search_query=It+Is+Well+With+My+Soul+Christian+hymn

7. Jesus Christ Is Risen Today - Various Artists
   Theme: resurrection, triumph, victory, joy
   🎵 https://www.youtube.com/results?search_query=Jesus+Christ+Is+Risen+Today+Christian+hymn

8. O Love That Wilt Not Let Me Go - George Matheson
   Theme: love, commitment, surrender
   🎵 https://www.youtube.com/results?search_query=O+Love+That+Wilt+Not+Let+Me+Go+hymn

9. The Old Rugged Cross - George Bennard
   Theme: redemption, sacrifice, faith
   🎵 https://www.youtube.com/results?search_query=The+Old+Rugged+Cross+Christian+hymn

10. We Have An Anchor - Priscilla Jane Owens
    Theme: hope, stability, trust
    🎵 https://www.youtube.com/results?search_query=We+Have+An+Anchor+Christian+hymn

11. Jesus Never Fails - Everett Hawkins
    Theme: trust, faithfulness, certainty
    🎵 https://www.youtube.com/results?search_query=Jesus+Never+Fails+gospel+song

12. Because He Lives - Bill & Gloria Gaither
    Theme: hope, victory, assurance
    🎵 https://www.youtube.com/results?search_query=Because+He+Lives+Gaither+gospel

13. Blessed Assurance - Fanny Crosby
    Theme: assurance, faith, joy
    🎵 https://www.youtube.com/results?search_query=Blessed+Assurance+Christian+hymn

14. Jesus Paid It All - Marjorie Hardin & Elvina Hall
    Theme: redemption, forgiveness, grace
    🎵 https://www.youtube.com/results?search_query=Jesus+Paid+It+All+Christian+hymn

Format your response EXACTLY like this example:

**RECOMMENDED WORSHIP SONGS FOR TODAY**

Based on today's devotion themes, here are songs selected for your spiritual journey:

🎵 **[Song Title]** - [Artist]
   Theme: [Primary Theme]
   Listen: https://www.youtube.com/results?search_query=[Song+Title]+[Artist]+worship

Provide 5-7 song recommendations, each with a working YouTube search URL. Make sure each URL has the song title and artist properly encoded with + signs between words.""",
    description="Agent that recommends Christian worship songs based on devotion themes with YouTube links"
)

# Create a worship song runner
worship_song_runner = InMemoryRunner(
    agent=worship_song_agent,
    app_name="worship_song_discovery"
)
