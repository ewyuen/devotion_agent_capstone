"""
DevotionAgent - Complete Devotion Workflow
Combines worship reflections, prayers, and song recommendations using AI
"""

# ============================================================
# SETUP & IMPORTS
# ============================================================
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass
import uuid
import os

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.genai import types, Client

from devotion_tools import get_today_devotion, DevotionSession
from devotion_agents import (
    devotion_summary_agent, 
    devotion_runner,
    user_input_agent,
    user_input_runner,
    prayer_generator_agent,
    prayer_runner,
    worship_song_agent,
    worship_song_runner
)

# Load environment variables from .env file
load_dotenv()

# Access environment variables
api_key = os.getenv("API_KEY")
model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")

# Configure retry settings for API calls
retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)


# ============================================================
# DATA STRUCTURES
# ============================================================
@dataclass
class DevotionWorkflowResult:
    """Encapsulates the complete workflow execution result"""
    status: str  # "success" or "error"
    devotion_summary: Optional[str] = None
    user_input: Optional[str] = None
    prayer_response: Optional[str] = None
    worship_songs: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


# ============================================================
# GLOBAL STATE
# ============================================================
user_reflections_global = {'data': None}


# ============================================================
# USER INPUT COLLECTION
# ============================================================
def collect_user_input():
    """
    Collect user's personal reflection on the devotion using standard input.
    """
    global user_reflections_global
    user_reflections_global['data'] = None
    
    print("\n" + "="*70)
    print("YOUR PERSONAL DEVOTION REFLECTION")
    print("="*70)
    print("\nShare your thoughts and reflections about today's devotion:\n")
    
    # Collect user input from standard input
    print("What are your thoughts, insights, or how does this devotion apply to you?")
    print("(Type your reflection and press Enter twice when done)\n")
    
    lines = []
    while True:
        line = input()
        if line == "":
            if lines and lines[-1] == "":
                break
        lines.append(line)
    
    reflection_text = "\n".join(lines[:-1])  # Remove the last empty line
    
    # Store the reflection
    user_reflections_global['data'] = {
        'reflection': reflection_text
    }
    
    print("\n✓ Your reflection has been recorded.\n")


# ============================================================
# UTILITY FUNCTIONS
# ============================================================
def safe_print(obj):
    """Print any object type safely"""
    if isinstance(obj, list):
        print("\n".join(str(item) for item in obj))
    else:
        print(str(obj))


# ============================================================
# MAIN WORKFLOW
# ============================================================
def run_devotion_workflow():
    """
    Execute the complete devotion workflow:
    1. Retrieve and summarize today's devotion
    2. Collect user reflection
    3. Generate affirmation and prayer
    4. Discover worship songs
    """
    
    print("\nStarting DevotionAgent workflow...\n")
    
    # Initialize session
    devotion_session = DevotionSession()
    
    # Initialize Gemini client
    client = Client(api_key=os.getenv("API_KEY"))
    
    # ============================================================
    # STEP 1: DEVOTION SUMMARY
    # ============================================================
    print("[STEP 1/2] DEVOTION SUMMARY AGENT")
    print("-" * 70)
    print("Retrieving and summarizing today's devotion passages...\n")
    
    # Get devotion data
    devotion_data = get_today_devotion()
    
    # Create prompt for devotion summary with actual devotion data
    devotion_prompt = f"""Here are today's devotion passages:

{devotion_data}

Based on these passages, please provide:
1. A summary of each passage type (Psalms, Old Testament, New Testament, Proverbs)
2. 2-3 key Bible verses that support the message
3. Spiritual insights and themes

Format clearly with sections for each passage type."""
    
    # Call Gemini directly
    devotion_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=devotion_prompt
    )
    
    devotion_summary = devotion_response.text
    
    print("✓ Devotion summary retrieved\n")
    print(devotion_summary)
    
    devotion_session.save_devotion_summary(devotion_summary)
    print("\n✓ Devotion summary saved to session")
    
    # ============================================================
    # STEP 2: COLLECT USER INPUT
    # ============================================================
    print("\n[STEP 2/2] COLLECT YOUR REFLECTION")
    print("-" * 70)
    
    # Show input form
    collect_user_input()
    
    return devotion_session, devotion_summary, client


