import os
import sys
import openai
import logging
from dotenv import load_dotenv
from datetime import datetime
from firebase.firebase_admin_sdk import db

# Ensure the correct path to Firebase is included
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

# Set up logging
# logging.basicConfig(level=logging.DEBUG)

openai.api_key = os.getenv("OPENAI_API_KEY")

# ChatGPT role description
CHATGPT_ROLE = "You are a consentual extension of Rabbi Curt Landry who wants to help people use the Bible to guide their life. Write in a modern, inspiring, upbeat, and positive tone without being too over-the-top. Make sure to touch on evangelical themes and provide judeo-christian guidance. Do not mention any info that makes you sound like a robot, including people's start dates."

BASE_PROMPT_SUFFIX = "ONLY provide the asked-for information. Do not include any filler text, greetings, or sign-offs. Do not include any text that is not explicitly demanded by the prompt."

DEVOTIONAL_PROMPT = (
    """
    Write a personalized devotional for the reader that encourages them to live a life of impact and purpose...
    (trimmed for brevity)
    """ + BASE_PROMPT_SUFFIX
)

SUBJECT_LINE_PROMPT = (
    "Based on the following devotional content: '{devotional}', generate an evangelical subject line that sums up the devotional..."
)

def build_user_data(user_id):
    """Fetch user data from Firestore for building the prompt."""
    user_doc = db.collection('users').document(user_id).get()
    if user_doc.exists:
        user_data = user_doc.to_dict()
        user_email = user_data.get('email')
        first_name = user_data.get('firstName', "").replace('"', '')
        
        # Additional checks for the email
        if user_email and not (user_email.startswith('test') or user_email.startswith('Test')):
            onboarding_answers = db.collection('onboardingAnswers').where('userID', '==', user_id).stream()
            user_data['onboardingAnswers'] = [answer.to_dict() for answer in onboarding_answers]

            why_statements = db.collection('whyStatements').where('forUser', '==', user_id).stream()
            user_data['whyStatements'] = [statement.to_dict() for statement in why_statements]
            return user_data
    
    return None

def generate_prompt(role, content):
    """Generate a structured prompt for OpenAI."""
    return {"role": role, "content": content}

def chatgpt_request(model, messages):
    """Request completion from OpenAI."""
    response = openai.ChatCompletion.create(model=model, messages=messages)
    return response['choices'][0]['message']['content']

def generate_devotional(user_info_formatted):
    """Generate the devotional content using ChatGPT."""
    content = DEVOTIONAL_PROMPT.format(user_info_formatted=user_info_formatted)
    prompt = generate_prompt("user", content)
    
    return chatgpt_request("gpt-4o", [{"role": "system", "content": CHATGPT_ROLE}, prompt])

def generate_subject_line(devotional):
    """Generate a subject line for the devotional."""
    content = SUBJECT_LINE_PROMPT.format(devotional=devotional)
    prompt = generate_prompt("user", content)
    return chatgpt_request("gpt-4o", [{"role": "system", "content": CHATGPT_ROLE}, prompt])

def save_devotional_to_firebase(user_id, subject_line, devotional_content):
    """Save the devotional content to the user's 'devotionals' subcollection in Firestore."""

    user_ref = db.collection('users').document(user_id)
    devotional_ref = user_ref.collection('devotionals').document()

    devotional_data = {
        "subject_line": subject_line,
        "devotional_content": devotional_content,
        "created_at": datetime.utcnow()
    }

    devotional_ref.set(devotional_data)
    logging.info(f"Devotional saved to Firebase for user {user_id}")

def generate_full_devotional(user_id):
    """Generate and save a full devotional for the specified user."""
    user_info_formatted = build_user_data(user_id)
    
    if user_info_formatted:
        # Generate content
        devotional_content = generate_devotional(user_info_formatted)
        subject_line = generate_subject_line(devotional_content)
        
        # Prepare fields for Firestore
        devotional_data = {
            "biblePassage": devotional_content.strip(),  # Use content or adjust mapping
            "dateTimeCreated": datetime.now().isoformat(),
            "doc_id": None,  # Will be set when adding to Firestore
            "forUser": user_id,
            "isFavorite": False,
            "journalingPrompt": "Reflect on how this passage applies to your life.",  # Example prompt
            "personalization": f"A message tailored for {user_info_formatted.get('firstName', 'you')}",
            "title": subject_line.strip()
        }

        # Save to the 'devotionals' collection in Firebase
        devotional_ref = db.collection('devotionals').add(devotional_data)
        devotional_doc_id = devotional_ref[1].id
        
        # Update doc_id
        devotional_data["doc_id"] = devotional_doc_id
        db.collection('devotionals').document(devotional_doc_id).set(devotional_data)

        logging.info(f"Devotional saved to Firebase with doc_id {devotional_doc_id}")
        
        # Return the saved data
        return devotional_data
    else:
        logging.error(f"No data found for user {user_id}")
        return {
            "biblePassage": None,
            "dateTimeCreated": datetime.now().isoformat(),
            "doc_id": None,
            "forUser": user_id,
            "isFavorite": False,
            "journalingPrompt": None,
            "personalization": None,
            "title": None
        }


if __name__ == "__main__":
    __main__()
