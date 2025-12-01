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
import logging
import json
import time

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

# ============================================================
# LOGGING CONFIGURATION
# ============================================================
# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/devotion_agent.log'),
        logging.StreamHandler()  # Also print to console
    ]
)

logger = logging.getLogger(__name__)
logger.info("="*70)
logger.info("DevotionAgent Started")
logger.info("="*70)

# Access environment variables
api_key = os.getenv("API_KEY")
model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")

logger.info(f"Model configured: {model_name}")

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
    
    logger.info("Starting user input collection")
    
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
    
    logger.info(f"User reflection collected - length: {len(reflection_text)} characters")
    logger.debug(f"Reflection content: {reflection_text[:100]}...")
    
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
    
    logger.info("Starting DevotionAgent workflow")
    workflow_start_time = time.time()
    
    # Initialize session
    devotion_session = DevotionSession()
    logger.info("DevotionSession initialized")
    
    # Initialize Gemini client
    client = Client(api_key=os.getenv("API_KEY"))
    logger.info("Gemini client initialized")
    
    # ============================================================
    # STEP 1: DEVOTION SUMMARY
    # ============================================================
    logger.info("[STEP 1/2] Starting DEVOTION SUMMARY")
    print("[STEP 1/2] DEVOTION SUMMARY AGENT")
    print("-" * 70)
    print("Retrieving and summarizing today's devotion passages...\n")
    
    step1_start = time.time()
    
    # Get devotion data
    devotion_data = get_today_devotion()
    logger.info(f"Devotion data retrieved - length: {len(str(devotion_data))} characters")
    
    # Create prompt for devotion summary with actual devotion data
    devotion_prompt = f"""Here are today's devotion passages:

{devotion_data}

Based on these passages, please provide:
1. A summary of each passage type (Psalms, Old Testament, New Testament, Proverbs)
2. 2-3 key Bible verses that support the message
3. Spiritual insights and themes

Format clearly with sections for each passage type."""
    
    # Call Gemini directly
    logger.info("Calling Gemini API for devotion summary")
    api_call_start = time.time()
    
    devotion_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=devotion_prompt
    )
    
    api_call_duration = time.time() - api_call_start
    devotion_summary = devotion_response.text
    
    logger.info(f"Devotion summary received - length: {len(devotion_summary)} characters, API call duration: {api_call_duration:.2f}s")
    
    print("✓ Devotion summary retrieved\n")
    print(devotion_summary)
    
    devotion_session.save_devotion_summary(devotion_summary)
    logger.info("Devotion summary saved to session")
    print("\n✓ Devotion summary saved to session")
    
    step1_duration = time.time() - step1_start
    logger.info(f"[STEP 1] Completed in {step1_duration:.2f}s")
    
    # ============================================================
    # STEP 2: COLLECT USER INPUT
    # ============================================================
    logger.info("[STEP 2/2] Starting user input collection")
    print("\n[STEP 2/2] COLLECT YOUR REFLECTION")
    print("-" * 70)
    
    # Show input form
    collect_user_input()
    
    logger.info("Returning to complete workflow after user input")
    return devotion_session, devotion_summary, client


def complete_devotion_workflow(devotion_session, devotion_summary, client):
    """
    Complete the workflow after user reflection is submitted.
    """
    logger.info("Starting workflow completion phase")
    completion_start_time = time.time()
    
    # Check if reflection was submitted
    if user_reflections_global['data'] is None:
        logger.error("User reflection not submitted")
        print("❌ Please submit your reflection first by running the collection step.")
        return None
    
    user_reflections = user_reflections_global['data']
    devotion_session.save_user_reflection(user_reflections['reflection'])
    
    reflections_text = user_reflections['reflection']
    
    # ============================================================
    # STEP 3: PROCESS REFLECTION & GENERATE AFFIRMATION
    # ============================================================
    logger.info("[STEP 3/4] Starting reflection processing and affirmation generation")
    step3_start = time.time()
    
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
    logger.info("Calling Gemini API for affirmation and prayer")
    step3_api_start = time.time()
    
    combined_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=combined_prompt
    )
    
    step3_api_duration = time.time() - step3_api_start
    combined_text = combined_response.text
    
    logger.info(f"Affirmation and prayer generated - length: {len(combined_text)} characters, API duration: {step3_api_duration:.2f}s")
    print("✓ Reflection processed and prayer generated\n")
    devotion_session.save_user_input_processing(combined_text)
    logger.info("Affirmation and prayer saved to session")
    
    step3_duration = time.time() - step3_start
    logger.info(f"[STEP 3] Completed in {step3_duration:.2f}s")
    
    # ============================================================
    # STEP 4: DISCOVER WORSHIP SONGS
    # ============================================================
    logger.info("[STEP 4/4] Starting worship song discovery")
    step4_start = time.time()
    
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
    
    logger.info("Calling Gemini API for worship song recommendations")
    step4_api_start = time.time()
    # Call Gemini directly
    worship_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=worship_prompt
    )
    
    step4_api_duration = time.time() - step4_api_start
    worship_text = worship_response.text
    
    logger.info(f"Worship songs discovered - length: {len(worship_text)} characters, API duration: {step4_api_duration:.2f}s")
    
    print("✓ Worship songs discovered\n")
    
    step4_duration = time.time() - step4_start
    logger.info(f"[STEP 4] Completed in {step4_duration:.2f}s")
    
    # ============================================================
    # DISPLAY RESULTS
    # ============================================================
    logger.info("Displaying workflow results")
    
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
    
    # Calculate total workflow duration
    total_duration = time.time() - completion_start_time
    logger.info(f"Workflow completion phase finished in {total_duration:.2f}s")
    logger.info("="*70)
    logger.info("DEVOTION AGENT WORKFLOW COMPLETED SUCCESSFULLY")
    logger.info("="*70)
    
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
    try:
        devotion_session, devotion_summary, client = run_devotion_workflow()
        
        # After user submits reflection, complete the workflow
        result = complete_devotion_workflow(devotion_session, devotion_summary, client)
        
        if result:
            logger.info(f"Final result status: {result.status}")
            logger.info(f"Workflow completed at {result.timestamp}")
            print(f"\nWorkflow completed at {result.timestamp}")
        else:
            logger.warning("Workflow did not produce a result")
    except Exception as e:
        logger.error(f"Workflow failed with error: {str(e)}", exc_info=True)
        print(f"\n❌ Workflow failed: {str(e)}")
        exit(1)
    
    logger.info("DevotionAgent completed successfully")