def complete_devotion_workflow(devotion_session, devotion_summary, client):
    """
    Complete the workflow after user reflection is submitted.
    """
    
    # Check if reflection was submitted
    if user_reflections_global['data'] is None:
        print("❌ Please submit your reflection first by running the collection step.")
        return None
    
    user_reflections = user_reflections_global['data']
    devotion_session.save_user_reflection(user_reflections['reflection'])
    
    reflections_text = user_reflections['reflection']
    
    # ============================================================
    # STEP 3: PROCESS REFLECTION & GENERATE AFFIRMATION
    # ============================================================
    print("\n[STEP 3/4] PROCESSING YOUR REFLECTION & GENERATING AFFIRMATION")
    print("-" * 70)
    print("Creating affirmation and personalized prayer...\n")
    
    # Create a combined prompt for processing and prayer
    combined_prompt = f"""Based on this devotion summary:

{devotion_summary}

And this user's personal reflection:
{reflections_text}

Please provide:
1. A warm, affirming response to their reflection (100 words)
2. A personalized prayer (200 words) that incorporates the devotion themes and their reflection

Format the response clearly with sections for "Your Affirmation" and "Today's Prayer"."""
    
    # Call Gemini directly
    combined_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=combined_prompt
    )
    
    combined_text = combined_response.text
    
    print("✓ Reflection processed and prayer generated\n")
    devotion_session.save_user_input_processing(combined_text)
    
    # ============================================================
    # STEP 4: DISCOVER WORSHIP SONGS
    # ============================================================
    print("\n[STEP 4/4] DISCOVERING WORSHIP SONGS")
    print("-" * 70)
    print("Finding worship songs that match today's spiritual themes...\n")
    
    # Create a worship prompt with context
    worship_prompt = f"""Based on this devotion:

{devotion_summary}

And this user reflection:
{reflections_text}

And this affirmation and prayer:
{combined_text}

Please recommend 5-7 worship songs that align with these themes. For each song, provide:
- Song title
- Artist name
- Spiritual theme
- YouTube search link

Format like this:
🎵 **[Song Title]** - [Artist]
   Theme: [Theme]
   https://www.youtube.com/results?search_query=[Song+Title]+[Artist]+worship"""
    
    # Call Gemini directly
    worship_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=worship_prompt
    )
    
    worship_text = worship_response.text
    
    print("✓ Worship songs discovered\n")
    
    # ============================================================
    # DISPLAY RESULTS
    # ============================================================
    print("\n" + "="*70)
    print("COMPLETE DEVOTION WORKFLOW SUMMARY")
    print("="*70)
    
    print("\n[1] TODAY'S DEVOTION SUMMARY")
    print("-" * 70)
    safe_print(devotion_summary)
    
    print("\n[2] YOUR REFLECTION & AFFIRMATION")
    print("-" * 70)
    print("Your Reflection:")
    print(reflections_text)
    print("\n" + combined_text)
    
    print("\n[3] WORSHIP SONGS")
    print("-" * 70)
    safe_print(worship_text)
    
    print("\n" + "="*70)
    print("✓ DEVOTION AGENT WORKFLOW COMPLETED SUCCESSFULLY")
    print("="*70 + "\n")
    
    # Return workflow result
    return DevotionWorkflowResult(
        status="success",
        devotion_summary=devotion_summary,
        user_input=reflections_text,
        prayer_response=combined_text,
        worship_songs=worship_text
    )


if __name__ == "__main__":
    # Run the devotion workflow
    devotion_session, devotion_summary, client = run_devotion_workflow()
    
    # After user submits reflection, complete the workflow
    result = complete_devotion_workflow(devotion_session, devotion_summary, client)
    
    if result:
        print(f"\nWorkflow completed at {result.timestamp}")
